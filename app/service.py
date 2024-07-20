import copy
from datetime import datetime
from email.message import Message
from http import HTTPStatus
from typing import List, Optional, Tuple

from .models import ApiResponse, Meta, SingleResponse, EmailMessageModel

from .config import config
from .imap_search_criteria import IMAPSearchCriteria
from .decorators import timed_operation
from .client import EmailClient
from .parser import parse_email_message


class EmailService:
    def __init__(self, client: EmailClient, default_criteria: Optional[IMAPSearchCriteria] = None):
        self.client = client
        self.__default_criteria = default_criteria or IMAPSearchCriteria()

    @property
    def default_criteria(self) -> IMAPSearchCriteria:
        return self.__default_criteria

    @default_criteria.setter
    def default_criteria(self, criteria: IMAPSearchCriteria) -> None:
        self.__default_criteria = criteria

    @timed_operation
    def __get_mail_from(self, sender: str, subject_filter: Optional[str] = None) -> Tuple[List[Message], float]:
        criteria = copy.deepcopy(self.__default_criteria).from_(sender)
        if subject_filter:
            criteria = criteria.subject(subject_filter)
        final_criteria = IMAPSearchCriteria().and_(criteria.build())
        ids = self.client.fetch_email_ids(final_criteria)
        if ids is None:
            return []
        emails = self.client.get_emails(ids)
        return emails

    def get_from_today(self, sender: str) -> ApiResponse[SingleResponse[Optional[List[EmailMessageModel]]]]:
        emails, exec_time = self.__get_mail_from(sender)
        if not emails:
            meta = Meta(status=HTTPStatus.NO_CONTENT,
                        message="You have no mail for today")
        else:
            meta = Meta(status=HTTPStatus.OK,
                        message=f"Today you got {len(emails)} emails in your {config.EMAIL_MAILBOX} mailbox.")

        data = []
        for i in emails:
            data.append(parse_email_message(i))

        meta.request_time = exec_time
        return ApiResponse(meta=meta, data=SingleResponse(item=data))
