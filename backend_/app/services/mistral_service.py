import os
import json
from datetime import datetime, timezone
from mistralai import Mistral  # official Mistral client
from mistralai.models import UserMessage
from ..models.application import Application

MISTRAL_API_KEY = os.getenv("MISTRAL_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")

client = Mistral(api_key=MISTRAL_API_KEY)

async def mistral_model_response(prompt):
    """
        generic engine that takes prompts
    """
    response = await client.chat.complete_async(
        model=MISTRAL_MODEL,
        messages=[UserMessage(content= prompt)], 
        temperature=0.2
    )

    # Extract response text
    content = response.choices[0].message.content
    return content

async def ping():    
    prompt= "what's the most beautiful city in morocco"
    content = await mistral_model_response(prompt)
    return content

def parse_mistral_response(text, keys) :
    """
    Parse a string response from the LLM that contains JSON inside code fences.

    Example input:
    '```json\n{\n    "company": "company.org", ... }\n```'

    Returns a dictionary with sent_date as a datetime object.
    """
    import re
    # Remove code fences
    results = {}

    for key in keys:
        # Regex to capture the value after key:
        # - optional quotes around key
        # - colon, optional space
        # - value that can be quoted or unquoted, until next comma or closing brace
        pattern = rf'"?{re.escape(key)}"?\s*:\s*(".*?"|[^,}}]+)'
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            # Remove wrapping quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            results[key] = value

    return results


async def classify_application_email(mail) :
    """
    Classify an email and extract internship application details using Mistral AI.
    Expects a mailparser object.
    """
    # Extract raw components
    subject = mail.subject or ""
    from_email = mail.from_[0][1] if mail.from_ else ""
    to_email = mail.to[0][1] if mail.to else ""
    body = mail.body or ""
    date = mail.date or datetime.now()

    prompt = f"""
    You are a structured data extraction assistant.
    Analyze the following email and extract internship application details.

    EMAIL DETAILS:
    Subject: {subject}
    From: {from_email}
    To: {to_email}
    Date: {date}
    Body:
    {body}

    From the following email, extract:
    - company name
    - internship position
    - status (e.g. Awaiting Reply, Rejected, Accepted) if mentioned
    - summary : a short summary of the mail

    Return valid JSON with keys:
    Return a JSON object ***only*** with the following fields:
    {{
        "company": string,
        "position": string,
        "internship_related": boolean,
        "status": string,  // e.g., "Awaiting Reply", "Accepted", "Rejected"
        "sent_date": ISO 8601 date string
        "summary": string
    }}
    if you don't understand the task, in the summary field metion 'not understood'
    """

    # Extract response text
    content = await mistral_model_response(prompt)

    keys = ["company", "position", "status","internship_related","sent_date","summary"]

    return parse_mistral_response(content,keys)


async def extract_internship_description(description):
    prompt= f"""
    You are a structured data extraction assistant.
    Analyze the following internship description:
    \"\"\"{description}\"\"\"

    Extract key structured information with the following informations in a coherent text if given:
    - role: the role or title offered
    - tech_stack: list of technologies/frameworks mentioned
    - advantages: benefits or perks of the internship
    - other_relevant_info: any extra relevant detail

    **Start your response immediately with the first bullet point. DO NOT include any introductory, confirming, or conversational sentences before the list.**
    """
    print(description, flush=True)
    content = await mistral_model_response(prompt)
    return content 


