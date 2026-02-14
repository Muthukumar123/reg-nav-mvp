#!/bin/bash

################################################################################
# App Service Startup Configuration
# 
# This script sets up the Azure App Service with the correct startup command
# and environment variables for the Regulation Navigator application.
#
# Usage:
#   ./configure-appservice.sh
################################################################################

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SUBSCRIPTION_ID="b783c958-2cc8-47c3-b095-79ac49d1949b"
RESOURCE_GROUP="reg-nav-mini"
APP_SERVICE_NAME="eu-regulatory-navigator"

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}        Configure App Service${NC}"
echo -e "${GREEN}        Regulation Navigator${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Set subscription
echo -e "${BLUE}Setting subscription...${NC}"
az account set --subscription "$SUBSCRIPTION_ID"
echo -e "${GREEN}✓ Done${NC}"
echo ""

# Step 1: Set startup command
echo -e "${BLUE}[1/3] Setting startup command...${NC}"
az webapp config set \
  --name "$APP_SERVICE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --startup-file "gunicorn --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app:app"

echo -e "${GREEN}✓ Startup command configured${NC}"
echo ""

# Step 2: Set Python version
echo -e "${BLUE}[2/3] Verifying Python version...${NC}"
az webapp config set \
  --name "$APP_SERVICE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --linux-fx-version "PYTHON|3.12"

echo -e "${GREEN}✓ Python 3.12 configured${NC}"
echo ""

# Step 3: Display environment variables to set
echo -e "${BLUE}[3/3] Environment variables needed:${NC}"
echo ""
echo -e "${YELLOW}You MUST set these in Azure Portal or CLI:${NC}"
echo ""
echo "  az webapp config appsettings set \\"
echo "    --name $APP_SERVICE_NAME \\"
echo "    --resource-group $RESOURCE_GROUP \\"
echo "    --settings \\"
echo "      AZURE_OPENAI_KEY='<YOUR_AZURE_OPENAI_KEY>' \\"
echo "      AZURE_OPENAI_ENDPOINT='<YOUR_AZURE_OPENAI_ENDPOINT>' \\"
echo "      AZURE_OPENAI_DEPLOYMENT='gpt-4-turbo-preview' \\"
echo "      AUTH_ENABLED='false'"
echo ""

echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ App Service configured!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Set the environment variables shown above"
echo "2. Restart the app service: az webapp restart --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP"
echo "3. View logs: az webapp log tail --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP"
echo ""
