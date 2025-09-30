import json
import re
from accounts.models import UserProfile

try:
    from postal.parser import parse_address
    POSTAL_AVAILABLE = True
except Exception as e:
    parse_address = None
    POSTAL_AVAILABLE = False

qs = UserProfile.objects.exclude(address__isnull=True).exclude(address='')[:200]
print('TOTAL', qs.count())
print('POSTAL_AVAILABLE', POSTAL_AVAILABLE)
modified = 0
count = 0

for p in qs:
    orig = p.address or ''
    addr = orig.strip()
    # Append ', Canada' when address does not already mention Canada
    if 'canada' not in addr.lower():
        addr2 = addr + ', Canada'
    else:
        addr2 = addr

    parsed = None
    if parse_address:
        try:
            parsed = parse_address(addr2)
        except Exception as e:
            parsed = f'ERROR: {e}'

    if addr2 != orig:
        p.address = addr2
        p.save(update_fields=['address'])
        modified += 1

    out = {
        'profile_id': str(p.id),
        'username': getattr(p.user, 'username', None),
        'orig': orig,
        'used_address': addr2,
        'parsed': parsed
    }
    print(json.dumps(out, ensure_ascii=False))
    count += 1
    if count >= 200:
        break

print('MODIFIED', modified)
