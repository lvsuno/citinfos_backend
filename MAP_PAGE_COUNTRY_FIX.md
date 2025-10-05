# Map Page - Country Switching Fix

## Issue
When changing countries on the map page (e.g., from Benin to Canada), the old country's divisions were still appearing in the dropdown list.

**Example:** Selecting Karimama (Benin) in left menu → Navigate to map → Change country to Canada → **Karimama still appeared in municipalities dropdown**

## Root Cause
The `getDivisionsByLevel` API was being called with the wrong `closestTo` parameter:
- User had Karimama (Benin) in localStorage
- When changing to Canada, the code was passing Karimama's ID as `closestTo`
- Backend returned "10 divisions closest to Karimama" which included Karimama itself + 9 Quebec municipalities

## Solution

### 1. Simplified Division ID Logic
**Before (Complex with 3 branches):**
```javascript
if (hierarchy matches country) {
    use hierarchy.id
} else if (hierarchy exists but doesn't match) {
    use null
} else if (!hierarchy) {
    use getEffectiveLocation() // ❌ Could return wrong country
}
```

**After (Simple):**
```javascript
if (hierarchy exists AND hierarchy.country === selectedCountry) {
    use hierarchy.id
} else {
    use null  // Load alphabetically
}
```

### 2. Aggressive State Clearing on Country Change
When user changes country dropdown:
```javascript
setSelectedCountry(country);
setSelectedLevel1(null);
setDefaultLevelDivisions([]);        // Clear list
setSelectedDefaultDivision(null);    // Clear selection
setDivisionHierarchy(null);          // Clear Benin hierarchy
setMunicipalitySearchTerm('');       // Clear search
setDropdownOpen(false);              // Close dropdown to force re-render
```

### 3. Early Return for Country Mismatch
Added protection in the default divisions loading useEffect:
```javascript
if (divisionHierarchy && divisionHierarchy.country?.iso3 !== selectedCountry.iso3) {
    console.log('⚠️ Country mismatch detected');
    setDefaultLevelDivisions([]);
    setSelectedDefaultDivision(null);
    return; // Don't load - wait for hierarchy to be cleared
}
```

### 4. Search Reload Fix
When search term is cleared, use same validation:
```javascript
if (searchValue.trim().length === 0) {
    let divisionId = null;

    // Only use hierarchy if it matches current country
    if (divisionHierarchy?.id && divisionHierarchy?.country?.iso3 === selectedCountry.iso3) {
        divisionId = divisionHierarchy.id;
    }

    // Reload with correct country divisions
    const result = await geolocationService.getDivisionsByLevel(..., divisionId);
}
```

## Files Modified
- `/src/pages/MapPage.js`
  - Country onChange handler
  - Level 1 onChange handler
  - Default divisions loading useEffect
  - Search input onChange handler

## Testing Scenarios

### ✅ Scenario 1: Left Menu Division (Same Country)
1. Select Karimama (Benin) in left menu
2. Navigate to map page
3. **Expected:** Benin selected, Alibori selected, Karimama + 9 closest communes shown
4. **Result:** ✅ Works correctly

### ✅ Scenario 2: Change Country on Map
1. Start with Karimama (Benin) selected
2. Change country dropdown to Canada
3. **Expected:** Quebec selected (first level 1), first 10 municipalities alphabetically, NO Karimama
4. **Result:** ✅ Fixed - Karimama no longer appears

### ✅ Scenario 3: Search and Clear
1. On Canada/Quebec
2. Type "bla" in search → See Blanc-Sablon
3. Clear search
4. **Expected:** First 10 Quebec municipalities alphabetically
5. **Result:** ✅ Works correctly

## API Behavior

### When hierarchy matches country (Benin → Benin):
```
GET /api/auth/divisions/?country_id=benin-id&admin_level=3&parent_id=alibori-id&limit=10&closest_to=karimama-id
→ Returns: Karimama + 9 closest communes in Alibori
```

### When country changes (Benin → Canada):
```
GET /api/auth/divisions/?country_id=canada-id&admin_level=4&parent_id=quebec-id&limit=10&closest_to=null
→ Returns: First 10 Quebec municipalities alphabetically (A-Z)
```

## Key Principle
**The `closestTo` parameter should ONLY be used when the hierarchy country matches the selected country. Otherwise, load alphabetically.**

This ensures clean data separation between countries and prevents cross-country contamination in the dropdown lists.
