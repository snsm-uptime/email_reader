import json
import logging
from http import HTTPStatus
from typing import List, Optional

from fastapi import APIRouter, Depends, FastAPI, Path, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .config import config
from .models import (ApiResponse, CursorModel, DateRange, EmailMessageModel,
                     ImapServer, Meta, PaginatedResponse,
                     PydanticValidationError)
from .service import EmailService
from .utils import configure_root_logger

app = FastAPI()

router = APIRouter()

configure_root_logger(
    log_level=logging.INFO if config.ENVIRONMENT == 'prod' else logging.DEBUG)
logger = logging.getLogger(__name__)


email_service = EmailService(
    email_user=config.EMAIL_USER,
    email_pass=config.EMAIL_PASSWORD,
    server=ImapServer.GOOGLE
)


def respond_with(response: ApiResponse) -> JSONResponse:
    content = jsonable_encoder(response)
    json_content = json.dumps(content)
    content_length = len(json_content.encode('utf-8'))

    headers = {"Content-Length": str(content_length)}
    return JSONResponse(status_code=response.meta.status, content=content, headers=headers)


@app.exception_handler(RequestValidationError)
async def custom_request_validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    custom_errors = [
        str(PydanticValidationError(
            field=".".join(map(str, error.get("loc"))),
            message=error.get("msg"),
            error=error.get("ctx", {}).get("error"),
            input=error.get('input')
        ))
        for error in errors
    ]
    meta = Meta(
        status=HTTPStatus.UNPROCESSABLE_ENTITY,
        message='.\n'.join(custom_errors),
        request_time=0.0
    )

    return JSONResponse(status_code=meta.status, content={"meta": meta.model_dump()})


@app.exception_handler(ValueError)
async def custom_validation_exception_handler(request: Request, exc: ValueError):
    errors = '. '.join(exc.args)
    status_code = HTTPStatus.NOT_ACCEPTABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "meta": Meta(status=status_code, message=errors).model_dump()
        })


@app.get("/{mailbox}", response_model=ApiResponse[PaginatedResponse[EmailMessageModel]])
# @catch_standard_errors
async def read_emails(
    mailbox: str = Path(..., description="Mailbox to get the data from"),
    date_range: DateRange = Depends(),
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    page: Optional[int] = Query(None, description="Current page"),
    page_size: Optional[int] = Query(
        None, description="Number of items per page"),
    senders: Optional[str] = Query(
        None, description="List of email senders to filter by. Use semicolon separated values"),
    subject: Optional[List[str]] = Query(
        None, description="List of strings that could match a subject"),
):
    email_service.mailbox = mailbox
    cursor = CursorModel(
        page=page, page_size=page_size, cursor=cursor)

    result = email_service.get_paginated(
        start_date=date_range.start_date,
        end_date=date_range.end_date,
        cursor=cursor,
        senders=senders.split(';') if senders else None,
        subjects=subject
    )
    return JSONResponse(status_code=result.meta.status, content=jsonable_encoder(result.model_dump()))

app.include_router(router)
