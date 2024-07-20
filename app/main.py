from datetime import datetime, timedelta
import logging
import os
from typing import List, Optional

import debugpy
from fastapi import APIRouter, FastAPI, Query

from .imap_search_criteria import IMAPSearchCriteria

from .client import EmailClient
from .config import config
from .models import (ApiResponse, EmailMessageModel, ImapServer,
                     PaginatedResponse, SingleResponse)
from .service import EmailService

router = APIRouter(prefix='/email')


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


@router.get("/today/from", response_model=ApiResponse[SingleResponse[List[EmailMessageModel]]])
def query(sender: str):
    with EmailClient(
        email_user=config.EMAIL_USER,
        email_pass=config.EMAIL_PASSWORD,
        server=ImapServer.GOOGLE.value,
        mailbox=config.EMAIL_MAILBOX
    ) as email_client:
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        default_criteria = IMAPSearchCriteria().date_range(
            start_date=yesterday, end_date=tomorrow
        )
        service = EmailService(email_client, default_criteria=default_criteria)

        response = service.get_from_today(sender=sender)
        return response


app = FastAPI()
app.include_router(router)
