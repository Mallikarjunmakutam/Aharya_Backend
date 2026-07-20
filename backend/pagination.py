from rest_framework.pagination import PageNumberPagination

class OptionalPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'page_size'

    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get('no_pagination') == 'true':
            return None
        return super().paginate_queryset(queryset, request, view)
