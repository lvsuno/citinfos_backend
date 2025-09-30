from django.contrib import admin
from .models import UserSearchQuery

@admin.register(UserSearchQuery)
class UserSearchQueryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'search_type', 'results_count', 'created_at')
    search_fields = ('query',)
    list_filter = ('search_type', 'created_at')
