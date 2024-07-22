import logging
import os
from typing import Optional

import debugpy
from fastapi import APIRouter, Depends, FastAPI, Path, Query


from .config import config
from .models import (ApiResponse, DateRange, EmailMessageModel, ImapServer,
                     PaginatedResponse, CursorModel)
from .service import EmailService

app = FastAPI()

router = APIRouter()

logger = logging.getLogger(__name__)


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
    page: Optional[int] = Query(None, description="Current page"),
    page_size: Optional[int] = Query(
        None, description="Number of items per page")
):
    email_service.mailbox = mailbox
    cursor = CursorModel(
        page=page if page else 1, page_size=page_size if page_size else config.PAGE_SIZE, cursor=cursor)
    response = email_service.get_paginated(
        start_date=date_range.start_date,
        end_date=date_range.end_date,
        cursor=cursor
    )
    return response

app.include_router(router)
