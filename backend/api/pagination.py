from rest_framework.pagination import PageNumberPagination


class PageAndLimitPagination(PageNumberPagination):
    '''Пользовательский класс пагинации.

    Устанавливает лимит объектов в ответе на запрос и
    добавляет параметр ограничения количества объектов
    в запросе.
    '''
    page_size = 6
    page_size_query_param = 'limit'
