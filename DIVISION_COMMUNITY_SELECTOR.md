# DivisionCommunitySelector Component

## Overview
The DivisionCommunitySelector component allows users to browse and select communities, optionally filtered by geographic divisions. It provides a user-friendly interface for community discovery with search capabilities.

## Purpose
- Browse all communities or filter by division
- Quick access to user's division communities
- Search communities by name or description
- Display community metadata and engagement stats
- Handle communities without divisions gracefully

## Props

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `onCommunitySelect` | function | No | Callback when community is clicked. Receives community object. Use this to integrate with other components (e.g., show ThreadList or filter SocialFeed) |
| `selectedCommunityId` | number | No | ID of currently selected community. Visually highlights the selected card with blue styling |

## Features

### 1. **Division Filtering**
- **"Toutes" Button**: Shows all communities across all divisions (🌐 GlobeAltIcon)
- **"Ma division" Button**: Shows only communities in user's division (📍 MapPinIcon)
- Active filter highlighted with colored background and border
- Automatically available when user has a division assigned

### 2. **Search Functionality**
- Real-time search across community names and descriptions
- Case-insensitive matching
- Clear visual indicator (🔍 MagnifyingGlassIcon)
- Results count updates dynamically
- Search resets when changing division filter

### 3. **Community Cards**
Each card displays:
- **Icon**: 👥 UserGroupIcon in blue
- **Name**: Community title (bold)
- **Description**: Line-clamped to 2 lines (if available)
- **Metadata**:
  - Division name with MapPinIcon (if available)
  - Member count with UserGroupIcon
  - Post count with 📝 emoji
- **Public Badge**: 🌐 Public indicator for public_access communities
- **Hover Effect**: Border turns blue, shadow increases
- **Selected State**: Blue background, blue border, blue icon/text

### 4. **State Management**
- **Loading**: Animated skeleton cards (3 placeholders)
- **Error**: Red alert box with retry button
- **Empty**: Friendly message with UserGroupIcon
- **Search No Results**: Context-aware empty message

### 5. **Scroll Support**
- Scrollable community list (max-height: 600px)
- Prevents excessive vertical growth
- Maintains header visibility while scrolling

## Usage Examples

### Basic Usage
```jsx
import DivisionCommunitySelector from '../components/social/DivisionCommunitySelector';

function CommunityBrowser() {
  const [selectedCommunity, setSelectedCommunity] = useState(null);

  return (
    <DivisionCommunitySelector
      onCommunitySelect={setSelectedCommunity}
      selectedCommunityId={selectedCommunity?.id}
    />
  );
}
```

### Integrated with ThreadList and SocialFeed
```jsx
function CommunityExplorer() {
  const [selectedCommunity, setSelectedCommunity] = useState(null);
  const [selectedThread, setSelectedThread] = useState(null);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Community Selector */}
      <div className="lg:col-span-1">
        <DivisionCommunitySelector
          onCommunitySelect={(community) => {
            setSelectedCommunity(community);
            setSelectedThread(null); // Reset thread when community changes
          }}
          selectedCommunityId={selectedCommunity?.id}
        />
      </div>

      {/* Thread List */}
      <div className="lg:col-span-1">
        {selectedCommunity && (
          <>
            <h3 className="font-bold mb-3">
              Sujets dans {selectedCommunity.name}
            </h3>
            <ThreadList
              communityId={selectedCommunity.id}
              onThreadSelect={setSelectedThread}
            />
          </>
        )}
      </div>

      {/* Feed */}
      <div className="lg:col-span-1">
        <SocialFeed
          communityId={selectedCommunity?.id}
          threadId={selectedThread?.id}
        />
      </div>
    </div>
  );
}
```

### In Sidebar Navigation
```jsx
function Sidebar() {
  const navigate = useNavigate();

  const handleCommunitySelect = (community) => {
    navigate(`/community/${community.slug}`);
  };

  return (
    <div className="w-64 bg-white border-r min-h-screen p-4">
      <DivisionCommunitySelector
        onCommunitySelect={handleCommunitySelect}
      />
    </div>
  );
}
```

### With Create Community Button
```jsx
function CommunityManager() {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedCommunity, setSelectedCommunity] = useState(null);

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Communautés</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          + Créer une communauté
        </button>
      </div>

      <DivisionCommunitySelector
        onCommunitySelect={setSelectedCommunity}
        selectedCommunityId={selectedCommunity?.id}
      />

      {showCreateModal && (
        <CreateCommunityModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={(newCommunity) => {
            setSelectedCommunity(newCommunity);
            setShowCreateModal(false);
          }}
        />
      )}
    </div>
  );
}
```

## API Integration

### Endpoints Used

#### 1. Communities List
- **Endpoint**: `GET /communities/api/communities/` or `GET /communities/api/communities/?division_id={divisionId}`
- **Method**: `socialAPI.communities.list(divisionId)`

#### 2. Divisions List (Optional)
- **Endpoint**: `GET /api/auth/divisions/`
- **Method**: `socialAPI.get('/auth/divisions/')`
- **Note**: Used for future enhancement (division dropdown). Currently, component only uses "All" vs "My Division" toggle.

### Response Format

#### Community Object
```javascript
{
  id: 1,
  name: "Tech Enthusiasts",
  description: "A community for technology lovers",
  slug: "tech-enthusiasts",
  division: 5,  // Can be null
  division_info: {  // Included if division exists
    id: 5,
    name: "Montreal",
    code: "MTL"
  },
  public_access: true,
  members_count: 234,
  posts_count: 1523,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-20T15:30:00Z"
}
```

#### API Response Structure
```javascript
{
  results: [
    { /* community object */ },
    { /* community object */ },
    // ...
  ],
  count: 10,
  next: null,
  previous: null
}
```

## State Management

### Local State
```javascript
const [communities, setCommunities] = useState([]);           // Community list
const [divisions, setDivisions] = useState([]);               // Division list (future use)
const [selectedDivisionId, setSelectedDivisionId] = useState(null);  // Active division filter
const [loading, setLoading] = useState(true);                 // Loading indicator
const [error, setError] = useState(null);                     // Error message
const [searchTerm, setSearchTerm] = useState('');            // Search input value
```

### Computed Values
```javascript
const userDivisionId = user?.profile?.division?.id;           // From AuthContext
const filteredCommunities = communities.filter(/* search */); // Search-filtered results
```

### Data Flow
1. **Mount** → Fetch divisions (optional) and communities
2. **Division Change** → Re-fetch communities with new filter, clear search
3. **Search Input** → Filter displayed communities client-side
4. **Community Click** → Call `onCommunitySelect(community)`
5. **Error** → Show error state with retry button
6. **Retry** → Re-fetch communities

## Visual States

### Division Filter Tabs
```
┌─────────────────────────────────────┐
│  [🌐 Toutes]  [📍 Ma division]      │
└─────────────────────────────────────┘
  (Blue when     (Green when selected
   selected)      - only if user has
                   division)
```

### Search Bar
```
┌─────────────────────────────────────┐
│ 🔍 Rechercher une communauté...     │
└─────────────────────────────────────┘
```

### Community Card
```
┌─────────────────────────────────────────────┐
│ 👥 Tech Enthusiasts                      → │
│    A community for technology lovers       │
│                                             │
│    📍 Montreal  👥 234 membres  📝 1523 posts│
│    🌐 Public                                │
└─────────────────────────────────────────────┘
```

### Selected Card (Blue Highlight)
```
┌═════════════════════════════════════════════┐
║ 👥 Tech Enthusiasts                      → ║
║    A community for technology lovers       ║
║                                             ║
║    📍 Montreal  👥 234 membres  📝 1523 posts║
║    🌐 Public                                ║
└═════════════════════════════════════════════┘
(Blue background, blue border, blue text)
```

### Loading Skeleton
```
┌─────────────────────────────────────┐
│ ████████████████░░░░░░░░░░░░░░░░░░ │
│ ██████████░░░░░░░░░░░░░░░░░░░░░░░░ │
└─────────────────────────────────────┘
(3 cards with pulse animation)
```

### Empty State (No Communities)
```
┌─────────────────────────────────────┐
│              👥                      │
│   Aucune communauté disponible       │
└─────────────────────────────────────┘
```

### Empty State (No Search Results)
```
┌─────────────────────────────────────┐
│              👥                      │
│  Aucune communauté ne correspond à   │
│        votre recherche               │
└─────────────────────────────────────┘
```

### Error State
```
┌─────────────────────────────────────┐
│ ⚠️ Impossible de charger les        │
│    communautés                       │
│                                      │
│         [ Réessayer ]                │
└─────────────────────────────────────┘
```

### Results Footer
```
─────────────────────────────────────────
  10 communautés trouvée(s) pour "tech"
```

## Dependencies
- `react` - Core React hooks
- `react-router-dom` - Not used directly, but available for navigation
- `@heroicons/react/24/outline` - Icons (MapPinIcon, UserGroupIcon, ChevronRightIcon, GlobeAltIcon, MagnifyingGlassIcon)
- `../../services/social-api` - API calls
- `../../contexts/AuthContext` - User information (useAuth)

## Styling
- **Framework**: Tailwind CSS
- **Colors**:
  - Blue accents for selection and hover
  - Green for "My Division" filter
  - Gray scale for neutral elements
- **Transitions**: Smooth color and shadow changes on hover
- **Responsive**: Adapts to container width, scrolls vertically when needed
- **Spacing**: Consistent padding and gaps

## Null Division Handling

### Communities Without Division
- Community cards still display normally
- `division_info` field is absent or null
- Division metadata row is conditionally hidden
- No impact on filtering or search

### Users Without Division
- "Ma division" button does NOT appear
- Only "Toutes" filter available
- Full browsing capability maintained

### "All" Filter Behavior
- Shows communities with AND without divisions
- No division_id parameter sent to API
- Backend returns all communities user can access

## Testing Checklist

### Functional Tests
- [ ] Communities load on mount
- [ ] "Toutes" filter shows all communities
- [ ] "Ma division" filter shows only user's division communities
- [ ] "Ma division" button hidden when user has no division
- [ ] Search filters communities by name
- [ ] Search filters communities by description
- [ ] Search is case-insensitive
- [ ] Search clears when changing division filter
- [ ] Community click calls `onCommunitySelect` with correct object
- [ ] Selected community highlighted with blue styling
- [ ] Loading skeleton shows during fetch
- [ ] Error state shows on API failure
- [ ] Retry button re-fetches communities
- [ ] Empty state shows when no communities exist
- [ ] Search empty state shows when no results found
- [ ] Results count updates correctly

### Visual Tests
- [ ] Division tabs styled correctly (blue/green when active)
- [ ] Search bar has proper icon alignment
- [ ] Community cards have proper spacing
- [ ] Hover effects work smoothly
- [ ] Selected state is visually distinct
- [ ] Scroll works when > 600px of content
- [ ] Skeleton cards animate with pulse
- [ ] Empty states are centered with icons
- [ ] Error state has red styling
- [ ] Results footer shows correct count

### Edge Cases
- [ ] Handle communities with null division
- [ ] Handle communities with no description
- [ ] Handle communities with 0 members
- [ ] Handle communities with 0 posts
- [ ] Handle users without division
- [ ] Handle empty search term (shows all)
- [ ] Handle search with special characters
- [ ] Handle very long community names
- [ ] Handle very long descriptions
- [ ] Handle API timeout
- [ ] Handle network errors
- [ ] Handle rapid filter changes
- [ ] Handle rapid search input changes

### Integration Tests
- [ ] Works with ThreadList component
- [ ] Works with SocialFeed component
- [ ] Works with Breadcrumb navigation
- [ ] Updates when new community created
- [ ] Re-fetches when division filter changes
- [ ] Maintains selection when re-fetching
- [ ] AuthContext user info updates reflected

## Performance Considerations

### Optimization Strategies
- Client-side search filtering (no API call per keystroke)
- useEffect dependencies prevent unnecessary re-fetches
- Division list fetched once on mount (cached)
- Community cards use key={community.id} for efficient re-renders

### Future Optimizations
- [ ] Add pagination for large community lists
- [ ] Debounce search input (if server-side search added)
- [ ] Virtual scrolling for 100+ communities
- [ ] Cache community list in context/Redux
- [ ] Prefetch community details on hover

## Integration Points

### Works With
- **ThreadList**: Select community → show threads
- **SocialFeed**: Select community → filter posts
- **Breadcrumb**: Selection updates navigation path
- **CreateCommunityModal**: New community triggers refresh
- **CommunitySettings**: Edit community updates displayed data

### Component Composition
```
DivisionCommunitySelector
  ├─ Division Filter Tabs
  │   ├─ "Toutes" button
  │   └─ "Ma division" button (conditional)
  ├─ Search Bar
  ├─ Loading State (skeleton cards)
  ├─ Error State (retry button)
  ├─ Empty State (no communities)
  └─ Community List (scrollable)
      └─ Community Card (repeating)
          ├─ Name + Icon
          ├─ Description
          ├─ Metadata (division, members, posts)
          └─ Public Badge
```

## Future Enhancements
- [ ] Advanced filters (public/private, member count range)
- [ ] Sort options (name, members, activity, created date)
- [ ] Community categories/tags
- [ ] Favorite/bookmark communities
- [ ] Recently visited communities
- [ ] Recommended communities based on user interests
- [ ] Division dropdown (instead of just "All" vs "My Division")
- [ ] Preview community on hover (tooltip with stats)
- [ ] Join/Leave community button in card
- [ ] Community admin actions (for moderators)
