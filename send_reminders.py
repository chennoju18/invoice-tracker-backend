import smtplib
from email.mime.text import MIMEText
from pymongo import MongoClient
from datetime import datetime

EMAIL_USER = "chennoju.18@gmail.com"
EMAIL_PASS = "enihnystdldlhgll"   
TO_EMAIL = "chennoju.18@gmail.com"

client = MongoClient("mongodb://localhost:27017/")
db = client["invoiceDB"]
collection = db["invoices"]

def send_email(invoice):
    subject = f"Invoice Reminder: {invoice['vendor']}"
    body = f"""
    Hello,

    This is a reminder that your invoice from {invoice['vendor']} is due on {invoice['due_date']}.

    Amount: {invoice['amount']}

    - Invoice Tracker App
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = TO_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, TO_EMAIL, msg.as_string())
        print(f"✅ Reminder sent for invoice: {invoice['vendor']} due on {invoice['due_date']}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def check_due_invoices():
    today = datetime.now().strftime("%d/%m/%Y")
    print(f"📅 Checking for invoices due today: {today}")

    invoices = collection.find({"due_date": today})

    found = False
    for invoice in invoices:
        found = True
        print(f"📬 Sending reminder for: {invoice['vendor']}")
        send_email(invoice)

    if not found:
        print("ℹ️ No invoices due today.")

check_due_invoices()

