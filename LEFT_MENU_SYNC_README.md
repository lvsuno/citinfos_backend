# Left Menu Division Selector - Always Synchronized

## Overview

The left menu division selector now **always stays synchronized** with the current page division across all scenarios:
- ✅ On page load/refresh
- ✅ After user login/connection
- ✅ When navigating to a different division
- ✅ When selecting a division from the map
- ✅ When choosing a neighbor from the dropdown

## How It Works

### Data Flow Priority (Top to Bottom)

1. **`currentPageDivision`** (from URL) - **HIGHEST PRIORITY**
   - Comes from `MunicipalityDashboard` via `pageDivision` state
   - Loaded from localStorage cache or API
   - Source of truth for what division is currently displayed

2. **`activeMunicipality`** (from Context) - **FALLBACK**
   - Used only when `currentPageDivision` is not available yet
   - Maintained for backward compatibility

3. **User Profile Division** - **LAST RESORT**
   - User's home division from their profile
   - Only used if no page division or active municipality

### Component Chain

```
MunicipalityDashboard (URL → pageDivision)
    ↓
Layout (passes pageDivision)
    ↓
Sidebar (receives pageDivision)
    ↓
MunicipalitySelector (currentPageDivision prop)
    ↓
Displays & fetches neighbors
```

## Changes Made

### 1. **MunicipalityDashboard.js**
- Already passing `pageDivision` to Layout ✅
- Loads division from URL on mount
- Caches in localStorage for instant reload

### 2. **Layout.js**
```javascript
// Added pageDivision prop
const Layout = ({
    activeRubrique,
    onRubriqueChange,
    municipalityName,
    pageDivision,  // NEW
    children
}) => {
    // ...

    // Pass to Sidebar
    <Sidebar
        activeRubrique={activeRubrique}
        onRubriqueChange={onRubriqueChange}
        isOpen={isSidebarOpen}
        onClose={closeSidebar}
        municipalityName={municipalityName}
        pageDivision={pageDivision}  // NEW
    />
}
```

### 3. **Sidebar.js**
```javascript
// Added pageDivision prop
const Sidebar = ({
    activeRubrique,
    onRubriqueChange,
    isOpen,
    onClose,
    municipalityName,
    pageDivision  // NEW
}) => {
    // ...

    // Pass to MunicipalitySelector
    <MunicipalitySelector currentPageDivision={pageDivision} />
}
```

### 4. **MunicipalitySelector.js**

#### Added `currentPageDivision` Prop
```javascript
const MunicipalitySelector = ({
  value = '',
  onChange = () => { },
  placeholder = '',
  error = '',
  required = false,
  className = '',
  currentPageDivision = null  // NEW: Current division from URL
}) => {
```

#### Updated Priority Logic
```javascript
// PRIORITY 1: Use currentPageDivision from props (URL-based)
// PRIORITY 2: Use activeMunicipality.id from context
// PRIORITY 3: Use user profile division
const userDivisionId = currentPageDivision?.id ||
                       activeMunicipality?.id ||
                       user?.profile?.administrative_division?.division_id ||
                       // ... other fallbacks
```

#### Updated Initial Selection
```javascript
useEffect(() => {
    // Priority 1: Use currentPageDivision from props (URL-based)
    if (currentPageDivision) {
      setSelectedMunicipality({
        id: currentPageDivision.id,
        nom: currentPageDivision.name,
        name: currentPageDivision.name,
        region: currentPageDivision.parent?.name,
        isCurrent: true,
        fromUrl: true
      });
    }
    // Priority 2: Use activeMunicipality from context
    else if (activeMunicipality && !selectedMunicipality && !userDivisionId) {
      setSelectedMunicipality(activeMunicipality);
    }
}, [currentPageDivision, selectedMunicipality, activeMunicipality, userDivisionId]);
```

#### Updated Neighbors Fetch Dependencies
```javascript
// Re-fetch neighbors when page division changes
}, [userDivisionId, activeMunicipality?.id, currentPageDivision?.id]);
```

## Behavior in Different Scenarios

### Scenario 1: User Visits URL Directly
```
1. User navigates to /municipality/sherbrooke/accueil
2. MunicipalityDashboard loads division from cache or API
3. pageDivision = { id: "...", name: "Sherbrooke", ... }
4. Passed to Layout → Sidebar → MunicipalitySelector
5. ✅ Selector shows "Sherbrooke" and its 4 neighbors
```

### Scenario 2: User Refreshes Page
```
1. User on /municipality/magog/accueil and refreshes
2. localStorage cache contains "pageDivision_CAN_magog"
3. MunicipalityDashboard loads instantly from cache
4. pageDivision = { id: "...", name: "Magog", ... }
5. ✅ Selector immediately shows "Magog" (no flash/flicker)
6. Background API refresh keeps data current
```

### Scenario 3: User Logs In
```
1. User logs in (profile has division: "Sherbrooke")
2. Redirected to /municipality/sherbrooke/accueil
3. MunicipalityDashboard fetches "Sherbrooke" division
4. pageDivision = { id: "...", name: "Sherbrooke", ... }
5. ✅ Selector shows "Sherbrooke" and neighbors
```

### Scenario 4: User Selects Division from Map
```
1. User on map page, clicks "Visit Magog"
2. MunicipalitiesMap calls switchMunicipality("Magog", id)
3. Navigates to /municipality/magog/accueil
4. MunicipalityDashboard loads "Magog" from cache/API
5. pageDivision = { id: "...", name: "Magog", ... }
6. ✅ Selector updates to show "Magog" and its neighbors
```

### Scenario 5: User Selects Neighbor from Dropdown
```
1. User on /municipality/sherbrooke/accueil
2. Opens dropdown, sees neighbors
3. Clicks "Saint-Denis-de-Brompton"
4. handleMunicipalitySelect() called
5. switchMunicipality() updates context
6. navigate() to /municipality/saint-denis-de-brompton/accueil
7. MunicipalityDashboard loads "Saint-Denis-de-Brompton"
8. ✅ Selector updates to show "Saint-Denis-de-Brompton"
```

## Benefits

✅ **No More Stale Data**: Selector always shows current page division
✅ **Instant Updates**: Changes on URL navigation, map selection, or dropdown selection
✅ **Cache Support**: Works with localStorage cache for fast loads
✅ **Backward Compatible**: Still works with old context-based logic as fallback
✅ **Proper Neighbors**: Always fetches neighbors for the current page division

## Testing Checklist

- [x] Visit /municipality/sherbrooke/accueil → Selector shows "Sherbrooke"
- [x] Refresh page → Selector immediately shows cached division
- [x] Login → Selector shows user's home division
- [x] Navigate from map → Selector updates to visited division
- [x] Select neighbor from dropdown → Selector updates to new division
- [x] Open dropdown → Shows current division + 4 closest neighbors
- [ ] Test with Benin communes (/commune/ze/accueil)
- [ ] Test on mobile (dropdown behavior)

## Future Improvements

Possible enhancements:
- Add loading indicator while pageDivision is being fetched
- Show "distance from your home" in neighbor list
- Add favorite divisions feature
- Implement division history (recently visited)
- Add search results preview before navigation

## Related Files

- `/src/pages/MunicipalityDashboard.js` - Loads pageDivision from URL
- `/src/components/Layout.js` - Passes pageDivision down
- `/src/components/Sidebar.js` - Receives and passes to selector
- `/src/components/MunicipalitySelector.js` - Uses currentPageDivision
- `/src/contexts/MunicipalityContext.js` - Manages activeMunicipality (fallback)
- `/src/services/geolocationService.js` - Caching and API calls
