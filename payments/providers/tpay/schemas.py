import typing as _typing
from datetime import datetime as _datetime
from datetime import timedelta as _timedelta
from decimal import Decimal as _Decimal
from enum import Enum as _Enum
from uuid import UUID as _UUID

from pydantic import BaseModel as _BaseModel
from pydantic import BaseSettings as _BaseSettings
from pydantic import Field as _Field
from pydantic import HttpUrl as _HttpUrl


class TpayResponseResultEnum(str, _Enum):
    SUCCESS: str = "success"
    FAILED: str = "failed"


class TpayTransactionStatusEnum(str, _Enum):
    PENDING: str = "pending"
    PAID: str = "paid"
    CORRECT: str = "correct"
    REFUND: str = "refund"
    ERROR: str = "error"


class TpayTransactionMethodEnum(str, _Enum):
    PAY_BY_LINK: str = "pay_by_link"
    TRANSFER: str = "transfer"
    SALE: str = "sale"


class TpayAuthBody(_BaseModel):
    client_id: str
    client_secret: str
    scope: str

    @classmethod
    def from_config(cls, config: _BaseSettings) -> "TpayAuthBody":
        """Parse tpay auth body shcema object from config"""
        return cls.parse_obj(config.dict())


class TpayPayerData(_BaseModel):
    payer_id: _typing.Optional[str] = _Field(alias="payerId")
    email: str
    name: str
    phone: _typing.Optional[str]
    address: _typing.Optional[str]
    code: _typing.Optional[str]
    city: _typing.Optional[str]
    country: _typing.Optional[str]
    postal_code: _typing.Optional[str] = _Field(alias="postalCode")


class TpayTransactionBody(_BaseModel):
    class TpayCallbacks(_BaseModel):
        class TpayPayerUrls(_BaseModel):
            success: _HttpUrl
            error: _HttpUrl

        class TpayNotification(_BaseModel):
            email: str
            # result_url: _HttpUrl

        payerUrls: TpayPayerUrls
        notification: TpayNotification

    amount: _Decimal
    description: str
    hiddenDescription: str
    payer: TpayPayerData
    lang: str = "pl"
    callbacks: TpayCallbacks


class TpayAuthResponse(_BaseModel):
    issued_at: int
    expires_in: int
    access_token: str
    token_type: str
    scope: str
    client_id: str

    @property
    def expires_at(self) -> _datetime:
        """Get expiration date as python datetime"""
        return _datetime.utcnow() + _timedelta(seconds=self.expires_in)

    @property
    def is_valid(self) -> bool:
        """Check if token is still valid"""
        return self.expires_at > _datetime.utcnow()

    @property
    def headers(self) -> dict:
        """Parse headers based on object data"""
        return {"Authorization": f"{self.token_type} {self.access_token}"}


class TpayErrorResponse(_BaseModel):
    class TpayErrorList(_BaseModel):
        class TpayError(_BaseModel):
            error_code: str = _Field(alias="errorCode")
            error_message: str = _Field(alias="errorMessage")
            field_name: str = _Field(alias="fieldName")
            dev_message: str = _Field(alias="devMessage")
            doc_url: str = _Field(alias="docUrl")

        __root__: _typing.List[TpayError]

    errors: TpayErrorList
    request_id: str = _Field(alias="requestId")
    result: TpayResponseResultEnum


class TpayTransactionDate(_BaseModel):
    creation: _typing.Optional[_datetime]
    realization: _typing.Optional[_datetime]


class TpayTransactionResponse(_BaseModel):
    class TpayPaymentsData(_BaseModel):
        status: TpayTransactionStatusEnum
        method: _typing.Optional[TpayTransactionMethodEnum]
        amount_paid: _Decimal = _Field(alias="amountPaid")
        date: TpayTransactionDate

    result: TpayResponseResultEnum
    request_id: str = _Field(alias="requestId")
    transaction_id: str = _Field(alias="transactionId")
    title: str
    pos_id: str = _Field(alias="posId")
    status: TpayTransactionStatusEnum
    date: TpayTransactionDate
    amount: _Decimal
    currency: str
    description: str
    hidden_description: str = _Field(alias="hiddenDescription")
    payer: TpayPayerData
    payments: TpayPaymentsData
    url: _HttpUrl = _Field(alias="transactionPaymentUrl")

    @property
    def to_update_django_object(self) -> dict:
        """Prepare dictionary based on schema to update a Transaction object in django"""
        return {
            "raw_create_response": self.json(by_alias=True),
            "url": self.url,
        }


class TpayValidationErrors(str, _Enum):
    INVALID_MD5 = "MD5 checksum is invalid"
    TRANSACTION_NOT_FOUND = "Transaction not found"
    INVALID_DATA = "Invalid data"
    TEST_MODE_NOT_ALLOWED = "Application does not accept test_mode transactions"


class DataAssertingErrors(str, _Enum):
    AMOUNT = "Amount is invalid"
    UUID = "UUID is invalid"
    DESCRIPTION = "Description is invalid"

    @property
    def parse_full(self) -> str:
        return f"{TpayValidationErrors.INVALID_DATA}: {self}"


class TrStatus(str, _Enum):
    TRUE: str = "TRUE"
    CHARGEBACK: str = "CHARGEBACK"
    PAID: str = "PAID"

    @property
    def acceptable(self) -> bool:
        return self in [self.TRUE, self.PAID]


class TrError(str, _Enum):
    OVERPAID: str = "overpayment"
    UNDERPAID: str = "underpayment"
    NONE: str = "none"

    @property
    def acceptable(self) -> bool:
        return self in [self.NONE, self.OVERPAID]


class TpayTransactionMode(str, _Enum):
    TEST: str = "1"
    PRODUCTION: str = "0"

    @property
    def is_test(self) -> bool:
        return self.value is self.TEST


class TpayTransactionResult(_BaseModel):
    """Transaction result - response from tpay"""

    merchant_id: int = _Field(alias="id")
    tr_id: str
    tr_date: _datetime
    tr_crc: _UUID
    tr_amount: _Decimal
    tr_paid: _Decimal
    tr_desc: str
    tr_status: TrStatus
    tr_error: TrError
    tr_email: str
    test_mode: TpayTransactionMode
    md5sum: str

    _errors: _typing.List[str] = []

    def prepare_to_hash(self, secret: str) -> str:
        """Parse response for django"""
        return f"{self.merchant_id}{self.tr_id}{self.tr_amount}{self.tr_crc}{secret}"
