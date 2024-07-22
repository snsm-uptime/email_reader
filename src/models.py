from pydantic import BaseModel, Field
from typing import Optional
import base64
import json
from datetime import datetime
from enum import Enum
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, EmailStr, Field

T = TypeVar('T')
D = TypeVar('D', bound=BaseModel)


class DateRange(BaseModel):
    start_date: datetime = Field(...,
                                 description="Start date in ISO format (YYYY-MM-DD)")
    end_date: datetime = Field(...,
                               description="End date in ISO format (YYYY-MM-DD)")


class PaginationMeta(BaseModel):
    total_items: Optional[int] = None
    total_pages: Optional[int] = None
    page_size: Optional[int] = None
    current_page: Optional[int] = None
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None


class Meta(BaseModel):
    status: int
    message: Optional[str] = None
    request_time: float = 0.0


class PaginatedResponse(BaseModel, Generic[T]):
    pagination: Optional[PaginationMeta] = None
    items: Optional[List[T]] = None


class SingleResponse(BaseModel, Generic[T]):
    item: Optional[T] = None


class ApiResponse(BaseModel, Generic[T]):
    meta: Meta
    data: Optional[T] = None


class ImapServer(Enum):
    GOOGLE = 'imap.gmail.com'
    OUTLOOK = 'imap-mail.outlook.com'
    YAHOO = 'imap.mail.yahoo.com'
    CUSTOM = 'custom'


class EmailMessageModel(BaseModel):
    subject: Optional[str]
    from_email: Optional[EmailStr]
    to_emails: List[EmailStr] = []
    date: Optional[datetime]
    body: Optional[str]


class CursorModel(BaseModel):
    page_size: Optional[int] = Field(
        default=10, description="The size of the page to fetch")
    page: Optional[int] = Field(
        default=1, description="The current page number")
    cursor: Optional[str] = Field(
        default=None, description="The cursor string for pagination")

    def encode(self) -> str:
        """
        Encode the current page and page_size into a base64 cursor string.

        Returns:
            str: The base64 encoded cursor string.
        """
        cursor_data = {"page": self.page, "page_size": self.page_size}
        cursor_str = json.dumps(cursor_data)
        self.cursor = base64.urlsafe_b64encode(cursor_str.encode()).decode()
        return self.cursor

    @staticmethod
    def encode_from_dict(page: int, page_size: int) -> str:
        """
        Encode given page and page_size into a base64 cursor string.

        Args:
            page (int): The current page number.
            page_size (int): The size of the page to fetch.

        Returns:
            str: The base64 encoded cursor string.
        """
        cursor_data = {"page": page, "page_size": page_size}
        cursor_str = json.dumps(cursor_data)
        return base64.urlsafe_b64encode(cursor_str.encode()).decode()

    @staticmethod
    def decode(cursor: str) -> 'CursorModel':
        """
        Decode a base64 cursor string into a CursorModel instance.

        Args:
            cursor (str): The base64 encoded cursor string.

        Returns:
            CursorModel: A CursorModel instance with page and page_size populated.
        """
        try:
            cursor_str = base64.urlsafe_b64decode(cursor.encode()).decode()
            data = json.loads(cursor_str)
            return CursorModel(
                page=data.get('page', None),
                page_size=data.get('page_size', None),
                cursor=cursor
            )
        except (base64.binascii.Error, json.JSONDecodeError) as e:
            raise ValueError("Invalid cursor format") from e
