# Division Cache System

## Overview

The application now uses **localStorage** to cache division data, reducing server calls and improving page load performance when refreshing or navigating to previously visited divisions.

## How It Works

### 1. **Cache Storage**

When a user visits a division page (e.g., `/municipality/sherbrooke/accueil`), the division data is:
1. **Fetched from API** (if not in cache)
2. **Stored in localStorage** with key: `pageDivision_{COUNTRY_ISO3}_{SLUG}`
3. **Example**: `pageDivision_CAN_sherbrooke`

### 2. **Cache Retrieval**

On page load or refresh:
1. **Check localStorage first** for cached division data
2. **If found**: Display immediately (instant load)
3. **Background refresh**: Fetch fresh data silently to keep cache updated
4. **If not found**: Show loading state and fetch from server

### 3. **Cache Invalidation**

Cache entries are removed when:
- **Division not found** (404 from API)
- **Parse error** (corrupted cache data)
- **Manual cleanup** (via `geolocationService.clearDivisionCache()`)

## Benefits

✅ **Faster Page Loads**: Instant rendering from cache on refresh
✅ **Reduced Server Load**: Fewer API calls for frequently visited divisions
✅ **Better UX**: No loading spinner when returning to cached divisions
✅ **Background Updates**: Cache stays fresh with silent background refreshes

## Cache Management

### Clear All Division Caches
```javascript
import geolocationService from './services/geolocationService';

// Clear all cached divisions
geolocationService.clearDivisionCache();
```

### Clear Specific Division Cache
```javascript
// Clear cache for a specific division
geolocationService.clearSpecificDivisionCache('CAN', 'sherbrooke');
```

### Get Cache Statistics
```javascript
// Get info about cached divisions
const stats = geolocationService.getCacheStats();
console.log(`Cached divisions: ${stats.divisionCaches}`);
console.log(`Total size: ${stats.totalSize} bytes`);
console.log('Entries:', stats.entries);
```

## Migration Notes

### Old System (Removed)
- ❌ `localStorage.getItem('selectedMunicipality')`
- ❌ `localStorage.getItem('selectedMunicipalityId')`

These keys are automatically cleaned up on first app load.

### New System (Current)
- ✅ `pageDivision_{COUNTRY}_{SLUG}` - Per-division cache with full data
- ✅ Automatic cleanup on errors
- ✅ Background refresh to keep data current

## Technical Details

### Cache Key Format
```
pageDivision_{COUNTRY_ISO3}_{NORMALIZED_SLUG}
```

**Examples**:
- Canada municipality: `pageDivision_CAN_sherbrooke`
- Canada with special chars: `pageDivision_CAN_saint-denis-de-brompton`
- Benin commune: `pageDivision_BEN_ze`

### Cached Data Structure
```javascript
{
  "id": "uuid-here",
  "name": "Sherbrooke",
  "admin_level": 4,
  "boundary_type": "municipalités",
  "parent": {
    "id": "parent-uuid",
    "name": "Estrie",
    "admin_level": 2
  },
  "country": {
    "id": "country-uuid",
    "name": "Canada",
    "iso3": "CAN",
    "default_admin_level": 4
  },
  "centroid": {
    "type": "Point",
    "coordinates": [-71.8998, 45.4042]
  }
  // ... other division properties
}
```

### Cache Lifecycle

1. **First Visit**: API call → Store in cache → Render
2. **Page Refresh**: Load from cache → Render instantly → Background API call → Update cache
3. **URL Change**: Check cache for new division → Repeat cycle
4. **Error**: Remove corrupted cache → Fetch fresh data

## Best Practices

### When to Clear Cache

- **After data imports**: Clear cache when municipalities/divisions are updated in backend
- **On logout**: Optional - clear user-specific cached divisions
- **Storage limits**: If localStorage is getting full (rare)

### Cache Size Monitoring

Each cached division is typically **2-5 KB**. With hundreds of divisions cached, total storage is usually **< 1 MB**, well within localStorage limits (5-10 MB).

## Debugging

### Check What's Cached
```javascript
// In browser console
Object.keys(localStorage)
  .filter(k => k.startsWith('pageDivision_'))
  .forEach(k => console.log(k, JSON.parse(localStorage.getItem(k)).name));
```

### Clear Cache for Testing
```javascript
// Clear all division caches
localStorage.clear(); // Nuclear option
// OR
geolocationService.clearDivisionCache(); // Surgical option
```

### Monitor Cache Usage
```javascript
// See cache stats in console
const stats = geolocationService.getCacheStats();
console.table(stats.entries);
```

## Future Enhancements

Possible improvements:
- **Cache expiration**: Add timestamps and auto-expire old entries
- **Cache versioning**: Invalidate cache when app version changes
- **Compression**: Use LZ-string to compress cached JSON
- **IndexedDB**: Move to IndexedDB for larger storage capacity
- **Service Worker**: Implement offline-first with Service Worker caching

## Related Files

- `/src/pages/MunicipalityDashboard.js` - Main cache implementation
- `/src/services/geolocationService.js` - Cache management utilities
- `/src/contexts/MunicipalityContext.js` - Context (removed old localStorage usage)
