import base64
import quopri
import re
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parsedate_to_datetime
from logging import getLogger

from bs4 import BeautifulSoup

from ..models import EmailMessageModel


def decode_base64(encoded_str: str) -> str:
    """Decode a base64 encoded string."""
    decoded_bytes = base64.b64decode(encoded_str)
    return decoded_bytes.decode('utf-8')


def decode_quoted_printable(encoded_str: str) -> str:
    """Decode a quoted-printable encoded string."""
    decoded_bytes = quopri.decodestring(encoded_str)
    return decoded_bytes.decode('utf-8')


def decode(subject: str) -> str:
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

    def parse_message_body(msg: Message) -> str:
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = part.get("Content-Disposition")

                    # Process parts even if Content-Disposition is missing or not an attachment
                    if content_disposition is None or "attachment" not in content_disposition:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body = payload.decode(charset, errors="replace")
                            if "text/plain" in content_type:
                                return body
                            elif "text/html" in content_type:
                                soup = BeautifulSoup(body, "html.parser")
                                return soup.get_text(separator='\n').strip()
            else:
                content_type = msg.get_content_type()
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="replace")
                    if "text/plain" in content_type:
                        return body
                    elif "text/html" in content_type:
                        soup = BeautifulSoup(body, "html.parser")
                        return soup.get_text(separator='\n').strip()
            return None
        except Exception as e:
            raise e

    subject = decode(msg.get('subject'))
    from_email = decode(msg.get('from'))
    to_emails = msg.get_all('to', [])
    date = msg.get('date')

    # Parse the date if it exists
    if date:
        date = parsedate_to_datetime(date)

    return EmailMessageModel(
        subject=subject,
        from_email=from_email,
        to_emails=to_emails,
        date=date,
        body=parse_message_body(msg)
    )
