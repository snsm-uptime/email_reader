import base64
import quopri
import re
from email.message import Message
from email.utils import parsedate_to_datetime

from ..models import EmailMessageModel
from email.header import decode_header, make_header


def decode_base64(encoded_str: str) -> str:
    """Decode a base64 encoded string."""
    decoded_bytes = base64.b64decode(encoded_str)
    return decoded_bytes.decode('utf-8')


def decode_quoted_printable(encoded_str: str) -> str:
    """Decode a quoted-printable encoded string."""
    decoded_bytes = quopri.decodestring(encoded_str)
    return decoded_bytes.decode('utf-8')


def decode_subject(subject: str) -> str:
    """Decode an email subject that might be encoded."""
    decoded_header = str(make_header(decode_header(subject)))
    return decoded_header


def decode_match(encoded_str: str) -> str:
    """Decode a string based on its encoding type."""
    match = re.match(r'=\?([^?]+)\?([BQ])\?([^?]+)\?=', encoded_str)
    if match:
        charset, encoding, encoded_text = match.groups()
        if encoding == 'B':
            return decode_base64(encoded_text)
        elif encoding == 'Q':
            return decode_quoted_printable(encoded_text)
    return encoded_str


def parse_email_message(msg: Message) -> EmailMessageModel:
    subject = decode_subject(msg.get('subject'))
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
