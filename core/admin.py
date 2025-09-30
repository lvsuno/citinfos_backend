from django.contrib import admin
from .models import Country, AdministrativeDivision


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'iso2', 'iso3']
    search_fields = ['name', 'iso2', 'iso3']
    ordering = ['name']


@admin.register(AdministrativeDivision)
class AdministrativeDivisionAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'admin_level', 'admin_level_name', 'parent', 'data_source']
    list_filter = ['country', 'admin_level', 'data_source', 'point_type', 'boundary_type']
    search_fields = ['name', 'local_name', 'admin_code', 'local_code']
    ordering = ['country__name', 'admin_level', 'name']
    raw_id_fields = ['parent']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'local_name', 'country', 'admin_level', 'parent')
        }),
        ('Administrative Codes', {
            'fields': ('admin_code', 'local_code'),
            'classes': ('collapse',)
        }),
        ('Geometry', {
            'fields': ('area_geometry', 'boundary_geometry', 'point_geometry', 'centroid'),
            'classes': ('collapse',)
        }),
        ('Classification', {
            'fields': ('point_type', 'boundary_type'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('population', 'area_sqkm', 'description', 'attributes', 'data_source'),
            'classes': ('collapse',)
        })
    )

    def admin_level_name(self, obj):
        return obj.admin_level_name
    admin_level_name.short_description = 'Level Type'
