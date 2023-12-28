from datetime import datetime as _datetime
from decimal import Decimal as _Decimal
from enum import Enum as _Enum
from uuid import UUID as _UUID

from _md5 import MD5Type as _MD5Type
from pydantic import BaseModel as _BaseModel
from pydantic import EmailStr as _EmailStr


class TrStatus(str, _Enum):
    TRUE: str = "TRUE"
    CHARGEBACK: str = "CHARGEBACK"


class TrError(str, _Enum):
    OVERPAID: str = "overpayment"
    UNDERPAID: str = "underpayment"
    NONE: str = "none"


class TransactionResult(_BaseModel):
    """Transaction result - response from tpay"""

    id: int
    tr_id: str
    tr_date: _datetime
    tr_crc: _UUID
    tr_amount: _Decimal
    tr_paid: _Decimal
    tr_desc: str
    tr_status: TrStatus
    tr_error: TrError
    tr_email: _EmailStr
    test_mode: int
    md5sum: _MD5Type
