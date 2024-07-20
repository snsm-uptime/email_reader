from datetime import datetime, timedelta
import logging
import os
from typing import List, Optional

import debugpy
from fastapi import APIRouter, Depends, FastAPI, Path, Query

from .imap_search_criteria import IMAPSearchCriteria

from .client import EmailClient
from .config import config
from .models import (ApiResponse, DateRange, EmailMessageModel, ImapServer,
                     PaginatedResponse, SingleResponse)
from .service import EmailService

app = FastAPI()

router = APIRouter()

logger = logging.getLogger(__name__)


# @router.get("/today", response_model=ApiResponse[PaginatedResponse[EmailMessageModel]])
# def query(sender: str, subject: Optional[str] = Query(None)):
#     with EmailClient(
#         email_user=config.EMAIL_USER,
#         email_pass=config.EMAIL_PASSWORD,
#         server=ImapServer.GOOGLE.value,
#         mailbox=config.EMAIL_MAILBOX
#     ) as email_client:
#         service = EmailService(email_client)
#         msg = f"Searching emails from {sender}"
#         if subject:
#             msg += f" and subject containing {subject}"
#         logger.info(msg)
#         messages = service.get_from_today(
#             sender=sender, subject_filter=subject)
#         return ApiResponse(meta=messages)
email_service = EmailService(
    email_user=config.EMAIL_USER,
    email_pass=config.EMAIL_PASSWORD,
    server=ImapServer.GOOGLE
)


@app.get("/{mailbox}", response_model=ApiResponse[PaginatedResponse[EmailMessageModel]])
async def read_emails(
    mailbox: str = Path(..., description="Mailbox to get the data from"),
    date_range: DateRange = Depends(),
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    page_size: int = Query(10, description="Number of items per page")
):
    response = email_service.get_paginated(
        start_date=date_range.start_date,
        end_date=date_range.end_date,
        page_size=page_size,
        cursor=cursor
    )
    return response

app.include_router(router)
