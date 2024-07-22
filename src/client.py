import email
import imaplib
import logging
from email.message import Message
from typing import List, Optional, Tuple

from .utils.decorators import timed_operation
from .utils.imap_search_criteria import IMAPSearchCriteria


class EmailClient:
    def __init__(self, email_user: str, email_pass: str, server: str, mailbox: str = "inbox"):
        self.server = server
        self.email_user = email_user
        self.email_pass = email_pass
        self.mailbox = mailbox
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self.logger = logging.getLogger(__name__)

    def connect(self):
        try:
            self.connection = imaplib.IMAP4_SSL(self.server)
            self.connection.login(self.email_user, self.email_pass)
            self.connection.select(self.mailbox)
            self.logger.debug('Connected to the email server')
        except Exception as e:
            self.logger.exception(
                f'Failed to connect to the email server: {e}')
            raise

    @timed_operation
    def fetch_email_ids(self, criteria: IMAPSearchCriteria) -> Tuple[Optional[List[str]], float]:
        try:
            status, data = self.connection.search(None, criteria.build())
            if status == 'OK':
                return data[0].split()
            self.logger.error(f'Status not OK: {status}')
        except Exception as e:
            self.logger.exception(f'Error fetching email IDs: {e}')
        return None

    @timed_operation
    def fetch_emails_by_ids(self, email_ids: List[str]) -> Tuple[List[Message], float]:
        emails: List[Message] = []
        for email_id in email_ids:
            try:
                status, msg_data = self.connection.fetch(email_id, "(RFC822)")
                if status != 'OK':
                    self.logger.error(
                        f'Failed to get email with ID {email_id}')
                    continue
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        emails.append(msg)
            except Exception as e:
                self.logger.exception(
                    f'Error fetching email with ID {email_id}: {e}')
        return emails

    def disconnect(self):
        if self.connection:
            try:
                self.connection.logout()
                self.logger.debug('Disconnected from the email server')
            except Exception as e:
                self.logger.error(
                    f'Failed to disconnect from the email server: {e}')

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()
