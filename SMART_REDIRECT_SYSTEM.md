# Smart Redirect System - Documentation

## Overview

The smart redirect system provides intelligent navigation after login based on user session activity. It balances user convenience with session continuity.

## How It Works

### Three-Tier Decision Logic

When a user logs in, the system determines where to redirect them using this priority:

1. **Recent Session (< 30 minutes since logout)**
   - Redirects user back to the last visited page
   - Provides session continuity for quick re-logins
   - Example: User was on Magog → Logged out → Logs back in within 30 min → Returns to Magog

2. **Old Session (> 30 minutes since logout)**
   - Redirects user to their home division
   - Provides fresh start for long-away users
   - Example: User was on Magog → Logged out → Logs back in after 2 hours → Goes to Sherbrooke (home)

3. **From Login/Register Pages**
   - Always redirects to user's home division
   - Predictable behavior for fresh logins
   - Example: User navigates to /login → Logs in → Goes to Sherbrooke (home)

## Implementation

### Files Modified

#### 1. `/src/utils/navigationTracker.js` (NEW)
Main tracking utility with functions:

- `trackPageVisit(url, divisionData)` - Tracks when user visits a division page
- `trackLogout()` - Records logout timestamp
- `getSmartRedirectUrl(userHomeDivisionUrl)` - Calculates smart redirect decision
- `getLastVisitedDivision()` - Retrieves last visited division data
- `shouldRedirectFromUrl(currentUrl)` - Checks if current URL should trigger redirect

#### 2. `/src/contexts/AuthContext.js`
Updated `logout()` function to call `trackLogout()`:
```javascript
const logout = async () => {
    try {
        setLoading(true);
        console.log('🚪 Starting logout process...');

        // Track logout time for smart redirect
        trackLogout();

        await apiService.logout();
        // ... rest of logout logic
    }
};
```

#### 3. `/src/pages/LoginPage.js`
Updated login redirect logic:
```javascript
const userHomeUrl = getUserRedirectUrl(result.user);
const { url: redirectUrl, reason } = getSmartRedirectUrl(userHomeUrl);
console.log('🎯 Smart redirect decision:', { redirectUrl, reason });
// Navigate to redirectUrl...
```

#### 4. `/src/pages/MunicipalityDashboard.js`
Added import for `trackPageVisit` (tracking calls to be added when division loads)

## Configuration

### Session Timeout

Default timeout is **30 minutes** - can be changed in `navigationTracker.js`:

```javascript
const SESSION_TIMEOUT_MINUTES = 30; // Change this value
```

### LocalStorage Keys

The system uses these localStorage keys:
- `lastVisitedUrl` - Last page URL
- `lastVisitedTime` - Timestamp of last visit
- `logoutTime` - Timestamp when user logged out
- `lastVisitedDivision` - Division data (id, name, slug, country)

## Usage Examples

### Scenario 1: Quick Re-login
```
User Activity:
1. Browsing /municipality/magog/accueil
2. Logs out (trackLogout() called)
3. Waits 5 minutes
4. Logs back in

Result: Redirected to /municipality/magog/accueil
Reason: "Recent session (5.0 min ago) - continuing"
```

### Scenario 2: Long Session Break
```
User Activity:
1. Browsing /municipality/magog/accueil
2. Logs out (trackLogout() called)
3. Waits 2 hours
4. Logs back in

Result: Redirected to /municipality/sherbrooke/accueil (home)
Reason: "Old session (120.0 min ago) - going home"
```

### Scenario 3: Fresh Login
```
User Activity:
1. Navigates to /login
2. Logs in

Result: Redirected to /municipality/sherbrooke/accueil (home)
Reason: "No previous visit data - going to home division"
```

## Testing Guide

### Test Cases

1. **Recent Session Test**
   - Navigate to a division (not your home)
   - Logout
   - Wait < 30 minutes
   - Login
   - **Expected**: Return to that division

2. **Old Session Test**
   - Navigate to a division (not your home)
   - Logout
   - Wait > 30 minutes (or manually change logoutTime in localStorage)
   - Login
   - **Expected**: Go to your home division

3. **Fresh Login Test**
   - Navigate directly to /login
   - Login
   - **Expected**: Go to your home division

4. **Logout Tracking Test**
   - Login
   - Open browser console
   - Logout
   - **Expected**: See "🚪 Logout tracked: [timestamp]" in console

5. **Page Visit Tracking Test**
   - Login
   - Navigate to different divisions
   - Check browser console
   - **Expected**: See "📍 Navigation tracked: {url, time}" for each visit

### Manual Testing with Browser DevTools

Check localStorage tracking data:
```javascript
// Open browser console
console.log({
    lastVisitedUrl: localStorage.getItem('lastVisitedUrl'),
    lastVisitedTime: new Date(parseInt(localStorage.getItem('lastVisitedTime'))),
    logoutTime: new Date(parseInt(localStorage.getItem('logoutTime'))),
    lastVisitedDivision: JSON.parse(localStorage.getItem('lastVisitedDivision'))
});
```

Manually force old session:
```javascript
// Set logout time to 2 hours ago
const twoHoursAgo = Date.now() - (2 * 60 * 60 * 1000);
localStorage.setItem('logoutTime', twoHoursAgo.toString());
```

## Debugging

### Enable Debug Logging

The system already logs all decisions. Look for these console messages:

- `📍 Navigation tracked:` - Page visit tracked
- `🚪 Logout tracked:` - Logout event tracked
- `🧭 Smart redirect calculation:` - Redirect decision details
- `🎯 Smart redirect decision:` - Final redirect with reason

### Common Issues

**Issue**: Always redirecting to home even for recent sessions
- **Check**: Logout time is being tracked correctly
- **Fix**: Ensure `trackLogout()` is called in logout function

**Issue**: Not tracking page visits
- **Check**: `trackPageVisit()` is called when division loads
- **Fix**: Add tracking call in MunicipalityDashboard useEffect

**Issue**: Redirect URL is invalid
- **Check**: `getUserRedirectUrl()` returns valid URL
- **Fix**: Ensure user has location data in profile

## Future Enhancements

Possible improvements:
- Make timeout configurable per user
- Add user preference for redirect behavior
- Track multiple recent divisions (breadcrumb trail)
- Add analytics for redirect decisions
- Persist across devices (backend storage)

## API Reference

### `trackPageVisit(url, divisionData)`
Records current page visit for redirect tracking.

**Parameters:**
- `url` (string): Current pathname (e.g., '/municipality/sherbrooke/accueil')
- `divisionData` (object): Division info `{id, name, slug, country}`

**Example:**
```javascript
trackPageVisit(location.pathname, {
    id: 'uuid-here',
    name: 'Sherbrooke',
    slug: 'sherbrooke',
    country: 'CAN'
});
```

### `trackLogout()`
Records logout timestamp.

**Parameters:** None

**Example:**
```javascript
trackLogout(); // Call in logout function
```

### `getSmartRedirectUrl(userHomeDivisionUrl)`
Calculates where to redirect user based on session activity.

**Parameters:**
- `userHomeDivisionUrl` (string): User's home division URL

**Returns:**
```javascript
{
    url: string,     // Where to redirect
    reason: string   // Why this decision was made
}
```

**Example:**
```javascript
const { url, reason } = getSmartRedirectUrl('/municipality/sherbrooke/accueil');
console.log(`Redirecting to ${url} because: ${reason}`);
navigate(url);
```

### `getLastVisitedDivision()`
Retrieves last visited division data.

**Returns:** Division object or null

**Example:**
```javascript
const lastDiv = getLastVisitedDivision();
if (lastDiv) {
    console.log(`Last visited: ${lastDiv.name}`);
}
```

### `shouldRedirectFromUrl(currentUrl)`
Checks if current URL should trigger redirect.

**Parameters:**
- `currentUrl` (string): Current pathname

**Returns:** boolean

**Example:**
```javascript
if (shouldRedirectFromUrl(location.pathname)) {
    // User is on login/register page, redirect after login
}
```

## Maintenance

### Updating Timeout Duration

Change in `/src/utils/navigationTracker.js`:
```javascript
const SESSION_TIMEOUT_MINUTES = 45; // Changed from 30 to 45 minutes
```

### Adding New Redirect Pages

Update `shouldRedirectFromUrl()` function:
```javascript
const redirectPages = ['/', '/login', '/register', '/signup', '/welcome']; // Add new pages
```

### Clearing Old Data

To reset all tracking data:
```javascript
import { clearAllNavigationTracking } from '../utils/navigationTracker';
clearAllNavigationTracking();
```

---

**Version:** 1.0
**Last Updated:** 5 octobre 2025
**Author:** Development Team
