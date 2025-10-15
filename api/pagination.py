from rest_framework import pagination


class PagePagination(pagination.PageNumberPagination):
    """
    Custom pagination class
    ?page_size=x - count of elements
    ?page_numer=x - page number
    example: ?page_size=10&page_number=4 - get queryset elements between 41 and 50
    """

    page_size: int = 10
    page_size_query_param: str = "page_size"
    max_page_size: int = 100


class TransferRequestCataloguePagePagination(PagePagination):
    """
    Custom pagination class for transfer request catalogue page.
    """


class ClubTeamsPagination(PagePagination):
    """
    Custom pagination class for club teams page.
    """


class ProfileSearchPagination(PagePagination):
    """
    Custom pagination class for profile search page.
    """

    page_size: int = 5


class InternalMappingPagination(PagePagination):
    """
    Custom pagination class for internal mapping endpoints.
    No default page size - returns all data unless limit is specified.
    """
    page_size = None  # No default limit
    page_size_query_param = 'limit'
    max_page_size = 10000  # Hard cap at 10k items
