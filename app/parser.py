import base64
import json
from email.message import Message
from email.utils import parsedate_to_datetime
from typing import Optional

from .models import EmailMessageModel


def encode_cursor(page: int, page_size: int) -> str:
    cursor_data = {"page": page, "page_size": page_size}
    cursor_str = json.dumps(cursor_data)
    return base64.urlsafe_b64encode(cursor_str.encode()).decode()


def decode_cursor(cursor: str) -> Optional[dict]:
    try:
        cursor_str = base64.urlsafe_b64decode(cursor.encode()).decode()
        return json.loads(cursor_str)
    except Exception as e:
        print(f"Failed to decode cursor: {e}")
        return None


def parse_email_message(msg: Message) -> EmailMessageModel:
    subject = msg.get('subject')
    from_email = msg.get('from')
    to_emails = msg.get_all('to', [])
    date = msg.get('date')

    # Parse the date if it exists
    if date:
        date = parsedate_to_datetime(date)

    # Extract the body of the email
    if msg.is_multipart():
        body = ''
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" not in content_disposition:
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode(
                        part.get_content_charset(), errors="replace")
                    break
    else:
        body = msg.get_payload(decode=True).decode(
            msg.get_content_charset(), errors="replace")

    return EmailMessageModel(
        subject=subject,
        from_email=from_email,
        to_emails=to_emails,
        date=date,
        body=body
    )
