from enum import Enum as _Enum


class InquiryPlanTypeRef(str, _Enum):
    BASIC: str = "BASIC"
    FREEMIUM_STANDARD: str = "FREEMIUM_STANDARD"
    FREEMIUM_PLAYER: str = "FREEMIUM_PLAYER"
    PREMIUM_STANDARD: str = "PREMIUM_STANDARD"
    PREMIUM_PLAYER: str = "PREMIUM_PLAYER"
    PREMIUM_L: str = "PREMIUM_INQUIRIES_L"
    PREMIUM_XL: str = "PREMIUM_INQUIRIES_XL"
    PREMIUM_XXL: str = "PREMIUM_INQUIRIES_XXL"

    @property
    def inquiry_count(self) -> int:
        return {
            InquiryPlanTypeRef.BASIC: 2,
            InquiryPlanTypeRef.FREEMIUM_STANDARD: 5,  # Club/Coach/etc. freemium
            InquiryPlanTypeRef.FREEMIUM_PLAYER: 10,  # Player freemium
            InquiryPlanTypeRef.PREMIUM_STANDARD: 30,  # Club/Coach/etc. premium
            InquiryPlanTypeRef.PREMIUM_PLAYER: 30,  # Player premium
            InquiryPlanTypeRef.PREMIUM_L: 3,
            InquiryPlanTypeRef.PREMIUM_XL: 5,
            InquiryPlanTypeRef.PREMIUM_XXL: 10,
        }[self]

    @property
    def price(self) -> float:
        return {
            InquiryPlanTypeRef.BASIC: 0,
            InquiryPlanTypeRef.FREEMIUM_STANDARD: 0,  # Freemium is free
            InquiryPlanTypeRef.FREEMIUM_PLAYER: 0,  # Freemium is free
            InquiryPlanTypeRef.PREMIUM_STANDARD: 0,  # Premium via subscription
            InquiryPlanTypeRef.PREMIUM_PLAYER: 0,  # Premium via subscription
            InquiryPlanTypeRef.PREMIUM_L: 7.99,
            InquiryPlanTypeRef.PREMIUM_XL: 10.99,
            InquiryPlanTypeRef.PREMIUM_XXL: 19.99,
        }[self]
