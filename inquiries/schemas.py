from enum import Enum as _Enum


class InquiryPlanTypeRef(str, _Enum):
    BASIC: str = "BASIC"
    PREMIUM_L: str = "PREMIUM_INQUIRIES_L"
    PREMIUM_XL: str = "PREMIUM_INQUIRIES_XL"
    PREMIUM_XXL: str = "PREMIUM_INQUIRIES_XXL"

    @property
    def inquiry_count(self) -> int:
        return {
            InquiryPlanTypeRef.BASIC: 2,
            InquiryPlanTypeRef.PREMIUM_L: 3,
            InquiryPlanTypeRef.PREMIUM_XL: 5,
            InquiryPlanTypeRef.PREMIUM_XXL: 10,
        }[self]

    @property
    def price(self) -> float:
        return {
            InquiryPlanTypeRef.BASIC: 0,
            InquiryPlanTypeRef.PREMIUM_L: 7.99,
            InquiryPlanTypeRef.PREMIUM_XL: 10.99,
            InquiryPlanTypeRef.PREMIUM_XXL: 19.99,
        }[self]
