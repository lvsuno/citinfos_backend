"""Accounts app tests package."""

from .base import AccountsAPITestCase
# from .test_accounts_comprehensive import (
#     AccountsAPITests,
#     AccountsTasksTests
#     # FollowSoftDeleteTest - commented out because toggle-follow action doesn't exist
#     # BlockToggleTest - commented out because toggle-block action doesn't exist
# )
from .test_api_comprehensive import AccountsComprehensiveAPITests
