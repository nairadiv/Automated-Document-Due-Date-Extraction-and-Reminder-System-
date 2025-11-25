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
import requests
import time
last_graph_hour = None


import matplotlib.pyplot as plt

def clean_date(date_str):
    """Convert extracted dates to standard YYYY-MM-DD."""
    date_str = str(date_str)

    formats = [
        "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",
        "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
        "%d %b %Y", "%d %B %Y",
        "%b %d %Y", "%B %d %Y",
        "%b %d, %Y", "%B %d, %Y",
        "%Y %b %d", "%Y %B %d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except:
            pass

    return None  # Could not parse date


def generate_graph():
    """Create a graph of date → submission category."""
    if not os.path.exists(LOG_FILE):
        print("❌ No log file found. Graph not created.")
        return

    df = pd.read_csv(LOG_FILE)

    # Convert all dates to standard format
    df["clean_date"] = df["date"].apply(clean_date)
    df = df.dropna(subset=["clean_date"])

    grouped = df.groupby(["clean_date", "category"]).size().reset_index(name="count")
    totals = df.groupby("clean_date").size().reset_index(name="total")

    # Highest submission day
    max_date = totals.loc[totals["total"].idxmax()]

    print(f" Highest Submissions: {max_date['clean_date']} → {max_date['total']} submissions")

    # --- PLOT ---
    plt.figure(figsize=(12, 6))

    for cat in grouped["category"].unique():
        temp = grouped[grouped["category"] == cat]
        plt.plot(temp["clean_date"], temp["count"], marker="o", label=cat)

    plt.axvline(max_date["clean_date"], linestyle="--")

    # ======= herre=======
    import matplotlib.dates as mdates

# --- Format X-Axis Dates ---
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # Show full date
    ax.xaxis.set_major_locator(mdates.MonthLocator())               # Show every month
    plt.xticks(rotation=45)                                         # Rotate dates



    plt.title(" Submission / Deadline Summary")
    plt.xlabel("Date")
    plt.ylabel("Number of Submissions")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    # Create folder if not exists

    output_folder = r"C:\Users\ADIV\python_project\graphs"
    os.makedirs(output_folder, exist_ok=True)

# Save graph BEFORE show()
    plt.savefig(os.path.join(output_folder, "submission_graph.png"))

# Show on screen
    plt.show()
    plt.close()



    print(" Graph updated → saved as submission_graph.png")

    # Optional Telegram notification
    telegram_notify(f"📊 Submission Graph Updated\nTop Date: {max_date['clean_date']} ({max_date['total']} submissions)")


TELEGRAM_BOT_TOKEN = "your bot token"
TELEGRAM_CHAT_ID = "your chat id"

def telegram_notify(message):
    """Send notification to Telegram."""
    try:
        url = f"https://api.telegram.org/bot{"bot token"/"chat id"}/sendMessage"
        requests.post(url, data={"chat_id":, "text": message})
    except Exception as e:
        print("Telegram error:", e)

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
    pattern = r'''(
        \b\d{1,2}[-\/\.]\d{1,2}[-\/\.]\d{2,4}\b |
        \b\d{4}[-\/\.]\d{1,2}[-\/\.]\d{1,2}\b |
        \b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b |
        \b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b |
        \b\d{4}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2}\b
    )'''
    
    matches = re.findall(pattern, text, flags=re.IGNORECASE | re.VERBOSE)

    # Each match is a tuple — convert to first non-empty element
    cleaned = []
    for m in matches:
        if isinstance(m, tuple):
            # The first element is always the full matched date string
            cleaned.append(m[0])
        else:
            cleaned.append(m)

    return cleaned

    return re.findall(pattern, text,flags=re.IGNORECASE | re.VERBOSE)

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


# ================== telegram_notify==============
def notify(msg):
    notification.notify(
        title="📅 Reminder / Detection",
        message=msg,
        timeout=8
    )
    print(msg)
def telegram_notify(message):
    """Send notification to Telegram bot."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        print("📨 Telegram message sent!")
    except Exception as e:
        print("Telegram error:", e)


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
            telegram_notify(f"New Date Detected\nfile: {file_name}\nDate: {date}\nTypes: {category}")
            print(f"✔ {date} → {category}")


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

    last_graph_update = None  # track last update day

    try:
        while True:
             now = datetime.now()

        # Run graph every 4 hours (00, 04, 08, 12, 16, 20)
        if now.hour % 4 == 0 and now.minute == 0:
            if last_graph_hour != now.hour:   # run once per hour
                generate_graph()
                generate_monthly_graph()
                last_graph_hour = now.hour

        time.sleep(1)


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
        notify(f"...")
telegram_notify(f"...")

if days_left == 3:
    notify(f"⏳ 3 days left for deadline: {file} ({date_text})")
    telegram_notify(f"⏳ 3 days left for deadline: {file} ({date_text})")
elif days_left == 1:
    notify(f"⚠️ 1 day left for deadline: {file} ({date_text})")
    telegram_notify(f"⚠️ Reminder: 1 day left for {file}\nDeadline: {date_text}")
elif days_left == 0:
    notify(f"🚨 TODAY is the deadline for: {file} ({date_text})")
    telegram_notify(f"🚨 FINAL REMINDER\nDeadline Today for: {file}\n({date_text})")
