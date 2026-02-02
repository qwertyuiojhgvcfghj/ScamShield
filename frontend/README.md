# ScamShield Frontend

Static frontend for ScamShield Pro - AI-powered scam detection platform.

## 🚀 Deploy to Vercel

### Option 1: One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOUR_USERNAME/scamshield&root-directory=frontend)

### Option 2: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy (from frontend directory)
cd frontend
vercel

# For production deployment
vercel --prod
```

### Option 3: Deploy via GitHub Integration

1. Push this repository to GitHub
2. Go to [vercel.com](https://vercel.com) and sign in
3. Click "New Project"
4. Import your GitHub repository
5. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Other
   - **Build Command**: (leave empty)
   - **Output Directory**: `public`
6. Add Environment Variable (optional):
   - Name: `VITE_API_URL`
   - Value: Your Render backend URL (e.g., `https://scamshield-api.onrender.com`)
7. Click "Deploy"

## 📁 Project Structure

```
frontend/
├── public/
│   ├── index.html          # Landing page
│   ├── login.html          # Login page
│   ├── signup.html         # Signup page
│   ├── dashboard.html      # User dashboard
│   ├── admin.html          # Admin panel
│   ├── contact.html        # Contact page
│   ├── verify-email.html   # Email verification
│   ├── 404.html            # Not found page
│   ├── 50x.html            # Error page
│   ├── css/
│   │   ├── style.css       # Main styles
│   │   ├── home.css        # Home page styles
│   │   ├── pages.css       # Page-specific styles
│   │   ├── dashboard.css   # Dashboard styles
│   │   └── mobile.css      # Mobile responsive styles
│   ├── js/
│   │   ├── api.js          # API client
│   │   ├── auth.js         # Authentication
│   │   ├── main.js         # Main scripts
│   │   └── dashboard.js    # Dashboard scripts
│   └── assets/
│       └── favicon.svg     # Site favicon
├── vercel.json             # Vercel configuration
├── .gitignore
└── README.md
```

## 💻 Local Development

```bash
# Serve locally with Python
cd public
python -m http.server 3000

# Or with Node.js
npx serve public -l 3000
```

## ⚙️ Configuration

The frontend connects to the backend API. Update the API URL in `public/js/api.js`:

```javascript
// For local development
const API_BASE_URL = 'http://localhost:8000';

// For production (update this before deploying)
const API_BASE_URL = 'https://your-backend.onrender.com';
```

## ✨ Features

- 🛡️ AI-powered scam detection interface
- 📱 Fully responsive (mobile-first design)
- 🔐 OAuth integration (Google, GitHub)
- 📊 Real-time threat dashboard
- 🎨 Modern editorial design
- ⚡ Fast static site deployment


The frontend is served via Nginx in Docker. The `Dockerfile` copies the `public/` folder to nginx's html directory.

```bash
docker build -t scamshield-frontend .
docker run -p 80:80 scamshield-frontend
```

## API Configuration

The frontend expects the API at `/api/`. In development, configure a proxy or update `js/api.js`:

```javascript
const API_BASE_URL = 'http://localhost:8000/api/v1';
```
