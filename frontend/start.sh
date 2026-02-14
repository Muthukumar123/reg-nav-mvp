#!/bin/bash

# Quick Start Script for Regulation Navigator UI

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       Regulation Navigator - UI Quick Start              ║"
echo "║         Beautiful ChatGPT-like Interface                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found${NC}"
    echo "Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi

echo -e "${GREEN}✓ Node.js found: $(node --version)${NC}"
echo ""

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ npm found: $(npm --version)${NC}"
echo ""

# Navigate to frontend
echo -e "${BLUE}[1/4] Navigating to frontend directory...${NC}"
cd frontend || exit 1
echo -e "${GREEN}✓ Done${NC}"
echo ""

# Install dependencies
echo -e "${BLUE}[2/4] Installing dependencies...${NC}"
npm install
echo -e "${GREEN}✓ Done${NC}"
echo ""

# Show environment info
echo -e "${BLUE}[3/4] Configuration${NC}"
echo "API URL: ${YELLOW}$NEXT_PUBLIC_API_URL${NC} (default: http://localhost:8000)"
echo -e "${GREEN}✓ Ready${NC}"
echo ""

# Start development server
echo -e "${BLUE}[4/4] Starting development server...${NC}"
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Development server starting...${NC}"
echo ""
echo -e "${YELLOW}Open your browser:${NC} ${BLUE}http://localhost:3000${NC}"
echo ""
echo -e "${YELLOW}Features:${NC}"
echo "  • ChatGPT-style interface"
echo "  • 3 languages (English, French, Dutch)"
echo "  • Dark/Light theme"
echo "  • Responsive design"
echo "  • Citation tracking"
echo ""
echo -e "${YELLOW}Stop server:${NC} Press Ctrl+C"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""

npm run dev
