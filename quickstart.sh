#!/bin/bash

# Quick Start Script for Citinfos Backend
# Minimal setup for development

set -e

echo "🚀 Citinfos Backend Quick Start"
echo "================================"

# Check Docker
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "🔨 Building backend..."
docker compose build backend

echo "🌐 Starting all services..."
docker compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 20

echo "📊 Running migrations..."
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate

echo "👤 Creating admin user..."
docker compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
"

echo "🌍 Setting up countries..."
docker compose exec backend python manage.py setup_country --name "Benin" --code "BEN" --capital "Porto-Novo" --continent "Africa"
docker compose exec backend python manage.py setup_country --name "Canada" --code "CAN" --capital "Ottawa" --continent "North America"

echo "✅ Quick start complete!"
echo ""
echo "🌐 Backend:      http://localhost:8000"
echo "👥 Admin:        http://localhost:8000/admin (admin/admin)"
echo "🌍 Frontend:     http://localhost:3000"
echo "📊 Flower:       http://localhost:5555"
echo "🔧 Redis:        http://localhost:8081 (admin/admin)"
echo "🔍 Elasticsearch: http://localhost:9200"
echo "🔗 Autocomplete: http://localhost:4000"
echo ""
echo "To load geographic data, run:"
echo "  docker compose exec backend python manage.py load_geo_data --auto-detect /app/shapefiles/[your_data]/"
echo ""
echo "All services are running. Use 'docker compose logs -f [service]' to view logs."