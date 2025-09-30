
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserSearchQueryViewSet,
    GlobalSearchView,
    QuickSearchView,
    ParseAddressView,
    UserSearchView
)

router = DefaultRouter()
router.register(
    r'user-search-queries',
    UserSearchQueryViewSet,
    basename='user-search-query'
)

urlpatterns = [
    # API endpoints with proper prefix
    path('api/search/global/', GlobalSearchView.as_view(), name='global-search'),
    path('api/search/quick/', QuickSearchView.as_view(), name='quick-search'),
    path('api/search/users/', UserSearchView.as_view(), name='user-search'),
    path('api/search/parse-address/', ParseAddressView.as_view(), name='parse-address'),
    path('api/', include(router.urls)),
]
