"""
Main URL configuration for citinfos_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Django AllAuth URLs for social authentication
    path('auth/', include('allauth.urls')),
    # New modular app URLs - now enabled for user event tracking
    path('', include('accounts.urls')),
    path('', include('content.urls')),
    path('', include('communities.urls')),
    # Equipment functionality removed
    path('', include('ai_conversations.urls')),
    path('', include('polls.urls')),
    path('', include('messaging.urls')),
    path('', include('notifications.urls')),
    path('', include('analytics.urls')),
    path('', include('core.urls')),
    path('', include('search.urls')),
]

# Backward compatibility redirect: /communities/<slug>/ -> /c/<slug>/
urlpatterns = [
    re_path(r'^communities/(?P<slug>[0-9A-Za-z\-_.]+)/$', RedirectView.as_view(pattern_name=None, url='/c/%(slug)s', permanent=True)),
] + urlpatterns

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
