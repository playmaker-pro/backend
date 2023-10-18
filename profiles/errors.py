class VerificationCompletionFieldsWrongSetup(Exception):
    pass


class SerializerError(Exception):
    def __init__(self, message):
        super().__init__(message)


class TeamContributorNotFoundServiceException(Exception):
    """
    Raised when a TeamContributor object is not found in service-level functions.
    This is a generic exception meant to signal the absence of a TeamContributor
    """

    pass


class TeamContributorAlreadyExistServiceException(Exception):
    """
    Raised when attempting to create or add a TeamContributor that already
    exists in service-level functions.
    """

    default_detail = (
        "Voivodeship object is required. "
        "You should provide voivodeship obj as fallows: voivodeship_obj: {id: 1}"
    )


class LanguageDoesNotExistException(Exception):
    """Raises when language does not exist in DB"""

    ...
