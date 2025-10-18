# Account Verification Flow

## Overview
Users must reverify their account every 7 days. When verification expires, they can still browse but cannot post, comment, or interact until they reverify.

## Implementation

### Backend (Middleware Check)
**File**: `accounts/middleware.py` - `UpdateLastActiveMiddleware`

- **Checks verification** on EVERY authenticated request (all HTTP methods)
- **For write operations** (POST, PUT, PATCH, DELETE): Returns 403 error immediately
- **For read operations** (GET, HEAD, OPTIONS): Adds warning header but allows request
- **Syncs verification status** from `last_verified_at` timestamp
- **Returns 403 error** for write operations when verification required:
  ```json
  {
    "detail": "Verification required",
    "error_code": "VERIFICATION_EXPIRED",
    "message": "Your account verification has expired. Please verify your account to continue.",
    "requires_verification": true
  }
  ```
- **Returns response headers** for read operations when verification required:
  ```
  X-Verification-Required: true
  X-Verification-Message: Your account verification has expired. Please verify your account to continue.
  ```

### Frontend (API Interceptor)
**File**: `src/services/apiService.js`

**Response Interceptor** checks EVERY response for verification headers:

**Success Response Handler**:
```javascript
(response) => {
  // Check for verification required header on ALL responses
  const verificationRequired = response.headers['x-verification-required'];
  const verificationMessage = response.headers['x-verification-message'];

  if (verificationRequired === 'true') {
    // Dispatch custom event for verification modal
    window.dispatchEvent(new CustomEvent('verificationRequired', {
      detail: {
        message: verificationMessage || 'Your account verification has expired.',
        errorCode: 'VERIFICATION_EXPIRED'
      }
    }));
  }

  return response;
}
```

**Error Response Handler** (for write operations):
```javascript
if (error.response?.status === 403) {
  const errorData = error.response?.data || {};

  if (errorData.error_code === 'VERIFICATION_EXPIRED' || errorData.requires_verification) {
    // Dispatch custom event for verification modal
    window.dispatchEvent(new CustomEvent('verificationRequired', {
      detail: {
        message: errorData.message,
        errorCode: errorData.error_code
      }
    }));
  }
}
```

### Global Verification Modal
**File**: `src/App.js`

**AuthContext State**:
- `showVerificationModal`: Controls modal visibility
- `verificationMessage`: Message to display in modal
- `setShowVerificationModal`: Function to close modal

**Event Listener** in `AuthContext`:
```javascript
const handleVerificationRequired = (event) => {
  const { message } = event.detail || {};
  setVerificationMessage(message || 'Your account verification has expired.');
  setShowVerificationModal(true);
};

window.addEventListener('verificationRequired', handleVerificationRequired);
```

**Modal Component** in `App.js`:
```javascript
{showVerificationModal && user && (
  <VerifyAccount
    show={showVerificationModal}
    onHide={() => setShowVerificationModal(false)}
    onSuccess={handleVerificationSuccess}
    userEmail={user.email}
    message={verificationMessage}
  />
)}
```

## User Flow

### 1. Session Recovery / Active Session
- User visits site with valid session cookie OR active login
- Frontend recovers session via fingerprint OR user is already logged in
- User is authenticated with potentially expired verification

### 2. Immediate Verification Detection
- User makes ANY authenticated request (even just loading a page)
- Middleware checks `profile.is_verified` (synced from `last_verified_at`)
- Verification is expired (>7 days since last verification)
- **For read requests**: Middleware adds `X-Verification-Required: true` header
- **For write requests**: Middleware returns 403 with `VERIFICATION_EXPIRED`

### 3. Modal Display (Immediate on Page Load)
- API interceptor checks response headers on ALL requests
- Detects `X-Verification-Required: true` header
- Dispatches `verificationRequired` custom event
- AuthContext listener catches event
- Sets `showVerificationModal = true`
- Global modal appears immediately, even if just browsing

### 4. Verification Process
- User enters verification code from email/SMS
- `VerifyAccount` component submits code
- Backend validates and updates `last_verified_at`
- `is_verified` becomes `true` again
- Modal closes via `onSuccess` callback

### 5. Continue Activity
- User can now browse AND interact without restrictions
- No page refresh or redirect needed
- Verification check happens on every request but modal only shows once

## Benefits

✅ **Immediate notification** - Modal appears on first request, not when trying to interact
✅ **No redirects** - Modal appears in place
✅ **No polling** - Check happens on every authenticated request
✅ **No extra endpoints** - Middleware handles everything
✅ **Seamless UX** - User knows immediately they need to verify
✅ **Secure** - Write operations blocked until verified
✅ **Read access maintained** - Can still browse while modal is shown
✅ **Modal shows once** - Event listener ensures modal appears once per session

## Settings

**Verification Valid Period**: 7 days (configurable in `settings.py`)
```python
VERIFICATION_VALID_DAYS = 7
```

## Testing

1. **Expire a user's verification**:
   ```python
   from accounts.models import UserProfile
   from django.utils import timezone
   from datetime import timedelta

   profile = UserProfile.objects.get(user__username='elvist')
   profile.last_verified_at = timezone.now() - timedelta(days=8)
   profile.save()
   ```

2. **Try to create a post** - Modal should appear
3. **Enter verification code** - Modal closes, post succeeds
4. **Check verification updated**:
   ```python
   profile.refresh_from_db()
   print(profile.last_verified_at)  # Should be recent
   print(profile.is_verified)  # Should be True
   ```

## Database Fields

**UserProfile Model**:
- `last_verified_at` (DateTimeField, nullable): Last verification timestamp
- `is_verified` (BooleanField): Computed from `last_verified_at` (7-day window)
- `sync_verification_status()`: Method to update `is_verified` from `last_verified_at`

## API Endpoints (No Changes Needed)

The verification flow doesn't require any new endpoints:
- Login already checks and returns verification status
- Middleware blocks actions when expired
- Existing verify endpoints handle the verification
- Modal uses existing `VerifyAccount` component

## Future Enhancements

- [ ] Configurable verification period per user role
- [ ] Grace period warnings (e.g., "expires in 1 day")
- [ ] Alternative verification methods (biometric, 2FA)
- [ ] Verification reminder notifications
