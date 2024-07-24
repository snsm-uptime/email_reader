import logging
from datetime import datetime
from http import HTTPStatus
from typing import Callable, List, Optional, Tuple

from .client import EmailClient
from .models import (ApiResponse, CursorModel, EmailMessageModel, ImapServer,
                     Meta, PaginatedResponse, PaginationMeta)
from .utils.cache import LRUCache
from .utils.imap_search_criteria import IMAPSearchCriteria
from .utils.parser import parse_email_message


class EmailService:
    def __init__(self, email_user: str, email_pass: str, server: ImapServer, mailbox: str = "inbox"):
        self.email_user = email_user
        self.email_pass = email_pass
        self.server = server
        self.__mailbox = mailbox
        self.ids_cache = LRUCache[List[str]](capacity=3)
        self.email_cache = LRUCache[List[EmailMessageModel]](capacity=3)
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def mailbox(self) -> str:
        return self.__mailbox

    @mailbox.setter
    def mailbox(self, label: str):
        self.__mailbox = label

    def _get_client(self) -> EmailClient:
        return EmailClient(email_user=self.email_user, email_pass=self.email_pass, server=self.server.value, mailbox=self.mailbox)

    def _generate_cache_key(self, criteria: IMAPSearchCriteria) -> str:
        return hash(str(criteria.build())+self.mailbox)

    def __get_email_ids(self, cache_key: str, criteria: IMAPSearchCriteria) -> Tuple[ApiResponse | List[str], float]:
        email_ids = self.ids_cache.get(cache_key)

        query = criteria.build()

        if email_ids is None:
            self.logger.info('No ids cache found')
            # Only create a client if needed
            with self._get_client() as client:
                email_ids, time_ids = client.fetch_email_ids(criteria)
                if not email_ids:
                    return ApiResponse(
                        meta=Meta(
                            status=HTTPStatus.PARTIAL_CONTENT,
                            message=f"No emails found for the given criteria = {
                                query}"
                        ), data=[]), time_ids
                self.ids_cache.put(cache_key, email_ids)
                self.logger.info(
                    f'[CACHE:SAVED] {len(email_ids)} for {query} | {cache_key}')
                return email_ids, time_ids
        else:
            self.logger.info(f'[CACHE:FOUND] {query} | {cache_key}')
            return email_ids, 0.0

    def __get_emails_by_id(
        self, cache_key: str, email_ids: List[str], criteria: IMAPSearchCriteria, cursor: CursorModel
    ) -> Tuple[ApiResponse[PaginatedResponse[EmailMessageModel]], float]:
        cache_key = f'{cache_key}{cursor.page}{cursor.page_size}'
        emails = self.email_cache.get(cache_key)
        time_email = 0.0
        if emails is None:
            self.logger.info('No emails cache found')
            with self._get_client() as client:
                emails, time_email = client.fetch_emails_by_ids(email_ids)
                self.email_cache.put(cache_key, emails)
                self.logger.info(
                    f'[CACHE:SAVED] {len(emails)} for {criteria.build()} in emails cache')
        else:
            self.logger.info(f'Used emails cache for {criteria.build()}')

        response = ApiResponse(
            meta=Meta(status=HTTPStatus.OK if len(emails)
                      > 0 else HTTPStatus.PARTIAL_CONTENT),
            data=PaginatedResponse(
                items=[parse_email_message(email) for email in emails]
            )
        )
        return response, time_email

    def get_paginated(
        self,
        start_date: datetime,
        end_date: datetime,
        cursor: CursorModel,
        senders: Optional[List[str]] = None,
        subjects: Optional[List[str]] = None,
        filter_criteria: Optional[Callable[[EmailMessageModel], bool]] = None,
    ) -> ApiResponse[PaginatedResponse[EmailMessageModel]]:

        criteria = IMAPSearchCriteria().date_range(start_date, end_date)

        and_conditions: list[str] = []

        if senders:
            if len(senders) > 1:
                sender_conditions = [IMAPSearchCriteria().from_(
                    sender).build() for sender in senders]
                and_conditions.append(
                    IMAPSearchCriteria().or_(*sender_conditions).build())
            else:
                and_conditions.append(
                    IMAPSearchCriteria().from_(senders[0]).build())

        if subjects:
            if len(subjects) > 1:
                subject_conditions = [IMAPSearchCriteria().subject(
                    subject).build() for subject in subjects]
                and_conditions.append(IMAPSearchCriteria().or_(
                    *subject_conditions).build())
            else:
                and_conditions.append(
                    IMAPSearchCriteria().subject(subjects[0]).build())

        if and_conditions:
            criteria.and_(*and_conditions)

        cache_key = self._generate_cache_key(criteria)

        # 2. Get email ids
        email_ids, time_ids = self.__get_email_ids(cache_key, criteria)

        if isinstance(email_ids, ApiResponse):
            return email_ids

        # 3. Paginate emails
        total_items = len(email_ids)
        offset = (cursor.page - 1) * cursor.page_size
        # Now that we have the entire list of emails, get only the segment of ids for the page requested
        paginated_email_ids = email_ids[offset:offset + cursor.page_size]

        email_response, time_emails = self.__get_emails_by_id(
            cache_key, paginated_email_ids, criteria, cursor)

        if email_response.meta == HTTPStatus.PARTIAL_CONTENT:
            return email_response

        emails = email_response.data.items
        filtered_total_items = total_items
        if filter_criteria:
            page_total_items = len(emails)
            self.logger.info(f'Found {page_total_items} emails initially')

            emails = list(filter(filter_criteria, email_response.data.items))
            filtered_total_items = len(emails)
            email_response.data.items = emails

            self.logger.info(
                f'Filtered out {page_total_items - filtered_total_items} emails')
            self.logger.info(f'Total images retrieved = {len()}')

        total_items = len(email_ids)
        total_pages = (total_items + cursor.page_size - 1) // cursor.page_size

        next_cursor = CursorModel(
            page=cursor.page+1, page_size=cursor.page_size).encode() if cursor.page < total_pages else None
        prev_cursor = CursorModel(
            page=cursor.page-1, page_size=cursor.page_size).encode() if cursor.page > 1 else None

        # Add pagination metadata
        pagination_meta = PaginationMeta(
            total_items=total_items,
            total_pages=total_pages,
            page_size=cursor.page_size,
            current_page=cursor.page,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor
        )

        email_response.data.pagination = pagination_meta

        # add complete time elapsed
        elapsed_time = time_emails + time_ids
        email_response.meta.request_time = elapsed_time
        msg = f'Found {total_items} items with this query: {criteria.build()}'
        email_response.meta.message = msg

        return email_response
