class ForbiddenInProduction(Exception):
    def __str__(self) -> str:
        return "Operation is forbidden in production environment!"
