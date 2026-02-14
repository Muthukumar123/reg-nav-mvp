# Azure App Service Configuration for Regulation Navigator MVP

## Deployment Steps

### 1. Prerequisites
- Azure CLI installed (`az` command)
- Azure subscription with permissions to create resources
- Git repository pushed to GitHub or Azure Repos
- Docker image built and pushed to Azure Container Registry (ACR)

### 2. Create Azure Resources

```bash
# Set variables
RESOURCE_GROUP="regnav-rg"
LOCATION="eastus2"
REGISTRY_NAME="regnav"
APP_NAME="regnav-mvp"
APP_PLAN="regnav-asp"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create Azure Container Registry
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $REGISTRY_NAME \
  --sku Basic \
  --admin-enabled true

# Get registry login credentials
az acr credential show \
  --name $REGISTRY_NAME \
  --query "[username, passwords[0].value]"
```

### 3. Build and Push Docker Image

```bash
# Login to ACR
az acr login --name $REGISTRY_NAME

# Build image
docker build -t $REGISTRY_NAME.azurecr.io/regulation-navigator:latest .

# Push to ACR
docker push $REGISTRY_NAME.azurecr.io/regulation-navigator:latest

# View images in registry
az acr repository show-tags \
  --name $REGISTRY_NAME \
  --repository regulation-navigator
```

### 4. Create App Service Plan

```bash
# Create App Service Plan (Linux, Basic tier sufficient for MVP)
az appservice plan create \
  --name $APP_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1 \
  --number-of-workers 1

# View available SKUs
az appservice plan list-skus --is-linux
```

### 5. Create Web App with Container

```bash
# Create web app
az webapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_PLAN \
  --deployment-container-image-name-user \
  --deployment-container-image-name "$REGISTRY_NAME.azurecr.io/regulation-navigator:latest"

# Configure container settings
az webapp config container set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name "$REGISTRY_NAME.azurecr.io/regulation-navigator:latest" \
  --docker-registry-server-url "https://$REGISTRY_NAME.azurecr.io" \
  --docker-registry-server-user <USERNAME> \
  --docker-registry-server-password <PASSWORD>

# Enable continuous deployment (webhook)
az webapp deployment container config \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --enable-cd true
```

### 6. Configure Environment Variables

```bash
# Set application settings
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AZURE_OPENAI_KEY="<your-key>" \
    AZURE_OPENAI_ENDPOINT="<your-endpoint>" \
    AZURE_OPENAI_DEPLOYMENT="<your-deployment>" \
    WEBSITES_PORT=8000
```

### 7. Configure Startup Command

```bash
# Set startup command
az webapp config set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --startup-file "gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app:app"
```

### 8. Enable Application Insights (Optional)

```bash
# Create Application Insights
az monitor app-insights component create \
  --app $APP_NAME \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --kind web \
  --application-type web

# Get instrumentation key
az monitor app-insights component show \
  --app $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query instrumentationKey
```

### 9. Configure Scaling (Optional)

```bash
# Create autoscale settings
az monitor metrics alert create \
  --name "CPU-High" \
  --resource-group $RESOURCE_GROUP \
  --scopes "/subscriptions/<SUB_ID>/resourcegroups/$RESOURCE_GROUP/providers/microsoft.web/serverfarms/$APP_PLAN" \
  --condition "avg Percentage CPU > 80 since 5m" \
  --window-size 5m \
  --evaluation-frequency 1m
```

## Monitoring and Management

### View Logs
```bash
# Stream logs from web app
az webapp log tail \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP

# Download logs
az webapp log download \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --log-file logs.zip
```

### Health Check
```bash
# Test health endpoint
APP_URL="https://${APP_NAME}.azurewebsites.net"
curl -X GET "${APP_URL}/health"
```

### Update Deployment
```bash
# Rebuild and push new image
docker build -t $REGISTRY_NAME.azurecr.io/regulation-navigator:v2 .
docker push $REGISTRY_NAME.azurecr.io/regulation-navigator:v2

# Update app to use new image
az webapp config container set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name "$REGISTRY_NAME.azurecr.io/regulation-navigator:v2"
```

## Cost Optimization

### Recommended SKU Progression
1. **Development:** B1 ($13/month Linux)
2. **Staging:** B2 ($33/month Linux)  
3. **Production:** P1V2 ($100+/month)

### Scaling Tiers
- **B1:** 1 GB RAM, 1.6 compute units
- **B2:** 1.75 GB RAM, 3.5 compute units
- **P1V2:** 3.5 GB RAM, 100 compute units

## Security Best Practices

### 1. Enable HTTPS
```bash
# Add managed certificate
az webapp config ssl bind \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --certificate-name <CERT_NAME>
```

### 2. Restrict Access
```bash
# Add access restrictions
az webapp config access-restriction add \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --rule-name "AllowInternalVPN" \
  --action Allow \
  --ip-address <IP_RANGE>/24
```

### 3. Manage Secrets
```bash
# Use Key Vault for sensitive data
az keyvault create \
  --name "regnav-kv" \
  --resource-group $RESOURCE_GROUP

# Add secrets
az keyvault secret set \
  --vault-name "regnav-kv" \
  --name "azure-openai-key" \
  --value "<API_KEY>"

# Reference in app settings
az webapp config appsettings set \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings AZURE_OPENAI_KEY="@Microsoft.KeyVault(SecretUri=https://regnav-kv.vault.azure.net/secrets/azure-openai-key/)"
```

## Cleanup

```bash
# Delete all resources
az group delete \
  --name $RESOURCE_GROUP \
  --yes --no-wait
```

## Quick Deploy Script

```bash
#!/bin/bash
# deploy.sh - One-command deployment to Azure AppService

set -e

RESOURCE_GROUP="regnav-rg"
LOCATION="eastus2"
REGISTRY_NAME="regnav"
APP_NAME="regnav-mvp"
APP_PLAN="regnav-asp"

echo "Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

echo "Creating container registry..."
az acr create --resource-group $RESOURCE_GROUP --name $REGISTRY_NAME --sku Basic --admin-enabled true

echo "Building and pushing Docker image..."
az acr build --registry $REGISTRY_NAME --image regulation-navigator:latest .

echo "Creating App Service Plan..."
az appservice plan create --name $APP_PLAN --resource-group $RESOURCE_GROUP --is-linux --sku B1

echo "Creating Web App..."
az webapp create --name $APP_NAME --resource-group $RESOURCE_GROUP --plan $APP_PLAN \
  --deployment-container-image-name-user \
  --deployment-container-image-name "$REGISTRY_NAME.azurecr.io/regulation-navigator:latest"

echo "Configuring container..."
REGISTRY_USER=$(az acr credential show --name $REGISTRY_NAME --query username -o tsv)
REGISTRY_PASS=$(az acr credential show --name $REGISTRY_NAME --query passwords[0].value -o tsv)

az webapp config container set --name $APP_NAME --resource-group $RESOURCE_GROUP \
  --docker-custom-image-name "$REGISTRY_NAME.azurecr.io/regulation-navigator:latest" \
  --docker-registry-server-url "https://$REGISTRY_NAME.azurecr.io" \
  --docker-registry-server-user "$REGISTRY_USER" \
  --docker-registry-server-password "$REGISTRY_PASS"

echo "Setting environment variables..."
az webapp config appsettings set --name $APP_NAME --resource-group $RESOURCE_GROUP \
  --settings \
    AZURE_OPENAI_KEY="$AZURE_OPENAI_KEY" \
    AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
    AZURE_OPENAI_DEPLOYMENT="$AZURE_OPENAI_DEPLOYMENT" \
    WEBSITES_PORT=8000

echo "Deployment complete!"
echo "Web App URL: https://${APP_NAME}.azurewebsites.net"
echo "Health Check: https://${APP_NAME}.azurewebsites.net/health"
```

## Troubleshooting

### Container won't start
```bash
# Check logs
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP

# SSH into container
az webapp create-remote-connection --name $APP_NAME --resource-group $RESOURCE_GROUP
```

### Out of memory
- Scale up to higher SKU (B2, P1V2)
- Check CHUNKS size in app.py
- Consider using database instead of in-memory storage

### LLM API timeout
- Increase timeout in llm.py
- Implement retry logic
- Consider using faster model variant

### High latency
- Use Azure AppService cache layer
- Enable Redis caching
- Optimize TF-IDF parameters (reduce vocabulary)
