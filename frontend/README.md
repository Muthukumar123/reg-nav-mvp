# Regulation Navigator UI

A beautiful, responsive web interface for Regulation Navigator with multi-language support and dark/light theme.

## Features

✨ **Beautiful UI**
- Modern, clean design inspired by ChatGPT
- Smooth animations and transitions
- Responsive design (Mobile, Tablet, Desktop)

🌍 **Multi-Language Support**
- English (English)
- Français (French)
- Nederlands (Dutch)
- Language switcher in header

🎨 **Theme System**
- Light theme (default)
- Dark theme with toggle
- System preference detection

📱 **Responsive Design**
- Mobile-first approach
- Works on all screen sizes
- Touch-friendly buttons

🚀 **Performance**
- Fast page loads (Next.js)
- Optimized images
- Minimal bundle size

🛠️ **Developer Friendly**
- TypeScript support
- Clean component architecture
- Easy API integration

## Tech Stack

- **Framework**: Next.js 14 (React 18)
- **Styling**: Tailwind CSS + PostCSS
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Theme**: next-themes
- **Internationalization**: Custom i18n system
- **Language**: TypeScript

## Prerequisites

- Node.js 18+ or npm 9+
- Regulation Navigator API running (default: http://localhost:8000)

## Installation

### 1. Navigate to frontend directory
```bash
cd frontend
```

### 2. Install dependencies
```bash
npm install
```

### 3. Configure environment
Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production:
```env
NEXT_PUBLIC_API_URL=https://eu-regulatory-navigator-esaxgvahdsgpffgn.westeurope-01.azurewebsites.net
```

## Development

### Start development server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Build

### Production build
```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx           # Root layout with theme provider
│   ├── page.tsx             # Main chat interface
│   └── globals.css          # Global styles
├── public/
│   └── locales/
│       ├── en.json          # English translations
│       ├── fr.json          # French translations
│       └── nl.json          # Dutch translations
├── next.config.js           # Next.js configuration
├── tailwind.config.js       # Tailwind CSS configuration
├── tsconfig.json            # TypeScript configuration
├── postcss.config.js        # PostCSS configuration
├── i18n.js                  # i18n configuration
└── package.json             # Dependencies
```

## Features in Detail

### 1. Chat Interface
- User messages shown on the right (blue)
- Assistant responses on the left (gray)
- Real-time loading indicator
- Smooth scroll to latest message

### 2. Citations Display
- Shows document sources for each answer
- Displays article/section references
- Shows relevance score as percentage
- Formatted for readability

### 3. Example Questions
- Four quick-start examples
- Click to auto-fill input
- Icons for visual appeal
- Helps new users explore features

### 4. Actions
- **Copy**: Copy message to clipboard
- **Share**: Share via native share API (if available)
- **Language**: Switch between 3 languages
- **Theme**: Toggle light/dark mode

### 5. Responsive Design
```
Desktop (1024px+):
- Full width layout
- Large text and buttons
- 2 examples per row

Tablet (640px-1023px):
- Centered content
- Medium text
- 2 examples per row

Mobile (< 640px):
- Full width with padding
- Compact buttons
- 1 example per row
- Optimized spacing
```

## API Integration

The UI connects to the FastAPI backend at `/ask` endpoint:

### Request
```json
POST /ask
{
  "question": "What is GDPR?",
  "top_k": 3
}
```

### Response
```json
{
  "answer": "GDPR is...",
  "citations": [
    {
      "doc": "GDPR Regulation (EU) 2016/679",
      "section": "Article 1"
    }
  ],
  "scores": [0.89]
}
```

### Error Handling
- Network errors display user-friendly messages
- Timeout after 60 seconds
- Retry button in error state
- Graceful fallback

## Customization

### Colors
Edit `app/globals.css` CSS variables:
```css
:root {
  --primary: 221 83% 53%;          /* Primary blue */
  --background: 0 0% 100%;         /* White background */
  --foreground: 0 0% 3.6%;         /* Dark text */
  /* more colors... */
}

.dark {
  --primary: 217 100% 71%;         /* Lighter blue */
  --background: 0 0% 3.6%;         /* Dark background */
  --foreground: 0 0% 98%;          /* Light text */
  /* more colors... */
}
```

### Language Strings
Edit `public/locales/[language].json`:
```json
{
  "title": "Regulation Navigator",
  "placeholder": "Ask a question...",
  /* more translations... */
}
```

### Fonts
Add custom fonts in `app/layout.tsx`:
```tsx
import { Inter } from 'next/font/google';
const inter = Inter({ subsets: ['latin'] });
```

## Deployment

### Deploy to Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

Environment variables in Vercel dashboard:
```
NEXT_PUBLIC_API_URL=<your-azure-app-service-url>
```

### Deploy to Azure App Service
```bash
# Build
npm run build

# Deploy using Azure CLI
az webapp up --name <app-name> --resource-group <rg>
```

### Deploy to Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Performance Optimization

### Already Included
- ✅ Image optimization (next/image)
- ✅ Code splitting per route
- ✅ CSS minification
- ✅ JavaScript minification
- ✅ Font optimization

### Ready to Add
- Add caching headers: `vercel.json`
- Add CDN: Cloudflare or Vercel Edge
- Add compression: `next.config.js`

## Troubleshooting

### Blank Page
```bash
# Clear Next.js cache and reinstall
rm -rf .next node_modules
npm install
npm run dev
```

### API Connection Error
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify backend is running
- Check CORS headers in backend
- Use browser dev tools (F12 → Network tab)

### Language Not Changing
- Verify translation files exist: `public/locales/[lang].json`
- Check browser console for errors
- Ensure JSON is valid (no trailing commas)

### Theme Not Persisting
- Check browser localStorage is enabled
- Verify `next-themes` is installed
- Check for JavaScript errors in console

## License

Part of Regulation Navigator MVP - All rights reserved

## Support

For issues or questions:
1. Check this README
2. Check Next.js docs: https://nextjs.org/docs
3. Check Tailwind docs: https://tailwindcss.com/docs
4. Create an issue on GitHub

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Next Steps

### Quick Wins
- [ ] Deploy to Vercel (5 minutes)
- [ ] Add favicon/branding (10 minutes)
- [ ] Configure custom domain (15 minutes)
- [ ] Setup analytics (20 minutes)

### Enhancements
- [ ] Add conversation history (localStorage)
- [ ] Add user accounts/registration
- [ ] Add export as PDF
- [ ] Add chat sharing/embedding
- [ ] Add advanced filters
- [ ] Add usage statistics

### Enterprise Features
- [ ] SSO/OAuth integration
- [ ] Team collaboration
- [ ] Audit logging
- [ ] Custom branding
- [ ] API rate limiting
- [ ] Multi-tenant support
