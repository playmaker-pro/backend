from enum import Enum as _Enum


class InquiryPlanTypeRef(str, _Enum):
    BASIC: str = "BASIC"
    PREMIUM5: str = "PREMIUM_INQUIRIES_5"
    PREMIUM10: str = "PREMIUM_INQUIRIES_10"
    PREMIUM25: str = "PREMIUM_INQUIRIES_25"

    @property
    def text_choice(self) -> tuple:
        """Get text choice for TransactionType"""
        return self.value, self.value
