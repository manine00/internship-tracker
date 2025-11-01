from dotenv import load_dotenv
import os

load_dotenv()  

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")

# sanity check
if EMAIL_USER is None or EMAIL_PASS is None:
    raise ValueError("EMAIL_USER and EMAIL_PASS must be set in .env")
