from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'polls', views.PollViewSet)
router.register(r'poll-options', views.PollOptionViewSet)
router.register(r'poll-votes', views.PollVoteViewSet)
router.register(r'poll-voters', views.PollVoterViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
