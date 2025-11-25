# Automated-Document-Due-Date-Extraction-and-Reminder-System-
“A Python automation system that extracts due-dates from PDFs/Docs using OCR, classifies them, stores logs, and sends reminders with notifications and graphs.”

🚀 Features
✅ 1. Auto-Monitor a Folder (Watchdog)

The script constantly monitors a folder.
Whenever a new file appears:

Extracts text

Finds dates

Classifies the date (deadline / exam / due date / etc.)

Stores data in a CSV

Sends notifications

Moves the file to a processed folder

🧠 2. Smart Date Extraction

Supports formats:

DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY

YYYY-MM-DD

12 Aug 2024, August 12 2024

Aug 12, 2024, etc.

Regex automatically detects them inside the document.

🗂 3. Smart Categorization (NLP Keyword Based)

Date type is detected based on keywords:

Category	Keywords
Deadline / Submission	submit, deadline, last date
Due Date	due, bill, pay before
Expiry Date	expire, valid till
Assignment Given	assigned on
Start / End Dates	start, begin, end, till
Exam Dates	exam, test, timetable
🔔 4. Notifications
Desktop Notifications

Using plyer

Telegram Notifications

Using bot + chat ID.

📊 5. Daily Submission Graph

Every night at 23:59, a graph is created showing:

Number of submissions per date

Category-wise trends

The day with the highest submissions

Graph is saved here:

C:\Users\ADIV\python_project\graphs\submission_graph.png

🗄 6. Deadline Reminder System

Checks date_log.csv and sends reminders:

3 days before

1 day before

On the deadline date

Supports both desktop & Telegram notifications.

📦 Folder Structure
project/
│
├── watchtest/
│   ├── processed/
│   └── (Incoming PDF/DOCX/TXT files)
│
├── graphs/
│   └── submission_graph.png
│
├── date_log.csv
├── hash_log.txt
├── main.py
└── README.md

⚙️ Setup Instructions
1. Install dependencies
pip install watchdog plyer pypdf python-docx pdfplumber matplotlib pandas requests

2. Create Telegram Bot

Open Telegram

Search: @BotFather

Use /newbot

Copy the BOT TOKEN

Get your CHAT ID using:
https://api.telegram.org/bot<token>/getUpdates

Add them to your script:

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

3. Set Your Folder Paths

Update:

MONITOR_FOLDER
PROCESSED_FOLDER
output_folder (graphs)

▶️ Run the Program

Just run:

python main.py


The script will begin watching your folder continuously.

📈 Example Output (Console)
🟢 Monitoring folder: C:\Users\ADIV\watchtest

📄 New file detected: fee_receipt.pdf
✔ 12-02-2025 → DUE DATE
📨 Telegram message sent!
🗂 File moved to processed folder.

 Highest Submissions: 2025-02-15 → 6 submissions
 Graph updated → saved as submission_graph.png

🛠 Technologies Used

Python 3

watchdog

pypdf

python-docx

matplotlib

pandas

plyer

Telegram Bot API
