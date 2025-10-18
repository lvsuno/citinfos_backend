# Résolution du Problème CORS - x-device-fingerprint

## Le Problème

Le client envoyait l'en-tête personnalisé `x-device-fingerprint` dans les requêtes, mais cet en-tête n'était pas autorisé par la configuration CORS du serveur.

### Erreur CORS

```
Blocage d'une requête multiorigine (Cross-Origin Request) :
la politique « Same Origin » ne permet pas de consulter la ressource distante
située sur http://localhost:8000/api/auth/user-info/.
Raison : l'en-tête « x-device-fingerprint » n'est pas autorisé d'après
l'en-tête « Access-Control-Allow-Headers » de la réponse de pré-vérification
des requêtes CORS.
```

### Endpoints Affectés

- `/api/auth/user-info/`
- `/api/auth/location-data/`
- `/api/auth/division-neighbors/`
- `/api/auth/countries/`
- Tous les endpoints recevant `x-device-fingerprint`

## La Solution

### 1. Ajout de `x-device-fingerprint` aux Headers Autorisés

**Fichier:** `citinfos_backend/settings.py`

```python
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-session-id',  # Custom session ID header
    'x-device-fingerprint',  # ✅ AJOUTÉ - Device fingerprint header
    'x-new-access-token',  # Token renewal header
    'x-new-refresh-token',  # Refresh token header
]
```

### 2. Ajout aux Headers Exposés (pour les réponses)

```python
CORS_EXPOSE_HEADERS = [
    'x-new-access-token',
    'x-new-refresh-token',
    'x-session-id',
    'x-device-fingerprint',  # ✅ AJOUTÉ - Device fingerprint header
]
```

## Pourquoi CORS Bloque les En-têtes Personnalisés?

### Les Requêtes CORS Préalables (Preflight)

Quand un client envoie une requête avec des en-têtes personnalisés, le navigateur envoie d'abord une requête `OPTIONS` (preflight) pour vérifier si le serveur autorise:

1. **L'origine** (domaine du client)
2. **Les méthodes HTTP** (GET, POST, etc.)
3. **Les en-têtes personnalisés** (x-device-fingerprint, etc.)

### Le Flow CORS

```
┌──────────────┐                           ┌──────────────┐
│   CLIENT     │                           │   SERVEUR    │
│ localhost:   │                           │ localhost:   │
│    3000      │                           │    8000      │
└──────────────┘                           └──────────────┘
      │                                            │
      │  1. OPTIONS /api/auth/user-info/          │
      │     Headers: x-device-fingerprint         │
      ├──────────────────────────────────────────>│
      │                                            │
      │  2. Vérification CORS                      │
      │     - Origin autorisé?                     │
      │     - Header x-device-fingerprint OK?      │
      │                                            │
      │  ❌ AVANT (Header non autorisé)            │
      │  Access-Control-Allow-Headers:             │
      │  authorization, content-type, ...          │
      │  (x-device-fingerprint manquant!)          │
      │<──────────────────────────────────────────┤
      │  ❌ CORS Error! Request blocked            │
      │                                            │
      │                                            │
      │  ✅ APRÈS (Header autorisé)                │
      │  Access-Control-Allow-Headers:             │
      │  authorization, x-device-fingerprint, ...  │
      │<──────────────────────────────────────────┤
      │  ✅ Preflight OK                           │
      │                                            │
      │  3. GET /api/auth/user-info/               │
      │     Headers: x-device-fingerprint          │
      ├──────────────────────────────────────────>│
      │                                            │
      │  4. Response avec données                  │
      │<──────────────────────────────────────────┤
      │  ✅ Success!                               │
      │                                            │
```

## Headers CORS Complets

### Headers Envoyés par le Client (Request)

Ces headers doivent être dans `CORS_ALLOW_HEADERS`:

- `authorization` - JWT token
- `content-type` - Type de contenu (application/json)
- `x-device-fingerprint` - ✅ Empreinte de l'appareil
- `x-session-id` - ID de session
- `x-requested-with` - XMLHttpRequest

### Headers Renvoyés par le Serveur (Response)

Ces headers doivent être dans `CORS_EXPOSE_HEADERS` pour être accessibles par JS:

- `x-new-access-token` - Nouveau token d'accès
- `x-new-refresh-token` - Nouveau refresh token
- `x-session-id` - ID de session
- `x-device-fingerprint` - ✅ Empreinte générée par le serveur

## Vérification

### Tester la Configuration CORS

```bash
# Tester la requête OPTIONS (preflight)
curl -X OPTIONS http://localhost:8000/api/auth/user-info/ \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: x-device-fingerprint, authorization" \
  -v

# Vérifier la réponse:
# < Access-Control-Allow-Headers: accept, accept-encoding, authorization, content-type, ..., x-device-fingerprint, ...
# < Access-Control-Allow-Origin: http://localhost:3000
# < Access-Control-Allow-Methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
```

### Vérifier dans le Navigateur

1. Ouvrir les DevTools (F12)
2. Onglet Network
3. Filtrer par "Fetch/XHR"
4. Chercher la requête OPTIONS (preflight)
5. Vérifier les headers de réponse:
   - `Access-Control-Allow-Headers` doit contenir `x-device-fingerprint`
   - `Access-Control-Allow-Origin` doit être `http://localhost:3000`

## Configuration Complète CORS

```python
# citinfos_backend/settings.py

# Origines autorisées
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Create React App dev server
    "http://127.0.0.1:3000",
    "http://localhost:8000",  # Backend Django server
    "http://127.0.0.1:8000",
]

# Permettre les credentials (cookies, authorization headers)
CORS_ALLOW_CREDENTIALS = True

# Headers que le client peut envoyer
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-session-id',
    'x-device-fingerprint',  # ✅ Essentiel pour le tracking
    'x-new-access-token',
    'x-new-refresh-token',
]

# Méthodes HTTP autorisées
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Headers que le client peut lire dans la réponse
CORS_EXPOSE_HEADERS = [
    'x-new-access-token',
    'x-new-refresh-token',
    'x-session-id',
    'x-device-fingerprint',  # ✅ Si le serveur le renvoie
]

# CSRF - Origines de confiance
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
```

## Middleware CORS

Django utilise `django-cors-headers` qui doit être dans `INSTALLED_APPS` et `MIDDLEWARE`:

```python
INSTALLED_APPS = [
    ...
    'corsheaders',
    ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # ✅ Doit être en premier
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    ...
]
```

## Cas d'Usage de x-device-fingerprint

### Client → Serveur (Request)

Le client peut envoyer le fingerprint qu'il a reçu précédemment:

```javascript
// Client-side (React/Axios)
axios.get('/api/auth/user-info/', {
    headers: {
        'x-device-fingerprint': localStorage.getItem('fingerprint'),
        'Authorization': `Bearer ${token}`
    }
});
```

### Serveur → Client (Response)

Le serveur génère le fingerprint et le renvoie:

```python
# Server-side (Django)
from core.device_fingerprint import OptimizedDeviceFingerprint

fingerprint = OptimizedDeviceFingerprint.get_fast_fingerprint(request)

response = Response({...})
response['x-device-fingerprint'] = fingerprint
return response
```

## Redémarrage Nécessaire

Après avoir modifié `settings.py`, il faut redémarrer le backend:

```bash
docker compose restart backend
```

## Points Importants

### ✅ À Faire

1. **Ajouter tous les headers personnalisés** à `CORS_ALLOW_HEADERS`
2. **Exposer les headers de réponse** via `CORS_EXPOSE_HEADERS`
3. **Placer CorsMiddleware en premier** dans `MIDDLEWARE`
4. **Redémarrer le serveur** après modification

### ❌ À Éviter

1. **N'utilisez pas `CORS_ALLOW_ALL_ORIGINS = True`** en production (risque de sécurité)
2. **Ne pas oublier de headers** - chaque header personnalisé doit être déclaré
3. **Ne pas confondre** `ALLOW_HEADERS` (requête) et `EXPOSE_HEADERS` (réponse)

## Résumé

Le problème CORS était causé par l'absence de `x-device-fingerprint` dans la liste des headers autorisés. L'ajout de cet header dans `CORS_ALLOW_HEADERS` et `CORS_EXPOSE_HEADERS` a résolu le problème.

**Fichier modifié:** `citinfos_backend/settings.py`
**Ligne ajoutée:** `'x-device-fingerprint',` dans les deux listes de headers
**Redémarrage:** `docker compose restart backend`

Les requêtes du client vers le backend fonctionnent maintenant correctement! ✅
