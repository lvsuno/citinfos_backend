#!/usr/bin/env python
"""Fix AnonymousSession.objects.create() calls in test_conversion_tracking.py"""

import re

# Read the file
with open('analytics/tests/test_conversion_tracking.py', 'r') as f:
    content = f.read()

# First fix: change page_url= to url=
content = content.replace('page_url=', 'url=')

# Find all AnonymousSession.objects.create() calls and check if they have required fields
lines = content.split('\n')
new_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    new_lines.append(line)

    # Check if this line contains AnonymousSession.objects.create(
    if 'AnonymousSession.objects.create(' in line:
        # Get the indentation of the next line
        j = i + 1
        create_block = []

        while j < len(lines) and not lines[j].strip().startswith(')'):
            create_block.append(lines[j])
            j += 1

        # Check if this block already has required fields
        block_text = '\n'.join(create_block)
        has_ip_address = 'ip_address=' in block_text
        has_landing_page = 'landing_page=' in block_text
        has_device_type = 'device_type=' in block_text

        # If missing any required field and has device_fingerprint
        if 'device_fingerprint=' in block_text and not (has_ip_address and has_landing_page and has_device_type):
            # Get indentation from the first parameter line
            first_param_line = create_block[0] if create_block else ''
            indent = len(first_param_line) - len(first_param_line.lstrip())
            indent_str = ' ' * indent

            # Add missing fields right after device_fingerprint line
            for k, create_line in enumerate(create_block):
                new_lines.append(create_line)
                if 'device_fingerprint=' in create_line and create_line.strip().endswith(','):
                    # Add required fields after this line
                    if not has_ip_address:
                        new_lines.append(f'{indent_str}ip_address="127.0.0.1",')
                    if not has_landing_page:
                        new_lines.append(f'{indent_str}landing_page="/",')
                    if not has_device_type:
                        new_lines.append(f'{indent_str}device_type="desktop",')

            # Skip to closing paren
            i = j
        else:
            # Just copy the block as-is
            for create_line in create_block:
                new_lines.append(create_line)
            i = j

    i += 1

# Write the fixed content
with open('analytics/tests/test_conversion_tracking.py', 'w') as f:
    f.write('\n'.join(new_lines))

print("Fixed AnonymousSession.objects.create() calls")
