#!/bin/bash

################################################################################
# Git Deployment to Azure App Service
# 
# This script deploys the Regulation Navigator to Azure App Service using Git
# 
# Prerequisites:
#   - Azure CLI installed (az command)
#   - Authenticated to Azure (az login)
#
# Usage:
#   ./deploy-git.sh
################################################################################

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SUBSCRIPTION_ID="b783c958-2cc8-47c3-b095-79ac49d1949b"
RESOURCE_GROUP="reg-nav-mini"
APP_SERVICE_NAME="eu-regulatory-navigator"

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}        Git Deployment to Azure App Service${NC}"
echo -e "${GREEN}        Regulation Navigator${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Set subscription
echo -e "${BLUE}[1/5]${NC} Setting Azure subscription..."
az account set --subscription "$SUBSCRIPTION_ID"
echo -e "${GREEN}✓${NC} Subscription set"
echo ""

# Step 2: Configure local Git deployment
echo -e "${BLUE}[2/5]${NC} Configuring Git deployment on App Service..."
GIT_URL=$(az webapp deployment source config-local-git \
  --name "$APP_SERVICE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query url \
  -o tsv)

if [ -z "$GIT_URL" ]; then
    echo -e "${RED}✗ Failed to get Git URL${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Git deployment configured"
echo -e "${YELLOW}  Git URL: $GIT_URL${NC}"
echo ""

# Step 3: Check if azure remote exists
echo -e "${BLUE}[3/5]${NC} Configuring Git remote..."

if git remote | grep -q "^azure$"; then
    echo -e "${YELLOW}⚠${NC} Azure remote already exists, updating..."
    git remote remove azure
fi

git remote add azure "$GIT_URL"
echo -e "${GREEN}✓${NC} Git remote 'azure' added"
echo ""

# Step 4: Verify code is committed
echo -e "${BLUE}[4/5]${NC} Checking for uncommitted changes..."
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo -e "${YELLOW}⚠${NC} Found uncommitted changes"
    echo ""
    echo -e "${YELLOW}Stage and commit your changes:${NC}"
    echo "  git add ."
    echo "  git commit -m 'Your commit message'"
    echo ""
    echo "Then run: git push azure main"
    exit 0
else
    echo -e "${GREEN}✓${NC} Working directory clean"
fi
echo ""

# Step 5: Push to Azure
echo -e "${BLUE}[5/5]${NC} Deploying to Azure App Service..."
echo -e "${YELLOW}This may take 2-5 minutes...${NC}"
echo ""

git push azure main

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Deployment started!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Your app will be available at:${NC}"
echo -e "${GREEN}  https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net${NC}"
echo ""
echo -e "${BLUE}Monitor deployment:${NC}"
echo "  az webapp log tail --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo -e "${BLUE}Test the API:${NC}"
echo "  curl https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net/health"
echo ""
