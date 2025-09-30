#!/bin/sh
set -e
echo "Waiting for Elasticsearch..."
until curl -s http://elasticsearch:9200 >/dev/null; do sleep 2; done

curl -X PUT "http://elasticsearch:9200/canada-addresses-2025.07.29" -H 'Content-Type: application/json' -d '{
  "mappings": {
    "properties": {
      "location": { "type": "geo_point" },
      "city": { "type": "text" },
      "full_addr": { "type": "text" },
      "pruid": { "type": "integer" },
      "postal_code": { "type": "text" }
    }
  }
}'