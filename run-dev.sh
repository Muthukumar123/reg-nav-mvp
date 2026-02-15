#!/bin/bash

################################################################################
# Run both Backend and Frontend in background
# Requires setup-dev.sh to have been run first
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}     Starting Regulation Navigator Locally${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo -e "${YELLOW}Please run: bash setup-dev.sh${NC}"
    exit 1
fi

# Activate venv
source .venv/bin/activate

# Start backend in background
echo -e "${BLUE}Starting Backend (FastAPI on port 8000)...${NC}"
python -m uvicorn app:app --reload &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
echo ""

# Wait for backend to be ready
echo -e "${YELLOW}Waiting for backend to start...${NC}"
sleep 3

# Start frontend in background
echo -e "${BLUE}Starting Frontend (Next.js on port 3000)...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo ""

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Both services running!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${BLUE}Access URLs:${NC}"
echo -e "  Frontend:  ${GREEN}http://localhost:3000${NC}"
echo -e "  Backend:   ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
echo ""

echo -e "${YELLOW}Process IDs:${NC}"
echo -e "  Backend:   ${GREEN}$BACKEND_PID${NC}"
echo -e "  Frontend:  ${GREEN}$FRONTEND_PID${NC}"
echo ""

echo -e "${YELLOW}To stop services, press Ctrl+C${NC}"
echo ""

# Wait for both processes
wait
