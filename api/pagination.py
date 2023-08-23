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
