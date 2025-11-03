# config/pagination.py
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"   # permite ?page_size=100, etc.
    max_page_size = 1000                  # límite sano para exportaciones grandes
