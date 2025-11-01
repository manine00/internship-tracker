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


""" async def get_emails_from_folder(folder_keywords, search_keywords, folder_label="Unknown"):
    
    emails = []

    with IMAPClient(IMAP_HOST, port=EMAIL_PORT, ssl=True) as client:
        client.login(EMAIL_USER, EMAIL_PASS)

        # Find matching folder
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
            raise ValueError(f"{folder_label} folder not found in your mailbox")

        client.select_folder(target_folder)
        print(target_folder, flush=True)
        # Build search criteria
        criteria = build_or_subject_criteria(search_keywords)
        print(criteria, flush=True)
        messages = client.search(criteria)
        print(messages, flush=True)
        response = client.fetch(messages, ['RFC822'])
        
        for msgid, data in response.items():
            parsed_mail = mailparser.parse_from_bytes(data[b'RFC822'])
            emails.append({
                "msgid": str(msgid),
                "mail": await classify_application_email(parsed_mail)
            })
    print(emails, flush=True)
    return emails

    
    async def get_sent_emails():
    return await get_emails_from_folder(
        folder_keywords=SENT_FOLDER_NAMES,
        search_keywords=INTERNSHIP_KEYWORDS,
        folder_label="Sent"
    )

    async def get_received_emails():
        return await get_emails_from_folder(
            folder_keywords=INBOX_FOLDER_NAMES,
            search_keywords=INTERNSHIP_KEYWORDS,
            folder_label="Inbox"
        )

      """






# before storing mails, i should send them through ai
# i need to refactore this code even more because having all serveices in the same file is not okay 

async def store_emails(emails):
    """Store emails in the database."""
    async with SessionLocal() as session:
        for email in emails:
            # Skip if already in database
            exists = await session.execute(
                select(Application).where(Application.email_id == email["msgid"])
            )
            if exists.scalars().first():
                continue

            existing_company = await session.execute(
                select(Company).where(Company.name == email["mail"]["company"])
            )
            company = existing_company.scalars().first()
            if not company:
                company = Company(name=email["mail"]["company"])
                session.add(company)
                await session.flush() 
                    

            app_entry = Application(
                company_id=company.id,
                position=email["mail"]["position"],
                sent_date=parse_iso_datetime(email["mail"]["sent_date"]),
                email_id=email["msgid"], 
                status=email["mail"]["status"],
                summary=email["mail"]["summary"]
            )
            session.add(app_entry)
        await session.commit()


async def update_emails(emails):
    """Update existing emails only."""
    async with SessionLocal() as session:
        for email in emails:
            result = await session.execute(
                select(Application).where(Application.email_id == email["msgid"])
            )
            app_entry = result.scalars().first()
            if not app_entry:
                # Skip if it doesn't exist
                continue
            
            existing_company = await session.execute(
                select(Company).where(Company.name == email["mail"]["company"])
            )
            company = existing_company.scalars().first()
            if not company:
                company = Company(name=email["mail"]["company"])
                session.add(company)
                await session.flush()
            

            # Update fields
            app_entry.company_id = company.id
            app_entry.position = email["mail"]["position"]
            app_entry.sent_date = parse_iso_datetime(email["mail"]["sent_date"])
            app_entry.status = email["mail"]["status"]
            app_entry.summary = email["mail"]["summary"]

        await session.commit()


async def fetch_and_store_applications():
    print("Fetching new emails...", flush=True)

    # Step 1: headers only
    sent_headers = await get_new_email_headers(SENT_FOLDER_NAMES, INTERNSHIP_KEYWORDS, "Sent")
    inbox_headers = await get_new_email_headers(INBOX_FOLDER_NAMES, INTERNSHIP_KEYWORDS, "Inbox")

    # Step 2: fetch full email + classify
    sent_emails = await classify_emails(sent_headers, SENT_FOLDER_NAMES)
    inbox_emails = await classify_emails(inbox_headers, INBOX_FOLDER_NAMES)

    # Step 3: store in DB
    await store_emails(sent_emails)
    await store_emails(inbox_emails)



# -- interface with the main --
async def fetch_sent_applications():
    await fetch_and_store_applications()


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