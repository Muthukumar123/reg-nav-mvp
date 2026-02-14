#!/bin/bash

################################################################################
# Azure App Service Deployment Script for Regulation Navigator
# 
# This script builds the Docker image and deploys it to your Azure App Service
# 
# Prerequisites:
#   - Docker installed and running
#   - Azure CLI installed (az command)
#   - Authenticated to Azure (az login)
#   - App Service already created
#
# Usage:
#   ./deploy_to_azure.sh <subscription-id> <resource-group> <acr-name> <app-service-name>
#
# Example:
#   ./deploy_to_azure.sh "12345678-1234-1234-1234-123456789012" "my-rg" "myregistry" "eu-regulatory-navigator"
################################################################################

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SUBSCRIPTION_ID="${1:-}"
RESOURCE_GROUP="${2:-}"
ACR_NAME="${3:-}"
APP_SERVICE_NAME="${4:-eu-regulatory-navigator}"
DOCKER_IMAGE_NAME="regulation-navigator"

# Print header
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}Azure App Service Deployment - Regulation Navigator${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""

# Validate inputs
if [ -z "$SUBSCRIPTION_ID" ] || [ -z "$RESOURCE_GROUP" ] || [ -z "$ACR_NAME" ]; then
    echo -e "${RED}❌ Error: Missing required parameters${NC}"
    echo ""
    echo "Usage: $0 <subscription-id> <resource-group> <acr-name> <app-service-name>"
    echo ""
    echo "Example:"
    echo "  $0 \"12345678-1234-1234-1234-123456789012\" \"my-rg\" \"myregistry\" \"eu-regulatory-navigator\""
    echo ""
    echo "To find your values:"
    echo "  Subscription ID: az account list --query '[].id' -o tsv"
    echo "  Resource Group: az group list --query '[].name' -o tsv"
    echo "  ACR Name: az acr list --query '[].name' -o tsv"
    exit 1
fi

echo "📋 Configuration:"
echo "  Subscription ID: ${SUBSCRIPTION_ID:0:8}..."
echo "  Resource Group: $RESOURCE_GROUP"
echo "  ACR Name: $ACR_NAME"
echo "  App Service: $APP_SERVICE_NAME"
echo ""

# Step 1: Set Azure subscription
echo -e "${YELLOW}[1/6] Setting Azure subscription...${NC}"
az account set --subscription "$SUBSCRIPTION_ID"
echo -e "${GREEN}✓ Subscription set${NC}"
echo ""

# Step 2: Verify App Service exists
echo -e "${YELLOW}[2/6] Verifying App Service exists...${NC}"
APP_SERVICE_EXISTS=$(az webapp show \
  --name "$APP_SERVICE_NAME" \
  --resource-group "$RESOURCE_GROUP" 2>/dev/null || echo "")

if [ -z "$APP_SERVICE_EXISTS" ]; then
    echo -e "${RED}❌ App Service not found: $APP_SERVICE_NAME${NC}"
    echo "Available App Services in $RESOURCE_GROUP:"
    az webapp list --resource-group "$RESOURCE_GROUP" --query '[].name' -o tsv
    exit 1
fi
echo -e "${GREEN}✓ App Service found${NC}"
echo ""

# Step 3: Build Docker image
echo -e "${YELLOW}[3/6] Building Docker image...${NC}"
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}❌ Dockerfile not found in current directory${NC}"
    exit 1
fi

docker build -t "${ACR_NAME}.azurecr.io/${DOCKER_IMAGE_NAME}:latest" \
  -t "${ACR_NAME}.azurecr.io/${DOCKER_IMAGE_NAME}:$(date +%Y%m%d-%H%M%S)" .

echo -e "${GREEN}✓ Docker image built${NC}"
echo ""

# Step 4: Push to ACR
echo -e "${YELLOW}[4/6] Authenticating with Azure Container Registry...${NC}"
az acr login --name "$ACR_NAME"
echo -e "${GREEN}✓ ACR authenticated${NC}"
echo ""

echo -e "${YELLOW}[5/6] Pushing image to ACR...${NC}"
docker push "${ACR_NAME}.azurecr.io/${DOCKER_IMAGE_NAME}:latest"
echo -e "${GREEN}✓ Image pushed to ACR${NC}"
echo ""

# Step 5: Configure App Service to use container
echo -e "${YELLOW}[6/6] Configuring App Service for container deployment...${NC}"

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"

# Configure container settings
az webapp config container set \
  --name "$APP_SERVICE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --docker-custom-image-name "${ACR_LOGIN_SERVER}/${DOCKER_IMAGE_NAME}:latest" \
  --docker-registry-server-url "https://${ACR_LOGIN_SERVER}" \
  --docker-registry-server-user "$ACR_USERNAME" \
  --docker-registry-server-password "$ACR_PASSWORD"

echo -e "${GREEN}✓ App Service configured${NC}"
echo ""

# Step 6: Set WEBSITES_PORT
echo -e "${YELLOW}Setting WEBSITES_PORT environment variable...${NC}"
az webapp config appsettings set \
  --name "$APP_SERVICE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings WEBSITES_PORT=8000

echo -e "${GREEN}✓ Environment configured${NC}"
echo ""

# Done
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""
echo "Your app is being deployed. Access it at:"
echo -e "${YELLOW}https://${APP_SERVICE_NAME}.azurewebsites.net${NC}"
echo ""
echo "Health check endpoint:"
echo -e "${YELLOW}https://${APP_SERVICE_NAME}.azurewebsites.net/health${NC}"
echo ""
echo "View logs:"
echo "  az webapp log tail --name $APP_SERVICE_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "📝 Don't forget to configure Azure OpenAI credentials in App Settings:"
echo "  - AZURE_OPENAI_KEY"
echo "  - AZURE_OPENAI_ENDPOINT"
echo "  - AZURE_OPENAI_DEPLOYMENT"
echo ""
