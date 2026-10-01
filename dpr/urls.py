from django.urls import path

from .views import search_dpr


urlpatterns = [
    path(
        "search/",
        search_dpr,
        name="search_dpr"
    ),
]