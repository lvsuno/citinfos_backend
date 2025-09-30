from rest_framework import serializers
from .models import UserSearchQuery

class UserSearchQuerySerializer(serializers.ModelSerializer):
    filters = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = UserSearchQuery
        fields = ['id', 'user', 'query', 'search_type', 'filters', 'results_count', 'created_at', 'is_deleted']
        read_only_fields = ['user']
