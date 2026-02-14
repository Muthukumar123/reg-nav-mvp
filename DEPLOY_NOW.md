# Deploy to Azure App Service NOW

Your App Service is ready: **eu-regulatory-navigator**

## Your App Service Details
- **Name**: eu-regulatory-navigator
- **Resource Group**: reg-nav-mini
- **Region**: West Europe
- **URL**: https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net
- **Runtime**: Python 3.12 (Linux)
- **Status**: Running
- **Subscription ID**: b783c958-2cc8-47c3-b095-79ac49d1949b

---

## Option 1: Deploy Using Git (Easiest - No ACR Needed)

### Step 1: Enable Git Deployment on App Service
```bash
# On your LOCAL machine
az login
az account set --subscription "b783c958-2cc8-47c3-b095-79ac49d1949b"

# Get Git deployment URL
az webapp deployment source config-local-git \
  --name eu-regulatory-navigator \
  --resource-group reg-nav-mini \
  --query url \
  -o tsv
```

### Step 2: Add Azure Remote to Git
```bash
# Result will be something like:
# https://<username>@eu-regulatory-navigator.scm.azurewebsites.net/eu-regulatory-navigator.git

# Add to your local repo
git remote add azure <PASTE_URL_FROM_ABOVE>

# Deploy
git push azure main
```

---

## Option 2: Deploy Using Docker + ACR (Recommended for Production)

### Step 1: Create/Get Azure Container Registry
```bash
# List existing ACR
az acr list --resource-group reg-nav-mini --query '[].name' -o tsv

# If none exists, create one
az acr create \
  --resource-group reg-nav-mini \
  --name regnavacr \
  --sku Basic \
  --admin-enabled true
```

### Step 2: Run Deployment Script
```bash
# On your LOCAL machine in the repo directory
chmod +x deploy_to_azure.sh

./deploy_to_azure.sh \
  "b783c958-2cc8-47c3-b095-79ac49d1949b" \
  "reg-nav-mini" \
  "regnavacr" \
  "eu-regulatory-navigator"
```

---

## Option 3: Manual Docker Deployment

### Step 1: Build Docker Image
```bash
docker build -t regulation-navigator:latest .
```

### Step 2: Login to ACR
```bash
az acr login --name regnavacr
```

### Step 3: Tag Image
```bash
docker tag regulation-navigator:latest regnavacr.azurecr.io/regulation-navigator:latest
```

### Step 4: Push to ACR
```bash
docker push regnavacr.azurecr.io/regulation-navigator:latest
```

### Step 5: Configure App Service
```bash
az webapp config container set \
  --name eu-regulatory-navigator \
  --resource-group reg-nav-mini \
  --docker-custom-image-name regnavacr.azurecr.io/regulation-navigator:latest \
  --docker-registry-server-url https://regnavacr.azurecr.io \
  --docker-registry-server-username <ACR_USERNAME> \
  --docker-registry-server-password <ACR_PASSWORD>
```

---

## Step: Set Required Environment Variables

After deployment, configure these on App Service:

```bash
az webapp config appsettings set \
  --name eu-regulatory-navigator \
  --resource-group reg-nav-mini \
  --settings \
    AZURE_OPENAI_KEY="<your-azure-openai-key>" \
    AZURE_OPENAI_ENDPOINT="<your-azure-openai-endpoint>" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4-turbo-preview" \
    AUTH_ENABLED="false"
```

Or set them manually in Azure Portal:
1. Go to **eu-regulatory-navigator** > **Configuration** > **Application settings**
2. Add the variables above
3. Click **Save**

---

## Verify Deployment

### Check Health Endpoint
```bash
curl https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net/health
```

### Test API
```bash
curl -X POST https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is AML?","top_k":3}'
```

### View Logs
```bash
az webapp log tail \
  --name eu-regulatory-navigator \
  --resource-group reg-nav-mini
```

---

## Troubleshooting

### App Service won't start
```bash
# Check logs
az webapp log tail --name eu-regulatory-navigator --resource-group reg-nav-mini

# Restart
az webapp restart --name eu-regulatory-navigator --resource-group reg-nav-mini
```

### Container not found
```bash
# Verify ACR image
az acr repository list --name regnavacr
az acr repository show-tags --name regnavacr --repository regulation-navigator
```

### Authentication errors
```bash
# Regenerate credentials
az acr credential renew --name regnavacr --password-name password
```

---

## Which Option to Use?

| Option | Best For | Speed | Setup |
|--------|----------|-------|-------|
| **Git** | Quick testing | ⚡ Fast | ✅ Easiest |
| **Docker + ACR** | Production | 🚀 Optimal | 📋 Standard |
| **Manual** | Learning | 🐢 Slow | 🔧 Complex |

**Recommendation**: Use **Option 1 (Git)** for immediate deployment, then **Option 2 (Docker + ACR)** for production.

---

## Ready to Deploy?

Choose an option above and run the commands on your **LOCAL machine** where you have Azure CLI installed.

Need help? 👉 Ask me to help with any specific step!
