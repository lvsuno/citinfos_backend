# Communities App Tests Organization

The communities app tests have been successfully reorganized into a structured `tests/` folder for better maintainability and clarity.

## Test Structure

```
communities/tests/
├── __init__.py
├── test_models.py          # Model tests with JWT authentication
├── test_api.py            # API endpoint tests
├── test_comprehensive.py  # Comprehensive CRUD and task tests
└── test_tasks.py          # Celery task tests
```

## Test Categories

### 1. Model Tests (`test_models.py`)
- **CommunityModelTests**: Core model functionality tests
- **CommunityIntegrationTests**: Comprehensive model integration tests
- **CommunityModerationTests**: Moderation functionality tests
- **Authentication**: Uses JWT authentication with proper user setup

### 2. API Tests (`test_api.py`)
- **CommunityAPITestCase**: REST API endpoint tests
- Tests community CRUD operations via API
- JWT authentication for API requests

### 3. Comprehensive Tests (`test_comprehensive.py`)
- **ComprehensiveCommunitiesTestCase**: End-to-end functionality tests
- Tests all CRUD operations, analytics, and business logic
- Tests integration between models and tasks

### 4. Task Tests (`test_tasks.py`)
- **CommunityTasksTests**: Celery task functionality tests
- Tests background jobs like cleanup, analytics updates
- Tests task error handling and edge cases

## Authentication Update

All test classes have been updated to use the JWT authentication system:
- Inherits from `JWTAuthTestMixin` from `core.jwt_test_mixin`
- Proper user and profile setup in `setUp()` methods
- Consistent with the project's authentication flow

## Running Tests

```bash
# Run all communities tests
docker compose exec -T backend python manage.py test communities.tests -v 2

# Run specific test categories
docker compose exec -T backend python manage.py test communities.tests.test_models -v 2
docker compose exec -T backend python manage.py test communities.tests.test_api -v 2
docker compose exec -T backend python manage.py test communities.tests.test_comprehensive -v 2
docker compose exec -T backend python manage.py test communities.tests.test_tasks -v 2

# Run specific test methods
docker compose exec -T backend python manage.py test communities.tests.test_models.CommunityModelTests.test_only_active_members_can_interact -v 2
```

## Import Fixes Applied

- Updated all relative imports (`from .models import`) to absolute imports (`from communities.models import`)
- Fixed JWT authentication mixin import path
- Corrected task import paths in test files
- Ensured proper Django app module resolution

## Benefits of New Organization

1. **Clear Separation**: Different test types are in separate files
2. **Better Maintainability**: Easier to find and modify specific test categories
3. **Improved Readability**: Each file focuses on one aspect of testing
4. **Consistent Authentication**: All tests use the same JWT authentication pattern
5. **Django Standards**: Follows Django's recommended test organization patterns

The test reorganization maintains all existing functionality while providing a cleaner, more maintainable structure that aligns with Django best practices.
