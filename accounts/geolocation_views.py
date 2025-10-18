"""
Geolocation views for IP-based user location detection and administrative division lookup.
"""

import logging
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Min, Q
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from core.models import Country, AdministrativeDivision
from core.serializers import CountryPhoneDataSerializer
from core.utils import get_client_ip, get_location_from_ip

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_countries(request):
    """
    Get all countries that have divisions in the database.
    Results are cached in Redis for 24 hours.

    Returns:
    {
        "success": true,
        "countries": [
            {
                "id": "uuid",
                "name": "Country Name",
                "iso2": "CA",
                "iso3": "CAN",
                "default_admin_level": 4,
                "admin_levels": {
                    "0": "country",
                    "1": "province",
                    "4": "municipality"
                }
            }
        ]
    }
    """
    try:
        # Try to get from Redis cache first
        cache_key = 'available_countries_v1'
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.debug("Returning countries from Redis cache")
            return Response(cached_data)

        # Cache miss - fetch from database
        logger.info("Cache miss - fetching countries from database")

        # Get only countries that have divisions
        country_ids = AdministrativeDivision.objects.values_list(
            'country_id', flat=True
        ).distinct()

        countries = Country.objects.filter(
            id__in=country_ids
        ).order_by('name')

        result = []
        for country in countries:
            boundary_types = country.get_boundary_types_by_level()

            country_data = {
                'id': str(country.id),
                'name': country.name,
                'iso2': country.iso2,
                'iso3': country.iso3,
                'default_admin_level': country.default_admin_level,
                'default_division_name': country.get_default_division_name(),
                'admin_levels': boundary_types
            }
            result.append(country_data)

        response_data = {
            'success': True,
            'countries': result,
            'count': len(result)
        }

        # Cache in Redis for 24 hours (86400 seconds)
        cache.set(cache_key, response_data, 86400)
        logger.info(f"Cached {len(result)} countries in Redis for 24 hours")

        return Response(response_data)

    except Exception as e:
        logger.error(f"Error fetching countries: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_countries_with_phone_data(request):
    """
    Get all countries with phone data, with optional filtering.

    Query params:
    - region (optional): Filter by region (e.g., 'West Africa', 'North America')
    - search (optional): Search by country name, ISO2, or ISO3 code
    - iso3 (optional): Get specific country by ISO3 code

    Returns:
    {
        "success": true,
        "countries": [
            {
                "iso2": "BJ",
                "iso3": "BEN",
                "name": "Benin",
                "phone_code": "+229",
                "flag_emoji": "🇧🇯",
                "region": "West Africa"
            }
        ],
        "count": 17,
        "region": "West Africa"  // if filtered
    }
    """
    try:
        # Check cache first
        region_filter = request.query_params.get('region')
        search_query = request.query_params.get('search')
        iso3_filter = request.query_params.get('iso3')

        # Build cache key
        cache_key = f'countries_phone_data_v1'
        if region_filter:
            cache_key += f'_region_{region_filter}'
        if search_query:
            cache_key += f'_search_{search_query}'
        if iso3_filter:
            cache_key += f'_iso3_{iso3_filter}'

        # Try cache
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Returning countries from cache: {cache_key}")
            return Response(cached_data)

        # Build query
        queryset = Country.objects.exclude(
            phone_code__isnull=True
        ).exclude(
            phone_code__exact=''
        ).order_by('name')

        # Apply filters
        if iso3_filter:
            queryset = queryset.filter(iso3__iexact=iso3_filter)

        if region_filter:
            queryset = queryset.filter(region__iexact=region_filter)

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(iso2__iexact=search_query) |
                Q(iso3__iexact=search_query)
            )

        # Serialize
        serializer = CountryPhoneDataSerializer(queryset, many=True)

        response_data = {
            'success': True,
            'countries': serializer.data,
            'count': len(serializer.data)
        }

        if region_filter:
            response_data['region'] = region_filter

        if search_query:
            response_data['search'] = search_query

        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, response_data, 3600)
        logger.info(f"Cached {len(serializer.data)} countries: {cache_key}")

        return Response(response_data)

    except Exception as e:
        logger.error(f"Error fetching countries with phone data: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_regions(request):
    """
    Get all unique regions with country counts.

    Returns:
    {
        "success": true,
        "regions": [
            {
                "name": "West Africa",
                "country_count": 17,
                "sample_countries": ["Benin", "Nigeria", "Ghana"]
            }
        ]
    }
    """
    try:
        cache_key = 'available_regions_v1'
        cached_data = cache.get(cache_key)

        if cached_data:
            logger.debug("Returning regions from cache")
            return Response(cached_data)

        # Get all regions with counts
        from django.db.models import Count

        regions = Country.objects.exclude(
            region__isnull=True
        ).exclude(
            region__exact=''
        ).values('region').annotate(
            country_count=Count('id')
        ).order_by('-country_count')

        # Get sample countries for each region
        result = []
        for region_data in regions:
            region_name = region_data['region']
            sample_countries = list(
                Country.objects.filter(
                    region=region_name
                ).values_list('name', flat=True).order_by('name')[:3]
            )

            result.append({
                'name': region_name,
                'country_count': region_data['country_count'],
                'sample_countries': sample_countries
            })

        response_data = {
            'success': True,
            'regions': result,
            'count': len(result)
        }

        # Cache for 24 hours
        cache.set(cache_key, response_data, 86400)
        logger.info(f"Cached {len(result)} regions")

        return Response(response_data)

    except Exception as e:
        logger.error(f"Error fetching regions: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_divisions_by_level(request):
    """
    Get administrative divisions by country and level.

    Query params:
    - country_id (required): UUID of the country
    - admin_level (required): Administrative level (0, 1, 2, 3, 4)
    - parent_id (optional): UUID of parent division to filter by
      * If parent is at a level < admin_level - 1, will get all
        descendants at admin_level
        Example: parent_id=Quebec (level 1), admin_level=4 will
        return all municipalities in Quebec
    - closest_to (optional): UUID of division to find closest to
    - limit (optional): Max results to return (default: 100)

    Returns:
    {
        "success": true,
        "divisions": [
            {
                "id": "uuid",
                "name": "Division Name",
                "admin_level": 1,
                "boundary_type": "province",
                "parent_id": "uuid",
                "parent_name": "Parent Name"
            }
        ]
    }
    """
    try:
        country_id = request.query_params.get('country_id')
        admin_level = request.query_params.get('admin_level')
        parent_id = request.query_params.get('parent_id')
        closest_to = request.query_params.get('closest_to')
        limit = int(request.query_params.get('limit', 100))

        if not country_id:
            return Response({
                'success': False,
                'error': 'country_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if admin_level is None:
            return Response({
                'success': False,
                'error': 'admin_level is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            admin_level = int(admin_level)
        except (ValueError, TypeError):
            return Response({
                'success': False,
                'error': 'admin_level must be an integer'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Build query
        query = AdministrativeDivision.objects.filter(
            country_id=country_id,
            admin_level=admin_level
        )

        # Filter by parent if provided
        if parent_id:
            # Get the parent division to check its level
            try:
                parent = AdministrativeDivision.objects.get(id=parent_id)
                parent_level = parent.admin_level

                # If parent is direct parent, use simple filter
                if parent_level == admin_level - 1:
                    query = query.filter(parent_id=parent_id)
                # If parent is ancestor, traverse down the hierarchy
                else:
                    # Build a recursive query to find all descendants
                    # Start with the parent's direct children
                    current_level = parent_level + 1
                    current_ids = [parent.id]

                    # Traverse down level by level until we reach target
                    while current_level < admin_level:
                        # Get all divisions at current level with parents
                        # in current_ids
                        current_ids = list(
                            AdministrativeDivision.objects.filter(
                                parent_id__in=current_ids,
                                admin_level=current_level
                            ).values_list('id', flat=True)
                        )

                        if not current_ids:
                            # No descendants found at this level
                            break

                        current_level += 1

                    # At this point, current_ids contains all divisions
                    # at admin_level - 1 that are descendants of parent
                    if current_ids and current_level == admin_level:
                        query = query.filter(parent_id__in=current_ids)
                    else:
                        # No valid descendants found
                        query = query.none()

            except AdministrativeDivision.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'Parent division {parent_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)

        # If closest_to is provided, order by distance
        if closest_to:
            try:
                reference_div = AdministrativeDivision.objects.get(
                    id=closest_to
                )
                if reference_div.centroid:
                    # Order by distance from reference division
                    query = query.exclude(
                        centroid__isnull=True
                    ).annotate(
                        distance=Distance('centroid', reference_div.centroid)
                    ).order_by('distance')

                    # Include the reference division itself as first item
                    divisions_list = [reference_div]
                    other_divisions = query.exclude(
                        id=closest_to
                    )[:limit-1]
                    divisions_list.extend(other_divisions)
                    divisions = divisions_list
                else:
                    divisions = query.order_by('name')[:limit]
            except AdministrativeDivision.DoesNotExist:
                divisions = query.order_by('name')[:limit]
        else:
            # Order and limit
            divisions = query.order_by('name')[:limit]

        result = []
        for division in divisions:
            division_data = {
                'id': str(division.id),
                'name': division.name,
                'admin_level': division.admin_level,
                'boundary_type': division.boundary_type,
                'admin_code': division.admin_code,
                'parent_id': (
                    str(division.parent_id) if division.parent else None
                ),
                'parent_name': (
                    division.parent.name if division.parent else None
                ),
            }
            result.append(division_data)

        return Response({
            'success': True,
            'divisions': result,
            'count': len(result)
        })

    except Exception as e:
        logger.error(f"Error fetching divisions: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def find_closest_divisions(country, lat, lng, limit=5):
    """
    Find closest administrative divisions at the default level for a country.
    Returns list of divisions ordered by distance.
    """
    if not country.default_admin_level:
        return []

    user_point = Point(lng, lat, srid=4326)

    # Get divisions at default level for this country
    divisions = AdministrativeDivision.objects.filter(
        country=country,
        admin_level=country.default_admin_level
    ).exclude(
        centroid__isnull=True  # Exclude divisions without centroid
    ).annotate(
        distance=Distance('centroid', user_point)
    ).order_by('distance')[:limit]

    return divisions


@api_view(['POST'])
@permission_classes([AllowAny])
def get_user_location_data(request):
    """
    Get user's geographic location and relevant administrative divisions.

    Expected request body:
    {
        "ip_address": "optional - if not provided, uses request IP"
    }

    Returns:
    {
        "success": true,
        "country": {
            "iso3": "BEN",
            "name": "Benin",
            "default_admin_level": 2,
            "default_division_name": "communes"
        },
        "user_location": {
            "latitude": 6.35,
            "longitude": 2.41,
            "city": "Cotonou",
            "region": "Littoral"
        },
        "closest_divisions": [
            {
                "id": "uuid",
                "name": "Cotonou",
                "boundary_type": "communes",
                "distance_km": 0.5,
                "parent_name": "Littoral"
            },
            // ... 4 more closest divisions
        ],
        "division_search_info": {
            "total_available": 77,
            "search_endpoint": "/api/accounts/search-divisions/",
            "country_filter": "BEN"
        }
    }
    """
    try:
        # Get IP address
        ip_address = request.data.get('ip_address') or get_client_ip(request)

        # Handle localhost/development cases
        if ip_address in ['127.0.0.1', 'localhost', '::1']:
            # Default to Benin for development
            ip_address = None
            mock_location = {
                'country_iso_code': 'BJ',
                'country': 'Benin',
                'region': 'Littoral',
                'city': 'Cotonou',
                'latitude': 6.3703,
                'longitude': 2.3912,
            }
            location_data = mock_location
        else:
            # Get real location from IP
            location_data = get_location_from_ip(ip_address)

        # Get user coordinates
        lat = location_data.get('latitude') if location_data else None
        lng = location_data.get('longitude') if location_data else None

        if not lat or not lng:
            return Response({
                'error': 'Unable to determine location coordinates',
                'fallback': True,
                'message': 'Please select your location manually'
            }, status=status.HTTP_200_OK)

        # Find the division that contains the user's location
        user_point = Point(lng, lat, srid=4326)

        # First, try to find which country the user is in
        try:
            country_with_point = Country.objects.filter(
                administrativedivision__area_geometry__contains=user_point
            ).distinct().first()

            if not country_with_point:
                # Fallback: find closest country
                country_with_point = Country.objects.annotate(
                    min_distance=Min(
                        Distance(
                            'administrativedivision__centroid',
                            user_point
                        )
                    )
                ).order_by('min_distance').first()

            if not country_with_point:
                return Response({
                    'error': 'Unable to determine country',
                    'fallback': True
                }, status=status.HTTP_200_OK)

            # Find the division at default level that contains the point
            default_level = country_with_point.default_admin_level
            user_division = AdministrativeDivision.objects.filter(
                country=country_with_point,
                admin_level=default_level,
                area_geometry__contains=user_point
            ).first()

            # If no division contains the point, find the closest one
            if not user_division:
                user_division = AdministrativeDivision.objects.filter(
                    country=country_with_point,
                    admin_level=default_level,
                    centroid__isnull=False
                ).annotate(
                    distance=Distance('centroid', user_point)
                ).order_by('distance').first()

            if not user_division:
                return Response({
                    'error': 'No administrative divisions found',
                    'fallback': True
                }, status=status.HTTP_200_OK)

            # Now find the 4 closest divisions at the same level
            # Get reference point for distance calculation
            if user_division.centroid:
                reference_point = user_division.centroid
            elif user_division.area_geometry:
                reference_point = user_division.area_geometry.centroid
            else:
                reference_point = user_point

            # Find 5 closest divisions (including the user's division)
            closest_divisions_qs = AdministrativeDivision.objects.filter(
                country=country_with_point,
                admin_level=default_level,
                centroid__isnull=False
            ).annotate(
                distance=Distance('centroid', reference_point)
            ).order_by('distance')[:5]

            # Build response list
            closest_divisions = []
            for division in closest_divisions_qs:
                distance_m = division.distance.m if division.distance else None
                distance_km = (
                    round(distance_m / 1000, 1) if distance_m else None
                )

                closest_divisions.append({
                    'id': str(division.id),
                    'name': division.name,
                    'boundary_type': division.boundary_type,
                    'distance_km': distance_km,
                    'parent_name': (
                        division.parent.name if division.parent else None
                    ),
                    'admin_code': division.admin_code,
                    'country_name': division.country.name
                })

        except Exception as e:
            logger.error(f"Error finding division: {e}")
            return Response({
                'error': 'Error processing location',
                'fallback': True
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Get total count for search info
        total_divisions = AdministrativeDivision.objects.filter(
            country=country_with_point,
            admin_level=default_level
        ).count()

        # Get detected country with phone data
        detected_country_data = {
            'iso3': country_with_point.iso3,
            'iso2': country_with_point.iso2,
            'name': country_with_point.name,
            'phone_code': country_with_point.phone_code,
            'flag_emoji': country_with_point.flag_emoji,
            'region': country_with_point.region,
            'default_admin_level': default_level,
            'default_division_name': (
                country_with_point.get_default_division_name()
            )
        }

        # Get other countries from the same region (for signup phone selection)
        regional_countries = []
        if country_with_point.region:
            regional_countries_qs = Country.objects.filter(
                region=country_with_point.region
            ).exclude(
                id=country_with_point.id
            ).exclude(
                phone_code__isnull=True
            ).exclude(
                phone_code__exact=''
            ).order_by('name')[:10]  # Limit to 10 regional countries

            regional_countries = [
                {
                    'iso2': c.iso2,
                    'iso3': c.iso3,
                    'name': c.name,
                    'phone_code': c.phone_code,
                    'flag_emoji': c.flag_emoji,
                    'region': c.region
                }
                for c in regional_countries_qs
            ]

        return Response({
            'success': True,
            'country': detected_country_data,
            'user_location': {
                'latitude': lat,
                'longitude': lng,
                'administrative_division_id': str(user_division.id),
                'division_name': user_division.name,
                'region': (
                    location_data.get('region') if location_data else None
                ),
                'ip_address': ip_address
            },
            'closest_divisions': closest_divisions,
            'division_search_info': {
                'total_available': total_divisions,
                'search_endpoint': '/api/accounts/search-divisions/',
                'country_filter': country_with_point.iso3
            },
            'regional_countries': regional_countries,
            'country_search_info': {
                'search_endpoint': '/api/auth/countries/phone-data/',
                'region_filter': country_with_point.region,
                'total_in_region': len(regional_countries) + 1
            }
        })

    except Exception as e:
        logger.error(f"Error in get_user_location_data: {e}")
        return Response({
            'error': 'Internal server error',
            'message': 'Unable to process location request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_divisions(request):
    """
    Search administrative divisions by name within a country.

    Query parameters:
    - country: Country ISO3 code (required)
    - q: Search query (required, min 2 characters)
    - limit: Max results (default 10, max 50)

    Returns:
    {
        "results": [
            {
                "id": "uuid",
                "name": "Division Name",
                "boundary_type": "communes",
                "parent_name": "Parent Division",
                "admin_code": "BEN-ADM2-001"
            }
        ],
        "total": 25,
        "query": "search term"
    }
    """
    try:
        country_code = request.GET.get('country')
        query = request.GET.get('q', '').strip()
        limit = min(int(request.GET.get('limit', 10)), 50)

        if not country_code:
            return Response({
                'error': 'Country parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(query) < 2:
            return Response({
                'error': 'Query must be at least 2 characters'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get country
        try:
            country = Country.objects.get(iso3=country_code)
        except Country.DoesNotExist:
            return Response({
                'error': f'Country {country_code} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Search divisions at default level
        divisions = AdministrativeDivision.objects.filter(
            country=country,
            admin_level=country.default_admin_level,
            name__icontains=query
        ).select_related('parent').order_by('name')[:limit]

        results = []
        for division in divisions:
            results.append({
                'id': str(division.id),
                'name': division.name,
                'boundary_type': division.boundary_type,
                'parent_name': (
                    division.parent.name if division.parent else None
                ),
                'admin_code': division.admin_code
            })

        # Get total count for pagination info
        total = AdministrativeDivision.objects.filter(
            country=country,
            admin_level=country.default_admin_level,
            name__icontains=query
        ).count()

        return Response({
            'results': results,
            'total': total,
            'query': query,
            'country': country_code,
            'division_type': country.get_default_division_name()
        })

    except ValueError:
        return Response({
            'error': 'Invalid limit parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error in search_divisions: {e}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_division_neighbors(request, division_id):
    """
    Get the 4 closest neighboring divisions to a specified division.

    Path parameters:
    - division_id: UUID of the division

    Query parameters:
    - limit: Number of neighbors to return (default 4, max 10)

    Returns:
    {
        "success": true,
        "division": {
            "id": "uuid",
            "name": "Division Name",
            "boundary_type": "communes"
        },
        "neighbors": [
            {
                "id": "uuid",
                "name": "Neighbor Name",
                "boundary_type": "communes",
                "distance_km": 5.2,
                "parent_name": "Parent Division",
                "admin_code": "BEN-ADM2-002"
            }
        ]
    }
    """
    try:
        limit = min(int(request.GET.get('limit', 4)), 10)

        # Get the division
        try:
            division = AdministrativeDivision.objects.get(id=division_id)
        except AdministrativeDivision.DoesNotExist:
            return Response({
                'error': f'Division with ID {division_id} not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get the centroid or geometry center
        if division.centroid:
            reference_point = division.centroid
        elif division.area_geometry:
            reference_point = division.area_geometry.centroid
        else:
            return Response({
                'error': 'Division does not have geographic data'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Find neighboring divisions at the same admin level
        neighbors = AdministrativeDivision.objects.filter(
            country=division.country,
            admin_level=division.admin_level
        ).exclude(
            id=division.id  # Exclude the division itself
        ).exclude(
            centroid__isnull=True  # Exclude divisions without centroid
        ).annotate(
            distance=Distance('centroid', reference_point)
        ).order_by('distance')[:limit]

        neighbors_data = []
        for neighbor in neighbors:
            distance_m = neighbor.distance.m if neighbor.distance else None
            distance_km = round(distance_m / 1000, 1) if distance_m else None

            neighbors_data.append({
                'id': str(neighbor.id),
                'name': neighbor.name,
                'boundary_type': neighbor.boundary_type,
                'distance_km': distance_km,
                'parent_name': (
                    neighbor.parent.name if neighbor.parent else None
                ),
                'admin_code': neighbor.admin_code
            })

        # Get level 1 parent (region/department) by traversing up the hierarchy
        level_1_parent = None
        current = division
        while current.parent:
            if current.parent.admin_level == 1:
                level_1_parent = current.parent
                break
            current = current.parent

        return Response({
            'success': True,
            'division': {
                'id': str(division.id),
                'name': division.name,
                'boundary_type': division.boundary_type,
                'admin_level': division.admin_level,
                'parent_name': (
                    division.parent.name if division.parent else None
                ),
                'parent_id': str(division.parent.id) if division.parent else None,
                'admin_code': division.admin_code,
                # Include country info
                'country': {
                    'id': str(division.country.id),
                    'name': division.country.name,
                    'iso3': division.country.iso3,
                    'iso2': division.country.iso2,
                    'default_admin_level': division.country.default_admin_level,
                    'default_division_name': division.country.get_default_division_name(),
                },
                # Include level 1 parent (region/department)
                'level_1_parent': {
                    'id': str(level_1_parent.id),
                    'name': level_1_parent.name,
                    'admin_level': level_1_parent.admin_level,
                } if level_1_parent else None,
            },
            'neighbors': neighbors_data
        })

    except ValueError:
        return Response({
            'error': 'Invalid limit parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error in get_division_neighbors: {e}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_division_geometry(request, division_id):
    """
    Get the geometry (polygon) and centroid for a specific division.
    This endpoint returns GeoJSON geometry for map visualization.

    Args:
        division_id: UUID of the administrative division

    Returns:
        {
            "success": true,
            "division_id": "uuid",
            "name": "Division Name",
            "geometry": {
                "type": "Polygon" or "MultiPolygon",
                "coordinates": [...]  // GeoJSON coordinates
            },
            "centroid": {
                "type": "Point",
                "coordinates": [lng, lat]
            }
        }
    """
    try:
        # Fetch the division with geometry and centroid
        division = AdministrativeDivision.objects.get(id=division_id)

        # Check if division has geometry
        if not division.area_geometry:
            return Response({
                'success': False,
                'error': 'Division has no geometry data'
            }, status=status.HTTP_404_NOT_FOUND)

        # Convert geometry to GeoJSON
        geometry_geojson = None
        if division.area_geometry:
            # Get GeoJSON representation
            geometry_geojson = {
                'type': division.area_geometry.geom_type,
                'coordinates': division.area_geometry.coords
            }

        # Convert centroid to GeoJSON
        centroid_geojson = None
        if division.centroid:
            centroid_geojson = {
                'type': 'Point',
                'coordinates': [division.centroid.x, division.centroid.y]
            }

        return Response({
            'success': True,
            'division_id': str(division.id),
            'name': division.name,
            'boundary_type': division.boundary_type,
            'geometry': geometry_geojson,
            'centroid': centroid_geojson
        })

    except AdministrativeDivision.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Division not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error in get_division_geometry: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_division_by_slug(request):
    """
    Get division details by URL slug and boundary type.
    Used for division-specific pages like /municipality/sherbrooke or /commune/ze

    Query Parameters:
        slug: URL slug (e.g., 'sherbrooke', 'ze')
        country_iso3: REQUIRED - Country code to narrow search (e.g., 'CAN', 'BEN')
        boundary_type: Optional singular boundary type from URL (e.g., 'municipality', 'commune')
        admin_level: Optional admin level override (defaults to country's default_admin_level)

    Returns:
        {
            "success": true,
            "division": {
                "id": "uuid",
                "name": "Sherbrooke",
                "boundary_type": "municipalités",
                "admin_level": 4,
                "country": {
                    "iso3": "CAN",
                    "name": "Canada",
                    "default_admin_level": 4
                },
                "parent": {...},
                "population": 123456,
                "centroid": {"lat": 45.4, "lng": -71.9}
            }
        }
    """
    slug = request.GET.get('slug', '').strip()
    country_iso3 = request.GET.get('country_iso3', '').strip()
    boundary_type_param = request.GET.get('boundary_type', '').strip()
    admin_level_param = request.GET.get('admin_level', '').strip()

    if not slug:
        return Response({
            'success': False,
            'error': 'Slug parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not country_iso3:
        return Response({
            'success': False,
            'error': 'country_iso3 parameter is required to ensure correct admin level lookup'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get the country to determine default admin level
        try:
            country = Country.objects.get(iso3__iexact=country_iso3)
        except Country.DoesNotExist:
            return Response({
                'success': False,
                'error': f'Country with ISO3 code "{country_iso3}" not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Convert slug back to name
        # Try multiple variations to handle both:
        # - 'sherbrooke' -> 'Sherbrooke'
        # - 'saint-denis-de-brompton' -> 'Saint-Denis-de-Brompton' (keep hyphens)
        # - "tno-aquatique-de-la-mrc-du-val-saint-francois" -> "TNO aquatique de la MRC du Val-Saint-François"
        # We'll try the slug as-is first, then with spaces, then normalized versions

        # Start with base query - case-insensitive name search
        # Try exact slug match first (handles hyphenated names like Saint-Denis-de-Brompton)
        divisions = AdministrativeDivision.objects.filter(
            name__iexact=slug,
            country=country
        )

        # If not found, try replacing hyphens with spaces
        if not divisions.exists():
            name_from_slug = slug.replace('-', ' ')
            divisions = AdministrativeDivision.objects.filter(
                name__iexact=name_from_slug,
                country=country
            )

        # If still not found, try normalizing: remove accents and try with/without apostrophes
        # This handles: "de la" vs "d'la", "du" vs "d'", etc.
        if not divisions.exists():
            # Normalize the slug for broader matching
            from django.db.models import Q
            import unicodedata

            # Create a normalized version by removing accents from database names
            # and comparing case-insensitively
            name_pattern = slug.replace('-', ' ')

            # Try fuzzy matching by comparing normalized versions
            # This will match "tno aquatique de la mrc du val saint francois"
            # with "TNO aquatique de la MRC du Val-Saint-François"
            all_divisions = AdministrativeDivision.objects.filter(country=country)

            for div in all_divisions:
                # Normalize both the database name and search term
                db_name_normalized = unicodedata.normalize('NFD', div.name.lower())
                db_name_normalized = ''.join(c for c in db_name_normalized if unicodedata.category(c) != 'Mn')
                db_name_normalized = db_name_normalized.replace("'", ' ').replace('-', ' ')
                db_name_normalized = ' '.join(db_name_normalized.split())  # normalize whitespace

                search_normalized = unicodedata.normalize('NFD', name_pattern.lower())
                search_normalized = ''.join(c for c in search_normalized if unicodedata.category(c) != 'Mn')
                search_normalized = search_normalized.replace("'", ' ').replace('-', ' ')
                search_normalized = ' '.join(search_normalized.split())

                if db_name_normalized == search_normalized:
                    divisions = AdministrativeDivision.objects.filter(id=div.id)
                    break

        # CRITICAL: Filter by admin level to avoid confusion between different levels
        # Use provided admin_level, or default to country's default_admin_level
        if admin_level_param:
            try:
                admin_level = int(admin_level_param)
                divisions = divisions.filter(admin_level=admin_level)
            except ValueError:
                return Response({
                    'success': False,
                    'error': f'Invalid admin_level: {admin_level_param}'
                }, status=status.HTTP_400_BAD_REQUEST)
        elif country.default_admin_level is not None:
            # Use country's default level (e.g., 4 for Canada, 3 for Benin)
            divisions = divisions.filter(admin_level=country.default_admin_level)
        # If no default level and no param, search all levels (not ideal but fallback)

        # Filter by boundary type if provided
        # Map singular English back to plural/French stored in DB
        if boundary_type_param:
            boundary_type_map = {
                'municipality': 'municipalités',
                'commune': 'communes',
                'city': 'cities',
                'town': 'towns',
                'village': 'villages',
                'arrondissement': 'arrondissements',
                'region': 'régions',
                'province': 'provinces',
                'department': 'départements',
                'prefecture': 'préfectures',
            }

            # Try mapped value first, then try direct match
            db_boundary_type = boundary_type_map.get(boundary_type_param.lower())
            if db_boundary_type:
                divisions = divisions.filter(boundary_type__iexact=db_boundary_type)
            else:
                # Try direct match as fallback
                divisions = divisions.filter(boundary_type__iexact=boundary_type_param)

        # Get the first result
        division = divisions.first()

        if not division:
            return Response({
                'success': False,
                'error': f'Division "{slug}" not found',
                'searched_name': name_from_slug,
                'boundary_type': boundary_type_param
            }, status=status.HTTP_404_NOT_FOUND)

        # Build response
        division_data = {
            'id': str(division.id),
            'name': division.name,
            'local_name': division.local_name,
            'boundary_type': division.boundary_type,
            'admin_level': division.admin_level,
            'admin_code': division.admin_code,
            'population': division.population,
            'description': division.description,
            'country': {
                'iso3': division.country.iso3,
                'name': division.country.name,
                'default_admin_level': division.country.default_admin_level
            },
            'centroid': None,
            'parent': None
        }

        # Add community_id if a community exists for this division
        try:
            from communities.models import Community
            community = Community.objects.filter(division=division, is_deleted=False).first()
            if community:
                division_data['community_id'] = str(community.id)
                division_data['community_slug'] = community.slug
        except Exception as e:
            logger.warning(f"Could not fetch community for division {division.id}: {e}")

        # Add centroid if available
        if division.centroid:
            division_data['centroid'] = {
                'lat': division.centroid.y,
                'lng': division.centroid.x
            }

        # Add parent if available
        if division.parent:
            division_data['parent'] = {
                'id': str(division.parent.id),
                'name': division.parent.name,
                'admin_level': division.parent.admin_level
            }

        return Response({
            'success': True,
            'division': division_data
        })

    except Exception as e:
        logger.error(f"Error in get_division_by_slug: {e}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
