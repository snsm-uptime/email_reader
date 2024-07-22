import logging
from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends, FastAPI, Path, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .config import config
from .models import (ApiResponse, CursorModel, DateRange, EmailMessageModel,
                     ImapServer, Meta, PaginatedResponse,
                     PydanticValidationError)
from .service import EmailService
from .utils import catch_standard_errors, configure_root_logger

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
    return JSONResponse(status_code=response.meta.status, content=jsonable_encoder(response))


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


@app.get("/{mailbox}", response_model=ApiResponse[PaginatedResponse[EmailMessageModel]])
@catch_standard_errors
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
        page=page, page_size=page_size, cursor=cursor)
    result = email_service.get_paginated(
        start_date=date_range.start_date,
        end_date=date_range.end_date,
        cursor=cursor
    )
    return respond_with(result)

app.include_router(router)
