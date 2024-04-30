from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class PageAndLimitPagination(PageNumberPagination):
    """Пользовательский класс пагинации.

    Устанавливает лимит объектов в ответе на запрос и
    добавляет параметр ограничения количества объектов
    в запросе.
    """

    page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
    page_size_query_param = settings.PAGE_SIZE_QUERY_PARAM
