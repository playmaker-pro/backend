import enum


class Environment(enum.Enum):
    PRODUCTION: str = "production"
    STAGING: str = "staging"
    DEV: str = "dev"
    TEST: str = "test"

    def __str__(self):
        return self.value
