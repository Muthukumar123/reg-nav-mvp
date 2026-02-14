# Quick Azure App Service Deployment Guide

## Your App Service Details

- **Name:** eu-regulatory-navigator
- **Region:** West Europe
- **URL:** https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net
- **Stack:** Python

## Prerequisites

Before deploying, ensure you have:

1. **Azure CLI** - [Install here](https://docs.microsoft.com/cli/azure/install-azure-cli)
2. **Docker** - [Install here](https://docs.docker.com/get-docker/)
3. **Git** - To clone/pull the repository
4. **Azure Subscription Access**

## Step-by-Step Deployment

### 1. On Your Local Machine - Clone Repository

```bash
git clone https://github.com/Muthukumar123/reg-nav-mvp.git
cd reg-nav-mvp
```

### 2. Login to Azure

```bash
az login

# Set your subscription if you have multiple
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"

# Verify you're authenticated
az account show
```

**Get your subscription ID:**
```bash
az account list --query '[].{name:name, id:id}' -o table
```

### 3. Create Azure Container Registry (ACR) - If Not Already Created

```bash
# Set variables
ACR_NAME="regunavacr"          # Must be unique globally, lowercase
RESOURCE_GROUP="eu-rg"          # Your resource group
LOCATION="westeurope"            # Your region

# Create ACR
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# List your ACRs to verify
az acr list --query '[].name' -o tsv
```

### 4. Use Automated Deployment Script

The easiest way is to use the provided deployment script:

```bash
# Make script executable
chmod +x deploy_to_azure.sh

# Run deployment
./deploy_to_azure.sh \
  "<YOUR_SUBSCRIPTION_ID>" \
  "<YOUR_RESOURCE_GROUP>" \
  "<YOUR_ACR_NAME>" \
  "eu-regulatory-navigator"

# Example:
./deploy_to_azure.sh \
  "12345678-1234-1234-1234-123456789012" \
  "eu-rg" \
  "regunavacr" \
  "eu-regulatory-navigator"
```

**What the script does:**
1. ✅ Sets Azure subscription
2. ✅ Verifies App Service exists
3. ✅ Builds Docker image
4. ✅ Authenticates with ACR
5. ✅ Pushes image to ACR
6. ✅ Configures App Service for container deployment

### 5. Configure Azure OpenAI Credentials

After deployment, set your LLM credentials in App Service:

```bash
RESOURCE_GROUP="eu-rg"
APP_SERVICE_NAME="eu-regulatory-navigator"

az webapp config appsettings set \
  --name $APP_SERVICE_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AZURE_OPENAI_KEY="your-api-key-here" \
    AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com/" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4-turbo-preview"
```

### 6. Verify Deployment

```bash
# Check App Service status
az webapp show \
  --name eu-regulatory-navigator \
  --resource-group $RESOURCE_GROUP

# View logs
az webapp log tail \
  --name eu-regulatory-navigator \
  --resource-group $RESOURCE_GROUP

# Test health endpoint
curl -X GET "https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net/health"

# Test API
curl -X POST "https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is GDPR?","top_k":3}'
```

## Manual Steps (If Script Doesn't Work)

### Build Docker Image

```bash
docker build -t regunavacr.azurecr.io/regulation-navigator:latest .
```

### Login to ACR

```bash
az acr login --name regunavacr
```

### Push to ACR

```bash
docker push regunavacr.azurecr.io/regulation-navigator:latest
```

### Configure App Service

```bash
# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name regunavacr --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name regunavacr --query "passwords[0].value" -o tsv)

# Configure container
az webapp config container set \
  --name eu-regulatory-navigator \
  --resource-group eu-rg \
  --docker-custom-image-name "regunavacr.azurecr.io/regulation-navigator:latest" \
  --docker-registry-server-url "https://regunavacr.azurecr.io" \
  --docker-registry-server-user "$ACR_USERNAME" \
  --docker-registry-server-password "$ACR_PASSWORD"

# Set port
az webapp config appsettings set \
  --name eu-regulatory-navigator \
  --resource-group eu-rg \
  --settings WEBSITES_PORT=8000
```

## Troubleshooting

### Container won't start

```bash
# View logs
az webapp log tail --name eu-regulatory-navigator --resource-group eu-rg

# SSH into container (if available)
az webapp create-remote-connection --name eu-regulatory-navigator --resource-group eu-rg
```

### Auth failed with ACR

```bash
# Verify registry credentials
az acr credential show --name regunavacr

# Re-login
az acr login --name regunavacr

# Manually set credentials
az webapp config container set \
  --name eu-regulatory-navigator \
  --resource-group eu-rg \
  --docker-registry-server-user "<USERNAME>" \
  --docker-registry-server-password "<PASSWORD>"
```

### Out of memory

```bash
# Scale up App Service Plan
az appservice plan update \
  --name "eu-regulatory-navigator-plan" \
  --resource-group "eu-rg" \
  --sku "B2"
```

### LLM timeout

```bash
# Increase timeout
az webapp config set \
  --name eu-regulatory-navigator \
  --resource-group eu-rg \
  --remote-debugging-enabled true

# Set app settings
az webapp config appsettings set \
  --name eu-regulatory-navigator \
  --resource-group eu-rg \
  --settings DEPLOYMENT_TIMEOUT=900  # 15 minutes
```

## Useful Commands

```bash
# List all resources
az resource list --resource-group eu-rg -o table

# View App Service details
az webapp show --name eu-regulatory-navigator --resource-group eu-rg

# Check App Service logs
az webapp log config --name eu-regulatory-navigator --resource-group eu-rg --web-server-logging filesystem

# Scale App Service
az appservice plan update --name <PLAN_NAME> --resource-group eu-rg --sku P1V2

# Delete deployment (cleanup)
az group delete --name eu-rg --yes --no-wait

# Get App Service logs
az webapp log download --name eu-regulatory-navigator --resource-group eu-rg --log-file logs.zip
```

## Next Steps

After deployment:

1. **Test the API**
   - Health: `https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net/health`
   - Ask: POST to `/ask` endpoint

2. **Set up monitoring**
   - Configure Application Insights
   - Set up alerts for errors

3. **Configure custom domain** (Optional)
   - Add your own domain name
   - Configure SSL certificate

4. **Enable auto-scaling** (Optional)
   - Scale based on CPU/memory
   - Handle traffic spikes

## Support

- **Azure CLI Help:** `az webapp --help`
- **Deployment Issues:** Check logs with `az webapp log tail`
- **Code Issues:** See USAGE_EXAMPLES.md for API examples
