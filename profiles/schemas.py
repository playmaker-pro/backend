from typing import Optional

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
