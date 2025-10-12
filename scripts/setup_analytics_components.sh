#!/bin/bash

# Analytics Components Setup Script for Docker + Yarn
# Run this from the project root

set -e  # Exit on error

echo "🚀 Setting up Visitor Analytics Components..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
echo -e "${BLUE}Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check if containers are running
echo -e "${BLUE}Checking containers...${NC}"
if ! docker-compose ps | grep -q "frontend.*Up"; then
    echo -e "${YELLOW}⚠ Frontend container is not running${NC}"
    echo -e "${BLUE}Starting frontend container...${NC}"
    docker-compose up -d frontend
    echo -e "${GREEN}✓ Frontend container started${NC}"
else
    echo -e "${GREEN}✓ Frontend container is running${NC}"
fi
echo ""

# Install Chart.js dependencies
echo -e "${BLUE}Installing Chart.js dependencies...${NC}"
docker-compose exec -T frontend yarn add chart.js react-chartjs-2
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi
echo ""

# Verify installation
echo -e "${BLUE}Verifying installation...${NC}"
if docker-compose exec -T frontend yarn list --pattern "chart.js" | grep -q "chart.js"; then
    echo -e "${GREEN}✓ chart.js installed${NC}"
else
    echo -e "${RED}❌ chart.js not found${NC}"
fi

if docker-compose exec -T frontend yarn list --pattern "react-chartjs-2" | grep -q "react-chartjs-2"; then
    echo -e "${GREEN}✓ react-chartjs-2 installed${NC}"
else
    echo -e "${RED}❌ react-chartjs-2 not found${NC}"
fi
echo ""

# Check backend is running
echo -e "${BLUE}Checking backend...${NC}"
if ! docker-compose ps | grep -q "backend.*Up"; then
    echo -e "${YELLOW}⚠ Backend container is not running${NC}"
    echo -e "${BLUE}Starting backend container...${NC}"
    docker-compose up -d backend
    echo -e "${GREEN}✓ Backend container started${NC}"
else
    echo -e "${GREEN}✓ Backend container is running${NC}"
fi
echo ""

# Test WebSocket endpoint
echo -e "${BLUE}Testing WebSocket endpoint...${NC}"
sleep 2  # Give backend time to start

if command -v wscat &> /dev/null; then
    echo -e "${BLUE}Testing WebSocket connection...${NC}"
    timeout 5 wscat -c ws://localhost:8000/ws/analytics/visitors/ 2>&1 | head -n 5 || true
else
    echo -e "${YELLOW}⚠ wscat not installed. Skipping WebSocket test.${NC}"
    echo -e "${YELLOW}  To test manually: yarn global add wscat${NC}"
    echo -e "${YELLOW}  Then: wscat -c ws://localhost:8000/ws/analytics/visitors/${NC}"
fi
echo ""

# Test API endpoint
echo -e "${BLUE}Testing API endpoint...${NC}"
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/analytics/visitors/ 2>&1 || echo "000")

if [ "$API_RESPONSE" = "401" ] || [ "$API_RESPONSE" = "403" ]; then
    echo -e "${GREEN}✓ API endpoint is accessible (requires authentication)${NC}"
elif [ "$API_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ API endpoint is accessible${NC}"
else
    echo -e "${YELLOW}⚠ API endpoint returned HTTP $API_RESPONSE${NC}"
fi
echo ""

# Component files check
echo -e "${BLUE}Checking component files...${NC}"
COMPONENTS=(
    "src/components/analytics/VisitorAnalyticsDashboard.jsx"
    "src/components/analytics/VisitorStatsCard.jsx"
    "src/components/analytics/VisitorTrendsChart.jsx"
    "src/components/analytics/DivisionBreakdown.jsx"
    "src/components/analytics/RealtimeVisitorCounter.jsx"
    "src/components/analytics/index.js"
)

ALL_EXIST=true
for component in "${COMPONENTS[@]}"; do
    if [ -f "$component" ]; then
        echo -e "${GREEN}✓ $component${NC}"
    else
        echo -e "${RED}❌ $component not found${NC}"
        ALL_EXIST=false
    fi
done
echo ""

# Service file check
echo -e "${BLUE}Checking service files...${NC}"
if [ -f "src/services/visitorAnalyticsAPI.js" ]; then
    echo -e "${GREEN}✓ src/services/visitorAnalyticsAPI.js${NC}"
else
    echo -e "${RED}❌ src/services/visitorAnalyticsAPI.js not found${NC}"
    ALL_EXIST=false
fi
echo ""

# Summary
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}          Setup Summary${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"

if [ "$ALL_EXIST" = true ]; then
    echo -e "${GREEN}✓ All component files exist${NC}"
    echo -e "${GREEN}✓ Dependencies installed${NC}"
    echo -e "${GREEN}✓ Containers are running${NC}"
    echo ""
    echo -e "${GREEN}🎉 Setup complete!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  1. Access frontend: ${YELLOW}http://localhost:3000${NC}"
    echo -e "  2. View components in your app"
    echo -e "  3. Check browser console for errors"
    echo ""
    echo -e "${BLUE}To integrate components:${NC}"
    echo -e "  import { VisitorAnalyticsDashboard } from './components/analytics';"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo -e "  - Component docs: ${YELLOW}src/components/analytics/README.md${NC}"
    echo -e "  - Docker setup: ${YELLOW}src/components/analytics/DOCKER_SETUP.md${NC}"
else
    echo -e "${RED}❌ Some component files are missing${NC}"
    echo -e "${YELLOW}Please check the file locations${NC}"
fi

echo -e "${BLUE}════════════════════════════════════════${NC}"
