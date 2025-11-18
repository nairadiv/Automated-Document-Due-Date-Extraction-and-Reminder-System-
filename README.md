# Automated-Document-Due-Date-Extraction-and-Reminder-System-


This project automatically monitors a folder, detects when a new document is added, extracts important dates, classifies them (deadline, exam date, due date, expiry, etc.), and stores them for reminder purposes.
It helps users avoid missing deadlines by reading dates directly from files—saving time and reducing manual effort.

Using Python libraries like Watchdog, pandas, regex, PyPDF, and python-docx, the system:

Watches a folder in real-time for new files

Extracts text from PDF, DOCX, and TXT documents

Uses regex to detect all date formats

Classifies the date type based on surrounding keywords

Stores extracted dates in a CSV log

Shows instant desktop notifications

Moves scanned files into a processed folder for privacy
