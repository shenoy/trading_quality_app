

import os
import sqlite3
import smtplib
import threading
from email.message import EmailMessage
from PyPDF2 import PdfReader, PdfWriter
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

# Email Settings
SENDER_EMAIL = "rajeshtshenoy@gmail.com"
RECEIVER_EMAIL = "rajeshtshenoy@gmail.com"
APP_PASSWORD = "justcjvmjrmvxfib"

def get_db_connection():
    conn = sqlite3.connect('/home/rsitracker/uploads.db')
    conn.row_factory = sqlite3.Row  # This enables dictionary-style access
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ensure tables exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT, page_number INTEGER, total_pages INTEGER,
        is_auto INTEGER DEFAULT 0, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY,
        minute INTEGER DEFAULT 0,
        hour INTEGER DEFAULT 9,
        day TEXT DEFAULT '*',
        trigger_type TEXT DEFAULT 'cron',
        interval_minutes INTEGER DEFAULT 5)''')

    # Add missing columns safely
    cursor.execute("PRAGMA table_info(settings)")
    columns = [info[1] for info in cursor.fetchall()]

    if 'trigger_type' not in columns:
        cursor.execute("ALTER TABLE settings ADD COLUMN trigger_type TEXT DEFAULT 'cron'")
    if 'interval_minutes' not in columns:
        cursor.execute("ALTER TABLE settings ADD COLUMN interval_minutes INTEGER DEFAULT 5")

    # Initialize settings row if missing
    cursor.execute("INSERT OR IGNORE INTO settings (id, minute, hour, day, trigger_type, interval_minutes) VALUES (1, 0, 9, '*', 'cron', 5)")

    conn.commit()
    conn.close()


def send_pdf_email(pdf_path, page_num, filename):
    msg = EmailMessage()
    # Use the filename as the subject
    msg['Subject'] = f"{filename} - Page {page_num}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg.set_content(f'Attached is page {page_num} of {filename}.')

    with open(pdf_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=f'page{page_num}.pdf')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)

def background_email_task(pdf_path, target_page, filename):
    """Function to run in the background."""
    try:
        send_pdf_email(pdf_path, target_page, filename)
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def update_and_send(app,id, target_page):
    conn = get_db_connection()
    row = conn.execute("SELECT filename, total_pages FROM uploads WHERE id = ?", (id,)).fetchone()

    if not row:
        conn.close()
        return False, "File not found"

    filename = row['filename']
    total_pages = row['total_pages']

    if not (1 <= target_page <= total_pages):
        conn.close()
        return False, f"Invalid page. Must be between 1 and {total_pages}"

    # Extract
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    reader = PdfReader(path)
    writer = PdfWriter()
    writer.add_page(reader.pages[target_page - 1])

    output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"page_{target_page}_{id}.pdf")
    with open(output_path, "wb") as output_file:
        writer.write(output_file)

    # Update DB immediately
    conn.execute("UPDATE uploads SET page_number = ? WHERE id = ?", (target_page, id))
    conn.commit()
    conn.close()

    # Start background thread to send email
    thread = threading.Thread(target=background_email_task, args=(output_path, target_page, filename))
    thread.start()

    return True, "Success"

def auto_send_task(app):
    """Note: app must be passed so we can access app.config['UPLOAD_FOLDER']"""
    conn = get_db_connection()
    files = conn.execute(
        "SELECT id, filename, page_number, total_pages FROM uploads WHERE is_auto = 1 AND page_number < total_pages"
    ).fetchall()
    conn.close()

    for row in files:
        new_page = row['page_number'] + 1
        # Pass 'app' through to update_and_send
        update_and_send(app, row['id'], new_page)


def update_scheduler_job(scheduler, app):
    conn = get_db_connection()
    s = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
    conn.close()

    # Remove existing job to avoid duplication
    try:
        scheduler.remove_job('auto_sender')
    except:
        pass

    # Schedule the job with the 'app' instance
    if s['trigger_type'] == 'interval':
        interval_val = int(s['interval_minutes']) if s['interval_minutes'] else 5
        scheduler.add_job(
            id='auto_sender',
            func=auto_send_task,
            args=[app],  # IMPORTANT: Passes app as the first argument
            trigger='interval',
            minutes=interval_val,
            replace_existing=True
        )
    else:
        m_val = int(s['minute']) if s['minute'] else 0
        h_val = int(s['hour']) if s['hour'] else 9
        day_val = s['day'] if s['day'] else '*'

        scheduler.add_job(
            id='auto_sender',
            func=auto_send_task,
            args=[app],  # IMPORTANT: Passes app as the first argument
            trigger='cron',
            minute=m_val,
            hour=h_val,
            day=day_val,
            replace_existing=True
        )

def handle_file_upload(file, upload_folder):
    """
    Saves the file and updates the database.
    Returns: (bool, str) -> (Success Status, Message/Error)
    """
    if not file or not file.filename.endswith('.pdf'):
        return False, "Invalid file type."

    filename = secure_filename(file.filename)
    path = os.path.join(upload_folder, filename)
    file.save(path)

    # Extract metadata
    reader = PdfReader(path)
    total_pages = len(reader.pages)

    # Database operations
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if exists
    cursor.execute("SELECT id FROM uploads WHERE filename = ?", (filename,))
    if cursor.fetchone():
        conn.close()
        return False, "Error: A file with this name has already been uploaded."

    cursor.execute("INSERT INTO uploads (filename, page_number, total_pages) VALUES (?, ?, ?)",
                  (filename, 1, total_pages))
    conn.commit()
    conn.close()

    return True, "File uploaded successfully."


def perform_manual_prev(file_id, upload_folder):
    """
    Handles logic for moving to the previous page.
    Returns: (bool, str) -> (Success, Message)
    """
    conn = get_db_connection()
    row = conn.execute("SELECT filename, page_number FROM uploads WHERE id = ?", (file_id,)).fetchone()
    conn.close()

    if not row:
        return False, "Record not found."

    filename = row['filename']
    page_num = row['page_number']

    if page_num <= 1:
        return False, "Already at the first page."

    target_page = page_num - 1

    # Extract PDF
    path = os.path.join(upload_folder, filename)
    reader = PdfReader(path)
    writer = PdfWriter()
    writer.add_page(reader.pages[target_page - 1])

    output_path = os.path.join(upload_folder, f"page_{target_page}_{file_id}.pdf")
    with open(output_path, "wb") as output_file:
        writer.write(output_file)

    # Update DB
    conn = get_db_connection()
    conn.execute("UPDATE uploads SET page_number = ? WHERE id = ?", (target_page, file_id))
    conn.commit()
    conn.close()

    # Background task
    threading.Thread(target=background_email_task, args=(output_path, target_page, filename)).start()

    return True, f"Previous page ({target_page}) is being sent."

def queue_delayed_email(scheduler, *args):
    """
    Schedules an email task to run 5 seconds after being called.
    args should contain: (pdf_path, target_page, filename)
    """
    run_date = datetime.now() + timedelta(seconds=5)

    scheduler.add_job(
        id=f'delayed_email_{datetime.now().timestamp()}',
        func=background_email_task,
        trigger='date',
        run_date=run_date,
        args=list(args)  # Only pass the email-related arguments here
    )