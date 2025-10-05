# localStorage Audit - Current Division Storage

## Verification Date
4 octobre 2025

## Current Division Key
`currentActiveDivision`

## ✅ VERIFIED: localStorage is NEVER deleted

### Files That WRITE to localStorage
1. **MunicipalitySelector.js**
   - Line ~260: `setCurrentDivision(divisionData)` when user selects from dropdown
   - Line ~185: `setCurrentDivision(...)` when initial division is set

2. **MunicipalitiesMap.js**
   - Line ~160: `setCurrentDivision(...)` when user clicks "Visiter" on map

3. **MunicipalityDashboard.js**
   - Line ~160: `setCurrentDivision(divisionWithSlug)` when division loads from API

### Files That READ from localStorage
1. **MunicipalityContext.js**
   - Line ~66: `getCurrentDivision()` on mount to populate context
   - ✅ ONLY removes OLD keys: `selectedMunicipality`, `selectedMunicipalityId`
   - ✅ NEVER removes `currentActiveDivision`

2. **MapPage.js**
   - Line ~60-90: `getCurrentDivision()` in `getEffectiveLocation()`
   - ✅ NEVER removes anything from localStorage

3. **Sidebar.js**
   - Line ~38: `getCurrentDivision()` as fallback for display name
   - ✅ NEVER removes anything from localStorage

### Files That NEVER Touch localStorage
- **MunicipalityDashboard.js** - ✅ No removeItem or clear calls
- **MapPage.js** - ✅ No removeItem or clear calls
- **MunicipalitySelector.js** - ✅ No removeItem or clear calls
- **Sidebar.js** - ✅ No removeItem or clear calls
- **Layout.js** - ✅ No removeItem or clear calls

## When is localStorage Updated?

### ✅ ONLY When User Makes Active Selection

1. **Left Menu Dropdown Selection**
   ```javascript
   User clicks division in MunicipalitySelector
   → handleMunicipalitySelect()
   → setCurrentDivision({name: "NewDivision", country: "CAN", ...})
   → localStorage.setItem('currentActiveDivision', ...)
   ```

2. **Map "Visiter" Button**
   ```javascript
   User clicks "Visiter" on map popup
   → handleVisitDivision()
   → setCurrentDivision({name: "Division", country: "CAN", ...})
   → localStorage.setItem('currentActiveDivision', ...)
   ```

3. **Page Load from URL**
   ```javascript
   Dashboard loads division from API
   → setCurrentDivision(divisionWithSlug)
   → localStorage.setItem('currentActiveDivision', ...)
   ```

4. **Initial Page Load**
   ```javascript
   MunicipalitySelector sets initial division
   → useEffect([currentPageDivision])
   → setCurrentDivision(...)
   → localStorage.setItem('currentActiveDivision', ...)
   ```

## When is localStorage NEVER Updated?

### ❌ These Actions DO NOT Change localStorage

1. **Changing Country on Map Page**
   - Clears map dropdowns: `setSelectedLevel1(null)`, `setSelectedDefaultDivision(null)`
   - Does NOT touch localStorage
   - User's selected division remains in storage

2. **Changing Level 1 on Map Page**
   - Clears default division dropdown
   - Does NOT touch localStorage

3. **Just Browsing the Map**
   - Viewing different divisions on map
   - Zooming, panning
   - Does NOT touch localStorage

4. **Page Refresh**
   - Context reads from localStorage
   - Does NOT modify localStorage

## Cleanup Operations

### One-Time Migration Cleanup (MunicipalityContext.js)
```javascript
// Only runs ONCE on mount
const oldKeys = ['selectedMunicipality', 'selectedMunicipalityId'];
oldKeys.forEach(key => localStorage.removeItem(key));
```

### Old Per-Page Cache Cleanup (divisionStorage.js)
```javascript
// cleanupOldDivisionKeys() - removes OLD system keys
const oldKeys = ['selectedMunicipality', 'selectedMunicipalityId', 'lastVisitedDivision'];
const pageDivisionKeys = keys.filter(k => k.startsWith('pageDivision_'));
// These are removed, but 'currentActiveDivision' is NEVER removed
```

## Error Handling

### Only Removal on Parse Error
```javascript
getCurrentDivision() {
    try {
        const data = localStorage.getItem(CURRENT_DIVISION_KEY);
        return JSON.parse(data);
    } catch (error) {
        // ONLY removed if corrupted/unparseable
        localStorage.removeItem(CURRENT_DIVISION_KEY);
        return null;
    }
}
```

## Conclusion

✅ **VERIFIED**: The `currentActiveDivision` localStorage key is:
- **ONLY written** when user makes an active division selection
- **NEVER deleted** during normal operation
- **NEVER deleted** when changing country on map
- **NEVER deleted** when browsing map
- **ONLY deleted** if data is corrupted (parse error)

The system is **SAFE** - localStorage persists across:
- Page refreshes
- Navigation between pages
- Country changes on map
- All browsing activities

## Testing Checklist

- [x] Verify no `localStorage.removeItem('currentActiveDivision')` in codebase
- [x] Verify no `localStorage.clear()` affecting current division
- [x] Verify MunicipalityContext only removes OLD keys
- [x] Verify MapPage never removes localStorage
- [x] Verify MunicipalitySelector only writes (never removes)
- [x] Verify country change doesn't affect localStorage
- [x] Code audit complete ✅
