# Single Division Storage Architecture

## Overview

The application now uses a **single source of truth** for the current active division across ALL pages. This ensures consistency and eliminates the need for per-page storage.

## Core Principle

**The dropdown selection in the left menu is THE defining action for which division is currently active.**

When a division is selected (either programmatically or by user action), it's immediately stored in localStorage with a single key: `currentActiveDivision`

## Storage Key

```javascript
localStorage key: 'currentActiveDivision'

Structure:
{
  id: "uuid-string",
  name: "Sherbrooke",
  slug: "sherbrooke",
  country: "CAN",
  parent: { id: "...", name: "Estrie" },
  boundary_type: "municipalités",
  admin_level: 4,
  level_1_id: "...",
  timestamp: 1696435200000
}
```

## When Division is Stored

### 1. **User Selects from Dropdown** (MunicipalitySelector)
```javascript
handleMunicipalitySelect(municipality) {
  // Store immediately when user clicks
  setCurrentDivision({
    id: municipality.id,
    name: municipality.name,
    slug: getMunicipalitySlug(municipality.name),
    country: countryCode,
    ...
  });

  // Then navigate
  navigate(`/municipality/${slug}`);
}
```

### 2. **Initial Page Load** (MunicipalitySelector useEffect)
```javascript
useEffect(() => {
  if (currentPageDivision) {
    setSelectedMunicipality(currentPageDivision);

    // Store in localStorage
    setCurrentDivision({
      id: currentPageDivision.id,
      name: currentPageDivision.name,
      ...
    });
  }
}, [currentPageDivision]);
```

### 3. **Map Page "Visiter" Button** (MunicipalitiesMap)
```javascript
handleVisitDivision() {
  // Store before navigation
  setCurrentDivision({
    id: selectedMunicipality.id,
    name: selectedMunicipality.name,
    slug: divisionSlug,
    ...
  });

  // Then navigate
  navigate(`/${typeSlug}/${divisionSlug}`);
}
```

### 4. **API Fetch on Dashboard** (MunicipalityDashboard)
```javascript
// When fetching fresh data from API
const result = await geolocationService.getDivisionBySlug(slug, country);
setCurrentDivision(result.division);
```

## Data Flow

### Scenario 1: User Logs In
```
1. Login → Redirect to user's home division URL (/municipality/sherbrooke)
2. MunicipalityDashboard loads → checks localStorage
3. If not found → fetch from API → store in localStorage
4. MunicipalitySelector displays → also stores in localStorage (redundant but ensures sync)
5. ✅ Result: Sherbrooke stored in 'currentActiveDivision'
```

### Scenario 2: User Selects Different Division
```
1. User opens dropdown → sees current division + neighbors
2. User clicks "Magog"
3. MunicipalitySelector.handleSelect → IMMEDIATELY stores Magog in localStorage
4. Navigate to /municipality/magog
5. MunicipalityDashboard loads → finds Magog in localStorage → no API call needed
6. ✅ Result: Instant page load, Magog is current division
```

### Scenario 3: User on Map Page, Refreshes
```
1. User is on /carte-municipalites (no division in URL)
2. MapPage.getEffectiveLocation() → checks localStorage
3. Finds 'currentActiveDivision' = Magog
4. Uses Magog's ID to load map data
5. ✅ Result: Map shows Magog area, not user's original location
```

### Scenario 4: User Clicks "Visiter" on Map
```
1. User clicks marker on map → popup shows "Visiter Sherbrooke"
2. MunicipalitiesMap.handleVisit → stores Sherbrooke in localStorage
3. Navigate to /municipality/sherbrooke
4. MunicipalityDashboard → finds Sherbrooke in localStorage → instant load
5. ✅ Result: Sherbrooke becomes current division
```

## Priority Order for Division Loading

### MunicipalityDashboard (has URL slug)
```
1. Check localStorage for 'currentActiveDivision'
   - Match slug and country
   - If found → use immediately (no API call)

2. If not found or mismatch
   - Fetch from API using slug
   - Store result in localStorage

3. Never use user profile location (that's only for initial redirect)
```

### MapPage (no URL slug)
```
1. Check activeMunicipality from context (just selected)
2. Check localStorage for 'currentActiveDivision'
3. Check user profile location
4. Check anonymous location
5. Fallback to country default
```

### MunicipalitySelector (dropdown)
```
1. Use currentPageDivision prop (from MunicipalityDashboard)
2. Use activeMunicipality from context
3. Use user profile location (for initial load only)
```

## Utility Functions

### divisionStorage.js
```javascript
// Single source of truth management
getCurrentDivision()      // Read from localStorage
setCurrentDivision(div)   // Write to localStorage
clearCurrentDivision()    // Clear localStorage
cleanupOldDivisionKeys()  // Remove old per-page caches
```

## Migration & Cleanup

The system automatically cleans up old localStorage keys:
- `selectedMunicipality` → removed
- `selectedMunicipalityId` → removed
- `pageDivision_*` → removed (all per-page caches)
- `lastVisitedDivision` → removed

This happens on:
1. MunicipalityDashboard mount
2. First call to cleanupOldDivisionKeys()

## Benefits

✅ **Single Source of Truth**: One key, one location, no conflicts
✅ **Instant Page Loads**: No API calls when division already loaded
✅ **Persistent Across Pages**: Map page knows current division
✅ **Simple Logic**: Dropdown selection = storage update
✅ **No Stale Data**: Every selection immediately updates storage
✅ **Clean Architecture**: No complex synchronization needed

## Files Modified

1. `/src/utils/divisionStorage.js` - NEW: Storage utilities
2. `/src/pages/MunicipalityDashboard.js` - Check localStorage first
3. `/src/pages/MapPage.js` - Use getCurrentDivision()
4. `/src/components/MunicipalitySelector.js` - Store on selection + initial load
5. `/src/components/MunicipalitiesMap.js` - Store on "Visiter" click

## Testing Checklist

- [ ] Login → division stored in localStorage
- [ ] Select different division → immediately stored, instant navigation
- [ ] Refresh page → division loaded from localStorage (no API call)
- [ ] Visit map page → shows current division's area
- [ ] Refresh map page → still shows current division
- [ ] Click "Visiter" on map → stores new division
- [ ] Dropdown always shows current division
- [ ] Old localStorage keys cleaned up on first load

## Future Enhancements

- Add expiry time to localStorage (e.g., 24 hours)
- Add version number to detect schema changes
- Sync across browser tabs using storage events
- Cache multiple recent divisions for faster switching
