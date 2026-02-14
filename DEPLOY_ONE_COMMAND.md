# One-Command Deploy Guide

Everything is ready in GitHub. **Run this ONE command on your LOCAL machine:**

```bash
# Copy and paste this entire command in your terminal:
curl -fsSL https://raw.githubusercontent.com/Muthukumar123/reg-nav-mvp/main/deploy-git.sh | bash -s -- && \
curl -fsSL https://raw.githubusercontent.com/Muthukumar123/reg-nav-mvp/main/configure-appservice.sh | bash -s --
```

---

## What This Does:

1. ✅ Downloads and runs the deployment script from GitHub
2. ✅ Configures Git deployment to your App Service
3. ✅ Pushes code to Azure
4. ✅ Configures the App Service startup settings

---

## Prerequisites (Must Have on Your Local Machine):

```bash
# Check you have these:
az --version          # Azure CLI
git --version         # Git
```

## Setup Steps on Your Local Machine:

### **1. Login to Azure**
```bash
az login
# Browser will open - sign in with your Azure account
```

### **2. Copy and Run the Deploy Script**
```bash
curl -fsSL https://raw.githubusercontent.com/Muthukumar123/reg-nav-mvp/main/deploy-git.sh | bash -s -- && \
curl -fsSL https://raw.githubusercontent.com/Muthukumar123/reg-nav-mvp/main/configure-appservice.sh | bash -s --
```

### **3. Set Environment Variables**
```bash
az webapp config appsettings set \
  --name eu-regulatory-navigator \
  --resource-group reg-nav-mini \
  --settings \
    AZURE_OPENAI_KEY="<YOUR_KEY>" \
    AZURE_OPENAI_ENDPOINT="<YOUR_ENDPOINT>" \
    AZURE_OPENAI_DEPLOYMENT="gpt-4-turbo-preview" \
    AUTH_ENABLED="false"
```

### **4. Wait 2-5 Minutes for Deployment**

### **5. Test**
```bash
# Check if it's running
curl https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net/health

# View live logs
az webapp log tail --name eu-regulatory-navigator --resource-group reg-nav-mini
```

---

## Full Manual Alternative:

If the curl method doesn't work, do this manually on your local machine:

```bash
# 1. Clone repo
git clone https://github.com/Muthukumar123/reg-nav-mvp.git
cd reg-nav-mvp

# 2. Login
az login
az account set --subscription "b783c958-2cc8-47c3-b095-79ac49d1949b"

# 3. Configure Git deployment
az webapp deployment source config-local-git \
  --name eu-regulatory-navigator \
  --resource-group reg-nav-mini

# 4. Add Azure remote (use the URL from step 3)
git remote add azure https://<USERNAME>@eu-regulatory-navigator.scm.azurewebsites.net/eu-regulatory-navigator.git

# 5. Deploy
git push azure main

# 6. Configure App Service
chmod +x configure-appservice.sh
./configure-appservice.sh

# 7. Set env vars (see step 3 above)
```

---

## What's Deployed:

- ✅ **Code**: Latest from GitHub main branch
- ✅ **Runtime**: Python 3.12 on Linux
- ✅ **Startup**: Gunicorn + Uvicorn
- ✅ **URL**: https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net

---

## Troubleshooting

**"az: command not found"**
- Install Azure CLI: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli

**"Permission denied"** 
- Make scripts executable: `chmod +x deploy-git.sh configure-appservice.sh`

**Deployment stuck**
- Check logs: `az webapp log tail --name eu-regulatory-navigator --resource-group reg-nav-mini`

**Still need help?**
- Ask me! I can guide through any specific step.

---

## Ready to Deploy?

**Open your terminal on your local machine and run:** 🚀

```bash
az login
```

Then I'll help with the next step!
