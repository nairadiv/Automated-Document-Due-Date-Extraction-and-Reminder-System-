import os
import re
import shutil
import hashlib
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from plyer import notification
from pypdf import PdfReader
import docx
from datetime import datetime
import pdfplumber


# --------------- PATHS ---------------

MONITOR_FOLDER = r"C:\Users\ADIV\watchtest"
PROCESSED_FOLDER = r"C:\Users\ADIV\watchtest\processed"
LOG_FILE = "date_log.csv"

# Create processed folder if not exist
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# --------------- DATE CLASSIFICATION KEYWORDS ---------------

DATE_TYPES = {
    "DEADLINE / SUBMISSION": ["submit", "submission", "deadline", "last date", "final date", "closing"],
    "DUE DATE": ["due", "payment", "bill", "pay before"],
    "EXPIRY DATE": ["expiry", "expire", "valid till", "valid upto"],
    "ASSIGNMENT GIVEN": ["assignment given", "assigned on", "assignment date"],
    "RENEWAL DATE": ["renew", "renewal", "renew before", "renew by"],
    "START DATE": ["start", "begin", "commence", "from"],
    "END DATE": ["end", "till", "upto", "valid until"],
    "EXAM DATES":["exam","test","paper","schedule","timetable"],

}

# --------------- TEXT EXTRACTION ---------------

def extract_text(file_path):
    ext = file_path.lower().split(".")[-1]

    try:
        if ext == "pdf":
            reader = PdfReader(file_path)
            return "\n".join([page.extract_text() or "" for page in reader.pages])

        elif ext == "docx":
            doc_file = docx.Document(file_path)
            return "\n".join([p.text for p in doc_file.paragraphs])

        elif ext == "txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        return ""
    except:
        return ""

# --------------- REGEX DATE FINDING ---------------

def find_dates(text):
    pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
    return re.findall(pattern, text)

def split_sentences(text):
    return re.split(r'[.!?]\s+', text)

def classify_date(sentence):
    s = sentence.lower()
    for category, keywords in DATE_TYPES.items():
        for k in keywords:
            if k in s:
                return category
    return "GENERAL DATE"

# --------------- FILE HASH TO PREVENT DUPLICATES ---------------

def file_hash(path):
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()

# --------------- LOGGING USING PANDAS ---------------

def log_to_csv(file_name, date, category):
    data = {
        "file_name": [file_name],
        "date": [date],
        "category": [category],
        "detected_on": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
    }
    
    df = pd.DataFrame(data)

    if not os.path.exists(LOG_FILE):
        df.to_csv(LOG_FILE, index=False)
    else:
        df.to_csv(LOG_FILE, mode="a", index=False, header=False)

# --------------- WATCHDOG HANDLER ---------------

class Handler(FileSystemEventHandler):

    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        file_name = os.path.basename(file_path)

        print(f"\n📄 New file detected: {file_name}")

        # Duplicate prevention
        h = file_hash(file_path)
        if os.path.exists("hash_log.txt") and h in open("hash_log.txt").read():
            print("⚠ File already scanned earlier.")
            return
        else:
            with open("hash_log.txt", "a") as f:
                f.write(h + "\n")

        # Extract text
        text = extract_text(file_path)
        sentences = split_sentences(text)
        dates = find_dates(text)

        if not dates:
            print("❌ No dates found.")
            shutil.move(file_path, PROCESSED_FOLDER)
            return

        # Process each date
        for date in dates:
            sentence = next((s for s in sentences if date in s), "")
            category = classify_date(sentence)

            log_to_csv(file_name, date, category)

            notification.notify(
                title="📅 Important Date Detected",
                message=f"{date} → {category}",
                timeout=6
            )

            print(f"✔ {date} → {category}")

        # Move file
        shutil.move(file_path, PROCESSED_FOLDER)
        print("🗂 File moved to processed folder.")

# --------------- MAIN PROGRAM ---------------

if __name__ == "__main__":
    print("🟢 Monitoring folder:", MONITOR_FOLDER)

    observer = Observer()
    observer.schedule(Handler(), MONITOR_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

def check_deadlines():
    """
    Checks deadline dates in CSV and shows reminder BEFORE the date.
    VERY SIMPLE LOGIC SO YOU CAN UNDERSTAND:
    - 3 days before
    - 1 day before
    - on the deadline day
    """
    if not os.path.exists(LOG_FILE):
        return

    df = pd.read_csv(LOG_FILE)
    today = datetime.today().date()

    for _, row in df.iterrows():
        file = row["file_name"]
        date_text = row["date"]

        # Try parsing dates in dd-mm-YYYY or dd/mm/YYYY
        parsed = None
        for fmt in ("%d-%m-%Y", "%d/%m/%Y"):
            try:
                parsed = datetime.strptime(date_text, fmt).date()
                break
            except:
                continue

        if parsed is None:
            continue

        days_left = (parsed - today).days

        # Simple reminder conditions (EASY TO UNDERSTAND)
        if days_left == 3:
            notify(f"⏳ 3 days left for deadline: {file} ({date_text})")
        elif days_left == 1:
            notify(f"⚠️ 1 day left for deadline: {file} ({date_text})")
        elif days_left == 0:
            notify(f"🚨 TODAY is the deadline for: {file} ({date_text})")