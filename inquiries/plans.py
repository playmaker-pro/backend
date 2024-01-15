from pydantic import BaseModel


class InquiryPlanSchema(BaseModel):
    name: str
    description: str
    limit: int
    default: bool = False

    @classmethod
    def basic(cls) -> "InquiryPlanSchema":
        """Create basic plan schema"""
        return cls(name="Basic", description="Basic plan", limit=5, default=True)

    @classmethod
    def premium(cls) -> "InquiryPlanSchema":
        """Create premium plan schema"""
        return cls(name="Premium", description="Premium plan", limit=10)


basic_plan = InquiryPlanSchema.basic()
premium_plan = InquiryPlanSchema.premium()
