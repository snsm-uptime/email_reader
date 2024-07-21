from http import HTTPStatus
import logging
from typing import Callable, Optional, TypeVar
from .cache import LRUCache

from fastapi import HTTPException
from datetime import datetime

from .client import EmailClient
from .imap_search_criteria import IMAPSearchCriteria
from .parser import parse_email_message
from .models import (
    CursorModel, Meta, PaginationMeta, PaginatedResponse, ApiResponse, EmailMessageModel, ImapServer
)

ModelType = TypeVar('ModelType')


class EmailService:
    def __init__(self, email_user: str, email_pass: str, server: ImapServer, mailbox: str = "inbox"):
        self.email_user = email_user
        self.email_pass = email_pass
        self.server = server
        self.mailbox = mailbox
        self.cache = LRUCache(capacity=3)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _get_client(self) -> EmailClient:
        return EmailClient(email_user=self.email_user, email_pass=self.email_pass, server=self.server.value, mailbox=self.mailbox)

    def _generate_cache_key(self, criteria: IMAPSearchCriteria) -> str:
        return hash(str(criteria.build()))

    def get_paginated(
        self,
        start_date: datetime,
        end_date: datetime,
        cursor: CursorModel,
        filter: Optional[Callable[[EmailMessageModel], bool]] = None
    ) -> ApiResponse[PaginatedResponse[EmailMessageModel]]:
        time_total = 0.0

        criteria = IMAPSearchCriteria().date_range(start_date, end_date)
        cache_key = self._generate_cache_key(criteria)

        # 2. Get email ids
        email_ids = self.cache.get(cache_key)
        time_ids = 0.0

        if email_ids is None:
            # Only create a client if needed
            with self._get_client() as client:
                email_ids, time_ids = client.fetch_email_ids(criteria)
                time_total += time_ids
                if not email_ids:
                    return ApiResponse(
                        meta=Meta(
                            request_time=time_total,
                            status=HTTPStatus.NO_CONTENT,
                            message=f"No emails found for the given criteria = {
                                criteria}"
                        ))
                self.cache.put(cache_key, email_ids)
                self.logger.info(
                    f'Saved {len(email_ids)} results for {criteria} in cache')
        else:
            self.logger.info(f'Used cache for {criteria}')

        # 3. Paginate emails
        total_items = len(email_ids)
        offset = (cursor.page - 1) * cursor.page_size
        # Now that we have the entire list of emails, get only the segment of ids for the page requested
        paginated_email_ids = email_ids[offset:offset + cursor.page_size]

        with self._get_client() as client:
            emails, time_email = client.fetch_emails_by_ids(
                paginated_email_ids)
            time_total += time_email

        email_models = [parse_email_message(email) for email in emails]

        filtered_total_items = total_items
        if filter:
            page_total_items = len(email_models)
            self.logger.info(f'Found {page_total_items} emails initially')

            email_models = list(filter(filter, email_models))
            filtered_total_items = len(email_models)

            self.logger.info(
                f'Filtered out {page_total_items - filtered_total_items} emails')
            self.logger.info(f'Total images retrieved = {len()}')

        total_pages = (total_items + cursor.page_size - 1) // cursor.page_size

        next_cursor = CursorModel(
            page=cursor.page+1, page_size=cursor.page_size).encode()
        prev_cursor = CursorModel(
            page=cursor.page-1, page_size=cursor.page_size).encode() if cursor.page > 1 else None

        pagination_meta = PaginationMeta(
            total_items=total_items,
            total_pages=total_pages,
            page_size=cursor.page_size,
            current_page=cursor.page,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor
        )

        response = ApiResponse(
            meta=Meta(status=200, request_time=time_total,
                      message=f"{filtered_total_items} Emails retrieved successfully"),
            data=PaginatedResponse(
                pagination=pagination_meta,
                items=email_models
            )
        )
        return response
