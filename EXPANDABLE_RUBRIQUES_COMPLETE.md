# Expandable Rubriques - Complete Implementation

## Overview

Successfully implemented expandable/collapsible rubrique sections with proper icon mapping to Material-UI components.

## Changes Made

### 1. Backend - API Response Enhancement

**File**: `communities/models.py` - `get_rubrique_tree()` method

Added `isExpandable` field to each rubrique in the tree structure:
```python
{
    'id': 'uuid',
    'template_type': 'nouvelles',
    'name': 'Nouvelles',
    'icon': 'Newspaper',
    'color': '#6366f1',
    'depth': 0,
    'path': '002',
    'parent_id': null,
    'isExpandable': true,  # ← NEW FIELD
    'children': [...]
}
```

- `isExpandable: true` - When rubrique has children (show expand/collapse icon)
- `isExpandable: false` - When rubrique is a leaf node (no expand icon needed)

### 2. Icon Mapping - Material-UI Alignment

Updated all parent section icons to match frontend MUI imports:

| Rubrique | Old Icon | New Icon (MUI) |
|----------|----------|----------------|
| Accueil | Home | Home ✅ |
| Nouvelles | Article | **Newspaper** |
| Services | HomeRepairService | **RoomService** |
| Culture | TheaterComedy | TheaterComedy ✅ |
| Économie | TrendingUp | **Business** |
| Art | Palette | Palette ✅ |
| Sports | FitnessCenter | **Sports** |
| Distinction | Stars | **EmojiEvents** |
| Photos et Vidéos | PermMedia | **PhotoCamera** |
| Participation | HowToVote | HowToVote ✅ |

## Frontend Implementation Guide

### 1. Import Required Icons

```javascript
import {
    Home as HomeIcon,
    Newspaper as NouvellesIcon,
    RoomService as ServicesIcon,
    TheaterComedy as CultureIcon,
    Business as EconomieIcon,
    Palette as ArtIcon,
    Sports as SportsIcon,
    EmojiEvents as DistinctionIcon,
    PhotoCamera as PhotosVideosIcon,
    HowToVote as ParticipationIcon,
    ExpandMore as ExpandMoreIcon,
    ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
```

### 2. Icon Mapping Object

```javascript
const iconMap = {
    'Home': HomeIcon,
    'Newspaper': NouvellesIcon,
    'RoomService': ServicesIcon,
    'TheaterComedy': CultureIcon,
    'Business': EconomieIcon,
    'Palette': ArtIcon,
    'Sports': SportsIcon,
    'EmojiEvents': DistinctionIcon,
    'PhotoCamera': PhotosVideosIcon,
    'HowToVote': ParticipationIcon,
    // Child icons
    'FiberNew': FiberNewIcon,
    'Campaign': CampaignIcon,
    'AccountBalance': AccountBalanceIcon,
    'DirectionsBus': DirectionsBusIcon,
    'Storefront': StorefrontIcon,
    'Event': EventIcon,
    'MenuBook': MenuBookIcon,
    'AutoStories': AutoStoriesIcon,
    'HistoryEdu': HistoryEduIcon,
    'WorkOutline': WorkOutlineIcon,
    'Brush': BrushIcon,
    'Museum': MuseumIcon,
    'DirectionsRun': DirectionsRunIcon,
    'CardGiftcard': CardGiftcardIcon,
    'MilitaryTech': MilitaryTechIcon,
    'PhotoLibrary': PhotoLibraryIcon,
    'VideoLibrary': VideoLibraryIcon,
    'QuestionAnswer': QuestionAnswerIcon,
    'Lightbulb': LightbulbIcon,
    'CalendarToday': CalendarTodayIcon,
};
```

### 3. Expandable Rubrique Component

```javascript
const RubriqueItem = ({ rubrique, isExpanded, onToggle }) => {
    const IconComponent = iconMap[rubrique.icon] || HomeIcon;

    return (
        <ListItem button onClick={() => onToggle(rubrique.id)}>
            <ListItemIcon>
                <IconComponent />
            </ListItemIcon>
            <ListItemText primary={rubrique.name} />
            {rubrique.isExpandable && (
                isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />
            )}
        </ListItem>
    );
};
```

### 4. State Management

```javascript
const [expandedRubriques, setExpandedRubriques] = useState(new Set());

const toggleRubrique = (rubriqueId) => {
    setExpandedRubriques(prev => {
        const next = new Set(prev);
        if (next.has(rubriqueId)) {
            next.delete(rubriqueId);
        } else {
            next.add(rubriqueId);
        }
        return next;
    });
};
```

### 5. Rendering Tree Structure

```javascript
{rubriques.map(rubrique => (
    <div key={rubrique.id}>
        <RubriqueItem
            rubrique={rubrique}
            isExpanded={expandedRubriques.has(rubrique.id)}
            onToggle={toggleRubrique}
        />

        {/* Show children only if expandable and expanded */}
        {rubrique.isExpandable &&
         expandedRubriques.has(rubrique.id) && (
            <List component="div" disablePadding>
                {rubrique.children.map(child => (
                    <ListItem
                        key={child.id}
                        button
                        sx={{ pl: 4 }}
                        onClick={() => navigateToRubrique(child.template_type)}
                    >
                        <ListItemIcon>
                            {React.createElement(iconMap[child.icon] || HomeIcon)}
                        </ListItemIcon>
                        <ListItemText primary={child.name} />
                    </ListItem>
                ))}
            </List>
        )}
    </div>
))}
```

## API Response Structure

### Endpoint
```
GET /api/communities/{slug}/rubriques/
```

### Response Format
```json
{
    "community_id": "uuid",
    "community_name": "Sherbrooke",
    "rubriques": [
        {
            "id": "uuid",
            "template_type": "accueil",
            "name": "Accueil",
            "icon": "Home",
            "color": "#6366f1",
            "depth": 0,
            "path": "001",
            "parent_id": null,
            "isExpandable": false,
            "children": []
        },
        {
            "id": "uuid",
            "template_type": "nouvelles",
            "name": "Nouvelles",
            "icon": "Newspaper",
            "color": "#6366f1",
            "depth": 0,
            "path": "002",
            "parent_id": null,
            "isExpandable": true,
            "children": [
                {
                    "id": "uuid",
                    "template_type": "actualites",
                    "name": "Actualités",
                    "icon": "FiberNew",
                    "color": "#6366f1",
                    "depth": 1,
                    "path": "002.001",
                    "parent_id": "parent-uuid",
                    "isExpandable": false,
                    "children": []
                }
            ]
        }
    ],
    "total_enabled": 32
}
```

## Statistics

- **Total Rubriques**: 32
- **Expandable Sections**: 9 (with children)
- **Leaf Sections**: 1 (Accueil - no children)
- **Total Children**: 22

## Expandable Rubriques

1. ✅ **Nouvelles** (2 children) - Icon: Newspaper
2. ✅ **Services** (3 children) - Icon: RoomService
3. ✅ **Culture** (4 children) - Icon: TheaterComedy
4. ✅ **Économie** (2 children) - Icon: Business
5. ✅ **Art** (2 children) - Icon: Palette
6. ✅ **Sports** (2 children) - Icon: Sports
7. ✅ **Distinction** (2 children) - Icon: EmojiEvents
8. ✅ **Photos et Vidéos** (2 children) - Icon: PhotoCamera
9. ✅ **Participation Citoyenne** (3 children) - Icon: HowToVote

## Non-Expandable Rubriques

1. ✅ **Accueil** (0 children) - Icon: Home

## Testing

Run this command to verify the structure:
```bash
curl http://localhost:8000/api/communities/sherbrooke/rubriques/
```

Expected behavior:
- `isExpandable: true` for all sections with children
- `isExpandable: false` for Accueil (no children)
- All icons match MUI component names exactly
- Tree structure properly nested

## Migration Notes

**Script**: `update_rubrique_icons.py`

Updates applied:
- Article → Newspaper
- HomeRepairService → RoomService
- TrendingUp → Business
- FitnessCenter → Sports
- Stars → EmojiEvents
- PermMedia → PhotoCamera

All other icons remained unchanged as they already matched MUI names.
