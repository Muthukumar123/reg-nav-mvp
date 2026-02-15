#!/bin/bash

################################################################################
# Local Development Setup Script
# 
# Starts both Backend (FastAPI) and Frontend (Next.js) for local development
# Prerequisites: Python 3.10+, Node.js 18+, npm
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}     Regulation Navigator - Local Development Setup${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}[1/5] Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found: $(python3 --version)${NC}"

if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found. Please install Node.js 18+${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found: $(node --version)${NC}"

if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm not found. Please install npm${NC}"
    exit 1
fi
echo -e "${GREEN}✓ npm found: $(npm --version)${NC}"
echo ""

# Setup Backend
echo -e "${BLUE}[2/5] Setting up Backend...${NC}"

if [ -d ".venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
    source .venv/bin/activate
else
    echo -e "Creating Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

if [ -f "requirements.txt" ]; then
    echo -e "Installing Python dependencies..."
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ requirements.txt not found${NC}"
fi
echo ""

# Setup Frontend
echo -e "${BLUE}[3/5] Setting up Frontend...${NC}"

if [ -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠ Frontend node_modules already exists${NC}"
else
    echo -e "Installing frontend dependencies..."
    cd frontend
    npm install --silent
    cd ..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
fi
echo ""

# Environment Setup
echo -e "${BLUE}[4/5] Setting up environment variables...${NC}"

if [ ! -f ".env.local" ]; then
    echo -e "Creating .env.local for frontend..."
    echo 'NEXT_PUBLIC_API_URL=http://localhost:8000' > frontend/.env.local
    echo -e "${GREEN}✓ Frontend environment configured${NC}"
else
    echo -e "${GREEN}✓ Frontend environment already configured${NC}"
fi

if [ ! -f ".env" ]; then
    echo -e "Note: Create .env file with your Azure OpenAI credentials:"
    echo -e "  AZURE_OPENAI_KEY=your-key"
    echo -e "  AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/"
    echo -e "  AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo-preview"
fi
echo ""

# Final Instructions
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}To start the application, open TWO terminal windows:${NC}"
echo ""

echo -e "${BLUE}Terminal 1 - Backend (FastAPI):${NC}"
echo -e "  ${GREEN}source .venv/bin/activate${NC}"
echo -e "  ${GREEN}python -m uvicorn app:app --reload${NC}"
echo ""

echo -e "${BLUE}Terminal 2 - Frontend (Next.js):${NC}"
echo -e "  ${GREEN}cd frontend${NC}"
echo -e "  ${GREEN}npm run dev${NC}"
echo ""

echo -e "${YELLOW}Or run both in background (requires tmux/screen):${NC}"
echo -e "  ${GREEN}./run-dev.sh${NC}"
echo ""

echo -e "${BLUE}Then visit:${NC}"
echo -e "  Frontend:  ${GREEN}http://localhost:3000${NC}"
echo -e "  Backend:   ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
echo ""

echo -e "${YELLOW}Environment Setup:${NC}"
echo -e "  Backend Environment:"
echo -e "    ${GREEN}export AZURE_OPENAI_KEY=your-key${NC}"
echo -e "    ${GREEN}export AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/${NC}"
echo -e "    ${GREEN}export AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo-preview${NC}"
echo ""

echo -e "${GREEN}Ready to develop! 🚀${NC}"
