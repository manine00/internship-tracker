import os
from imapclient import IMAPClient
import mailparser
from datetime import datetime
from ..db import SessionLocal
from ..models.application import Application
from ..models.company import Company
from sqlalchemy.future import select
from datetime import datetime
from .mistral_service import classify_application_email
import asyncio

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")  # Use app password for Gmail
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))

# Define keywords to filter internship-related emails
INTERNSHIP_KEYWORDS = ["internship", "stage", "echange", "PFE", "application"]
# multilingual safe
SENT_FOLDER_NAMES = ["Sent", "Sent Mail", "Messages envoyés"]  
INBOX_FOLDER_NAMES = ["Inbox", "Boîte de réception"]
BANNED_SENDERS = ["jobalerts-noreply@linkedin.com","no-reply@linkedin.com", "noreply@linkedin.com", "spam@example.com", "notification@emails.hellowork.com"]


async def get_new_email_headers(folder_keywords, search_keywords, folder_label="Unknown"):
    new_emails = []

    with IMAPClient(IMAP_HOST, port=EMAIL_PORT, ssl=True) as client:
        client.login(EMAIL_USER, EMAIL_PASS)

        # Find folder
        target_folder = None
        for flags, delimiter, folder_name in client.list_folders():
            name = folder_name.decode() if isinstance(folder_name, bytes) else folder_name
            if any(fk.lower() in name.lower() for fk in folder_keywords):
                target_folder = name
                break

        if target_folder is None:
            all_folders = [folder_name.decode() if isinstance(folder_name, bytes) else folder_name
                           for _, _, folder_name in client.list_folders()]
            print(f"DEBUG — Available folders for {folder_label}:", all_folders)
            raise ValueError(f"{folder_label} folder not found")

        client.select_folder(target_folder)
        criteria = build_or_subject_criteria(search_keywords)
        msg_ids = client.search(criteria)
        print(f"DEBUG — {folder_label} matching subjects found:", len(msg_ids))

        async with SessionLocal() as session:
            for msgid in msg_ids:
                msgid_str = str(msgid)

                # Skip if already in DB
                exists = await session.execute(
                    select(Application).where(Application.email_id == msgid_str)
                )
                if exists.scalars().first():
                    continue

                # Fetch envelope (headers only)
                envelope = client.fetch([msgid], ['ENVELOPE'])[msgid][b'ENVELOPE']
                sender_email = envelope.from_[0].mailbox.decode() + "@" + envelope.from_[0].host.decode()

                # Skip banned senders
                if sender_email.lower() in BANNED_SENDERS:
                    continue

                new_emails.append({
                    "msgid": msgid_str,
                    "from": sender_email,
                    "subject": envelope.subject.decode() if envelope.subject else "",
                    "date": envelope.date
                })

    return new_emails

async def classify_emails(email_headers, folder_keywords):
    """Fetch full email only for new headers and classify them."""
    classified_emails = []

    with IMAPClient(IMAP_HOST, port=EMAIL_PORT, ssl=True) as client:
        client.login(EMAIL_USER, EMAIL_PASS)

        # Select the folder before fetching
        target_folder = None
        for flags, delimiter, folder_name in client.list_folders():
            name = folder_name.decode() if isinstance(folder_name, bytes) else folder_name
            if any(fk.lower() in name.lower() for fk in folder_keywords):
                target_folder = name
                break

        if not target_folder:
            raise ValueError("Folder not found for classification step")

        client.select_folder(target_folder)

        for email in email_headers:
            msgid = int(email["msgid"])
            data = client.fetch([msgid], ['RFC822'])[msgid]
            parsed_mail = mailparser.parse_from_bytes(data[b'RFC822'])
            classified_mail = await classify_application_email(parsed_mail)

            classified_emails.append({
                "msgid": email["msgid"],
                "mail": classified_mail
            })

    return classified_emails



async def ingest_raw_emails(email_headers, folder_keywords):
    """PHASE 1: Fetch full email text and save to DB instantly (No AI yet)."""
    with IMAPClient(IMAP_HOST, port=EMAIL_PORT, ssl=True) as client:
        client.login(EMAIL_USER, EMAIL_PASS)

        # Select folder logic
        target_folder = next((name.decode() if isinstance(name, bytes) else name for _, _, name in client.list_folders() if any(fk.lower() in (name.decode() if isinstance(name, bytes) else name).lower() for fk in folder_keywords)), None)
        if not target_folder: return
        client.select_folder(target_folder)

        async with SessionLocal() as session:
            for email in email_headers:
                msgid = int(email["msgid"])
                data = client.fetch([msgid], ['RFC822'])[msgid]
                parsed_mail = mailparser.parse_from_bytes(data[b'RFC822'])
                
                # Bundle text for AI
                raw_text = f"Subject: {parsed_mail.subject}\nFrom: {parsed_mail.from_[0][1] if parsed_mail.from_ else ''}\nBody:\n{parsed_mail.body}"
                
                app_entry = Application(
                    email_id=email["msgid"],
                    sent_date=parse_iso_datetime(str(parsed_mail.date)) if parsed_mail.date else datetime.utcnow(),
                    raw_text=raw_text,
                    ai_status="PENDING",
                    status="Pending AI Analysis"
                )
                session.add(app_entry)
            await session.commit()


async def process_ai_queue():
    """PHASE 2: Process pending emails slowly to respect Mistral Rate Limits."""
    async with SessionLocal() as session:
        pending_apps = await session.execute(
            select(Application).where(Application.ai_status == "PENDING")
        )
        
        for app in pending_apps.scalars().all():
            try:
                print(f"Processing AI for email {app.email_id}...", flush=True)
                ai_data = await classify_application_email(app.raw_text)
                
                if not ai_data or not ai_data.get("company"):
                    app.ai_status = "FAILED"
                    await session.commit()
                    continue

                # Handle Company
                company_result = await session.execute(select(Company).where(Company.name == ai_data["company"]))
                company = company_result.scalars().first()
                if not company:
                    company = Company(name=ai_data["company"])
                    session.add(company)
                    await session.flush()
                
                # Update Application
                app.company_id = company.id
                app.position = ai_data.get("position", "Unknown Position")
                app.status = ai_data.get("status", "Awaiting Reply")
                app.summary = ai_data.get("summary", "")
                app.ai_status = "COMPLETED"
                
                await session.commit()
                
                # THROTTLE: Polite delay to avoid 429 Rate Limit
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Mistral error on {app.email_id}: {e}", flush=True)
                await session.rollback() # Rollback the current failed email
                continue


async def fetch_sent_applications():
    print("Fetching new emails...", flush=True)
    sent_headers = await get_new_email_headers(SENT_FOLDER_NAMES, INTERNSHIP_KEYWORDS, "Sent")
    inbox_headers = await get_new_email_headers(INBOX_FOLDER_NAMES, INTERNSHIP_KEYWORDS, "Inbox")

    await ingest_raw_emails(sent_headers, SENT_FOLDER_NAMES)
    await ingest_raw_emails(inbox_headers, INBOX_FOLDER_NAMES)

#-- Helper functions --

from datetime import datetime

def parse_iso_datetime(value):
    if isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        # convert to naive datetime (strip tzinfo)
        return dt.replace(tzinfo=None)
    return value

def build_or_subject_criteria(keywords: list[str]):
    """Build a nested OR search criteria for IMAPClient."""
    if not keywords:
        return ['ALL']
    if len(keywords) == 1:
        return ['SUBJECT', keywords[0]]

    # Start with first two keywords
    criteria = ['OR', ['SUBJECT', keywords[0]], ['SUBJECT', keywords[1]]]

    # Nest remaining keywords
    for kw in keywords[2:]:
        criteria = ['OR', criteria, ['SUBJECT', kw]]
    return criteria