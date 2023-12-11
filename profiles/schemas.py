from typing import List, Optional

from pydantic import BaseModel


class PlayerProfileGET(BaseModel):
    """
    Player profile GET response schema.
    Schema required for url: /api/v1/profiles/{UUID}/
    """

    slug: str
    user: dict
    external_links: Optional[dict]
    player_positions: Optional[dict]
    profile_video: Optional[dict]
    transfer_status: Optional[dict]
    height: Optional[str]
    weight: Optional[str]
    prefered_leg: Optional[int]
    training_ready: Optional[dict]
    playermetrics: Optional[dict]
    role: str


class TransferStatusPhoneNumberSchema(BaseModel):
    """
    Transfer status phone number schema.
    Schema required for url: /api/v1/profiles/{UUID}/transfer-status/
    """

    number: str
    dial_code: str


class TransferStatusLeagueSchema(BaseModel):
    """
    Transfer status league schema.
    Schema required for url: /api/v1/profiles/{UUID}/transfer-status/
    """

    id: int
    name: str
    is_parent: bool


class TransferStatusStatusSchema(BaseModel):
    """
    Transfer status status schema.
    Schema required for url: /api/v1/profiles/{UUID}/transfer-status/
    """

    id: int
    name: str


class TransferStatusAdditionalInfoSchema(BaseModel):
    """
    Transfer status additional info schema.
    Schema required for url: /api/v1/profiles/{UUID}/transfer-status/
    """

    id: int
    name: str


class TransferStatusSchema(BaseModel):
    """
    Transfer status schema.
    Schema required for url: /api/v1/profiles/{UUID}/transfer-status/
    """

    contact_email: str
    phone_number: TransferStatusPhoneNumberSchema
    status: TransferStatusStatusSchema
    additional_info: TransferStatusAdditionalInfoSchema
    league: TransferStatusLeagueSchema


class TransferRequestSchema(BaseModel):
    """
    Transfer request schema.
    Schema required for url: /api/v1/profiles/{UUID}/transfer-request/
    """

    requesting_team: dict
    gender: str
    status: dict
    position: dict
    number_of_trainings: dict
    additional_info: List[dict]
    salary: dict
    contact_email: str
    phone_number: dict
