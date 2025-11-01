# Internship application tracker v1.0

## Overview
The Internship Application Analyzer is a full-stack project built to simplify the management of internship-related communications.
It automatically retrieves your internship-related emails, classifies and summarizes them using Mistral’s SDK, and provides an intuitive frontend interface for exploring the structured results.

At its core, the backend connects to your email account via IMAP, detects relevant internship messages from both Inbox and Sent folders, and sends them through Mistral’s AI model to extract:

- Company name
- Internship position
- Application date
- Application status (sent, replied, rejected, etc.)
- Concise summary of the conversation

The Mistral SDK was chosen for its high-quality natural language understanding and ease of integration. It enables the system to convert raw email content into rich, structured data without manual parsing, capturing nuanced details like tone, intent, and next steps from email exchanges.

## Features
- Automatic Email Fetching: Retrieves internship-related messages from both Sent and Inbox folders via IMAP.
- Smart Filtering: Detects subjects containing keywords like internship, stage, PFE, or application.
- AI-Powered Classification: Uses the Mistral SDK to extract key fields and summarize each message.
- Duplicate Avoidance: Skips emails already stored in the database.
- Noise Filtering: Ignores irrelevant senders (e.g., LinkedIn, calendar invites).
- Persistent Storage: Saves structured data in a PostgreSQL database.
- Timeline Visualization: Automatically groups exchanges per company for chronological display.
- Dockerized Deployment: Fully containerized for easy setup and consistent development environments.

## Tech Stack
| Component            | Technology                   |
| -------------------- | ---------------------------- |
| **Backend**          | FastAPI (Python)             |
| **Frontend**         | Vue.js 3 + TypeScript (Vite) |
| **Database**         | PostgreSQL                   |
| **ORM**              | SQLAlchemy (async)           |
| **Mail Client**      | IMAPClient                   |
| **AI SDK**           | Mistral                      |
| **Containerization** | Docker & Docker Compose      |

## Installation & Setup

1. Clone the repository
   
````
git clone https://github.com/manine00/internship-tracker.git
cd internship-analyzer
````
2. Create a ``.env`` file in the backend_ directory
   
   copy the given code below and add your email credentials and API keys:

````
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
IMAP_HOST=imap.gmail.com
EMAIL_PORT=993
MISTRAL_KEY=your_mistral_api_key
````
### Important – Gmail IMAP Setup

Gmail does not allow you to log in directly with your normal account password when connecting through external applications (like this one).
For security reasons, you must generate a special App Password, which acts as a secure token that only grants access to your mailbox.

This step is required only once.

Here’s how to do it:

1. Open your Google Account Security Settings: Visit https://myaccount.google.com/security
2. Enable 2-Step Verification (if it’s not already enabled):
Scroll down to "Signing in to Google" → click 2-Step Verification → follow the setup steps. You’ll need this active before you can create app passwords.
3. Generate an App Password:
    - Once 2-Step Verification is on, go back to the Security page.
    - Click App Passwords (it appears below 2-Step Verification).
    - Log in again if prompted.
    - Under Select App, choose Mail.
    - Under Select Device, choose Other (Custom name) → type for example ``InternshipTracker``.
    - Click Generate.
    - Google will display a 16-character password — copy it.
4. Use this password in your ``.env`` file
5. Enable IMAP in Gmail (if not already):
    - Go to Gmail → Settings  → See all settings → Forwarding and POP/IMAP tab.
    - Under “IMAP access,” choose Enable IMAP → click Save Changes.
  
Once this is done, your backend will be able to connect safely to your Gmail account to fetch internship-related emails.

###  Getting Your Mistral API Key

The project uses Mistral AI’s SDK to analyze and summarize internship-related emails.
You need to create an API key to authenticate your requests.

Here’s how to get it:

1. Create a Mistral AI account: Go to https://mistral.ai
2. Access your API dashboard: Once logged in, open the Mistral Console.
3. Generate a new API key:
   - Navigate to “API Keys” in the sidebar.
   - Click “Create new key.”
   - Give it a name 
   - Copy the generated key.
4. Store it in your ``.env`` file.

## Running with Docker
1. Build and start containers
   ````
   docker-compose up --build
   ````
This launches:
- The FastAPI backend
- The PostgreSQL database
- The Vue.js frontend

2. Verify everything is running
   - Backend API documentation: http://localhost:8000/docs
   - Frontend dashboard: http://localhost:5173


## Usage
Once running, the backend will:

- Connect to your Gmail account using IMAP.
- Fetch internship-related emails from both Sent and Inbox folders.
- Classify and summarize them with Mistral.
- Store structured results in PostgreSQL.
- Expose the data to the Vue frontend.

The frontend then displays:
- A structured list of all AI-parsed applications.
- A company-wise timeline view of email exchanges.
- Automatic summaries and extracted descriptions.
  
