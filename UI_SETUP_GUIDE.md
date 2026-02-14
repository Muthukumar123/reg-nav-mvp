# UI Setup & Deployment Guide

## Quick Start (5 Minutes)

### Prerequisites
- Node.js 18+ installed
- npm or yarn
- Backend API running (see backend deployment guide)

### Local Development

#### 1. Navigate to frontend
```bash
cd frontend
```

#### 2. Install dependencies
```bash
npm install
```

#### 3. Start development server
```bash
npm run dev
```

#### 4. Open in browser
```
http://localhost:3000
```

Done! 🎉

---

## Detailed Setup

### Environment Configuration

Create `.env.local` with:
```env
# For local development (backend on same machine)
NEXT_PUBLIC_API_URL=http://localhost:8000

# For production (use your Azure App Service URL)
NEXT_PUBLIC_API_URL=https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net
```

### Available Scripts

```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Start production server
npm start

# TypeScript type checking
npm run type-check

# Lint with ESLint
npm run lint
```

---

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx           # Root layout with theme provider
│   ├── page.tsx             # Main chat interface
│   └── globals.css          # Global styles & tailwind
├── public/
│   └── locales/             # Translation files
│       ├── en.json          # English
│       ├── fr.json          # French
│       └── nl.json          # Dutch
├── .dockerignore            # Docker build optimization
├── .env.local               # Environment variables (local)
├── .gitignore               # Git ignore rules
├── Dockerfile               # Docker build file
├── README.md                # Detailed documentation
├── i18n.js                  # i18n configuration
├── next.config.js           # Next.js configuration
├── package.json             # Dependencies
├── postcss.config.js        # PostCSS configuration
├── tailwind.config.js       # Tailwind CSS configuration
├── tsconfig.json            # TypeScript configuration
└── vercel.json              # Vercel deployment config
```

---

## Features

### 🎨 User Interface
- Modern, clean design inspired by ChatGPT
- Dark and light theme toggle
- Smooth animations and transitions
- Mobile-first responsive design

### 🌍 Multi-Language Support
- English (🇬🇧)
- Français (🇫🇷)
- Nederlands (🇳🇱)
- Language switcher in header

### 💬 Chat Features
- User messages on right (blue)
- Assistant responses on left (gray)
- Real-time loading indicator
- Auto-scroll to latest message
- Smooth typing animation

### 📚 Citations Display
- Shows document sources
- Displays article/section references
- Shows relevance percentage
- Clearly formatted and readable

### 🎯 Quick Examples
- 4 example questions
- Auto-fill on click
- Visual icons
- Helps new users explore

### ⚡ Actions
- Copy response to clipboard
- Share via native API
- Language switching
- Theme toggle

---

## Deployment Options

### Option 1: Vercel (Recommended - 5 Minutes)

**Easiest, free tier available, automatic deployments**

#### 1. Create Vercel account
```
https://vercel.com
```

#### 2. Connect GitHub repository
- Click "New Project"
- Select your GitHub repo
- Import from "reg-nav-mvp"

#### 3. Configure environment
- Set `NEXT_PUBLIC_API_URL` to your backend URL
- Example: `https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net`

#### 4. Deploy
- Click "Deploy"
- Wait 2-3 minutes
- Get live URL automatically

#### 5. Continuous deployment
- Every GitHub push = automatic deployment
- No manual work needed

**Cost:** Free tier includes up to $150/month usage

---

### Option 2: Azure App Service (10 Minutes)

**Integrated with backend, enterprise-ready**

#### 1. Create App Service for frontend
```bash
az appservice plan create \
  --name NavigatorFrontendPlan \
  --resource-group reg-nav-mini \
  --sku B1 \
  --is-linux

az webapp create \
  --resource-group reg-nav-mini \
  --plan NavigatorFrontendPlan \
  --name regulation-navigator-ui \
  --runtime "NODE|18-lts"
```

#### 2. Configure Node.js
```bash
az webapp config set \
  --resource-group reg-nav-mini \
  --name regulation-navigator-ui \
  --startup-file "npm start"
```

#### 3. Set environment variables
```bash
az webapp config appsettings set \
  --resource-group reg-nav-mini \
  --name regulation-navigator-ui \
  --settings \
    NEXT_PUBLIC_API_URL="https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net" \
    NODE_ENV="production"
```

#### 4. Deploy
```bash
# Build locally
npm run build

# Deploy to Azure
az webapp up \
  --name regulation-navigator-ui \
  --resource-group reg-nav-mini \
  --plan NavigatorFrontendPlan
```

**Cost:** ~$10-15/month (Basic tier)

---

### Option 3: Docker + Docker Hub (15 Minutes)

**Container-based, easy to manage**

#### 1. Build Docker image
```bash
docker build -t username/regulation-navigator-ui:latest .
```

#### 2. Push to Docker Hub
```bash
# Login
docker login

# Push
docker push username/regulation-navigator-ui:latest
```

#### 3. Deploy to App Service
```bash
az webapp create \
  --resource-group reg-nav-mini \
  --plan NavigatorFrontendPlan \
  --name regulation-navigator-ui \
  --deployment-container-image-name username/regulation-navigator-ui:latest

# Set environment
az webapp config appsettings set \
  --resource-group reg-nav-mini \
  --name regulation-navigator-ui \
  --settings \
    NEXT_PUBLIC_API_URL="https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net" \
    NODE_ENV="production"
```

**Cost:** Docker Hub free tier + App Service costs

---

### Option 4: Local Docker Compose (For Testing)

**Run everything locally**

```bash
# In repository root
docker-compose -f docker-compose.full.yml up -d

# Access
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# Nginx: http://localhost:80
```

---

## Production Checklist

- [ ] Environment variables set correctly
- [ ] Backend API URL configured
- [ ] Dark/light theme tested
- [ ] All 3 languages tested
- [ ] Mobile responsiveness tested
- [ ] API calls working
- [ ] Citations displaying correctly
- [ ] Animations smooth
- [ ] Error handling works
- [ ] Loading states visible
- [ ] HTTPS enabled
- [ ] Favicon/branding set

---

## Customization

### Change Theme Colors
Edit `app/globals.css`:
```css
:root {
  --primary: 221 83% 53%;        /* Main brand color */
  --background: 0 0% 100%;       /* White background */
  --foreground: 0 0% 3.6%;       /* Dark text */
}

.dark {
  --primary: 217 100% 71%;       /* Lighter blue for dark */
  --background: 0 0% 3.6%;       /* Dark background */
  --foreground: 0 0% 98%;        /* Light text */
}
```

### Add New Language
1. Create `public/locales/[code].json`
2. Copy from `en.json` and translate
3. Add to language selector in `page.tsx`

### Update Branding
1. Logo: Replace icon in header
2. Title: Change in `en.json` (all languages)
3. Description: Update `subtitle` field

---

## Performance Tips

### Already Optimized
✅ Image compression  
✅ Code splitting  
✅ CSS minification  
✅ JS minification  
✅ Font optimization  

### Add More Performance
```bash
# Enable caching
# In vercel.json, add:
"crons": [{
  "path": "/api/*",
  "schedule": "0 */6 * * *"
}]

# Add compression
# In next.config.js:
compress: true,

# Enable static generation
# Add ISR to page.tsx:
export const revalidate = 3600; // 1 hour
```

---

## Troubleshooting

### Frontend won't connect to backend
```bash
1. Check API URL in .env.local
2. Verify backend is running
3. Check browser DevTools Network tab
4. Try: curl http://localhost:8000/health
```

### Styles not applying
```bash
# Rebuild Tailwind
npm run build

# Or clear Next.js cache
rm -rf .next node_modules
npm install
npm run dev
```

### Language not switching
```bash
1. Check public/locales/[lang].json exists
2. Verify JSON is valid (no trailing commas)
3. Check browser console for errors
4. Clear browser cache
```

### Dark mode not working
```bash
# Ensure next-themes installed
npm install next-themes

# Check html class="dark" in DOM
# Verify CSS variables in globals.css
```

### Images not loading
```bash
1. Check public folder structure
2. Use relative paths like /public/image.png
3. For external images, use Next.js Image
```

---

## Performance Dashboard

### Monitor in Production

**Vercel:**
```
https://vercel.com/dashboard
→ Select project
→ Analytics tab
```

**Azure:**
```
Azure Portal
→ App Service
→ Monitoring / Application Insights
```

---

## Security Best Practices

- ✅ No secrets in environment (use .env.local)
- ✅ Validate all API responses
- ✅ Use HTTPS in production
- ✅ Set secure CSP headers
- ✅ Keep dependencies updated
- ✅ No authentication required (as requested)

---

## Next Steps

### Immediate (Today)
- [ ] npm install && npm run dev locally
- [ ] Test all 3 languages
- [ ] Test dark/light mode
- [ ] Deploy to Vercel

### Short-term (This Week)
- [ ] Add favicon/branding
- [ ] Setup custom domain
- [ ] Configure analytics
- [ ] Add conversation history (localStorage)

### Medium-term (This Month)
- [ ] Add user accounts
- [ ] Add PDF export
- [ ] Add chat sharing
- [ ] Add embedded widget

---

## Getting Help

**Documentation:**
- [Next.js Docs](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Vercel Deploy](https://vercel.com/docs)

**Community:**
- Next.js Discord: https://discord.gg/nextjs
- Tailwind Discord: https://tailwindcss.com/discord

**Issues:**
- Check browser DevTools (F12)
- Check server logs: `npm run dev` output
- Check API status: `curl http://localhost:8000/health`

---

## Summary

| Task | Time | Difficulty |
|------|------|-----------|
| Local setup | 5 min | Easy |
| Deploy to Vercel | 10 min | Easy |
| Deploy to Azure | 20 min | Medium |
| Custom domain | 15 min | Easy |
| Add branding | 30 min | Easy |
| Add features | Variable | Medium |

**Quick win:** Deploy to Vercel in 10 minutes! 🚀

---

**Your beautiful UI is ready to go!** 🎨✨
