# ScamShield Backend

FastAPI backend for ScamShield Pro - AI-powered scam detection platform.

## 🚀 Deploy to Render

### Option 1: One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR_USERNAME/scamshield)

### Option 2: Manual Deployment

1. Go to [render.com](https://render.com) and sign in
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `scamshield-api`
   - **Root Directory**: `backend`
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
5. Add Environment Variables (see below)
6. Click "Create Web Service"

### Option 3: Using render.yaml

The `render.yaml` file is included for Infrastructure as Code deployment.

## ⚙️ Environment Variables

Set these in Render Dashboard → Environment:

```env
# Required
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/scamshield
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_REFRESH_SECRET_KEY=another-secret-key-min-32-chars

# AI Providers (at least one required)
GROQ_API_KEY=gsk_xxxxx
GEMINI_API_KEY=AIzaSyxxxxx

# OAuth (optional but recommended)
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
GITHUB_CLIENT_ID=Ov23lixxxxx
GITHUB_CLIENT_SECRET=xxxxx

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=ScamShield <noreply@scamshield.com>

# Frontend URL for CORS
FRONTEND_URL=https://your-frontend.vercel.app

# Environment
ENVIRONMENT=production
DEBUG=false
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/v1/           # API endpoints
│   │   ├── auth.py       # Authentication
│   │   ├── users.py      # User management
│   │   ├── scans.py      # Scan endpoints
│   │   ├── threats.py    # Threat management
│   │   ├── analytics.py  # Analytics
│   │   ├── admin.py      # Admin endpoints
│   │   └── router.py     # Route aggregation
│   ├── core/
│   │   ├── config.py     # Configuration
│   │   ├── security.py   # Security utils
│   │   └── dependencies.py
│   ├── db/
│   │   ├── mongodb.py    # MongoDB connection
│   │   └── models/       # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── main.py           # App entry point
├── prompts/
│   └── agent_prompt.txt  # AI prompts
├── tests/
│   └── test_api.py       # API tests
├── requirements.txt      # Dependencies
├── render.yaml           # Render configuration
├── Dockerfile            # Docker build
└── .env.example          # Environment template
```

## 💻 Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your values

# Initialize database
python -m app.init_db

# Run server
uvicorn app.main:app --reload --port 8000
```

## 🐳 Docker

```bash
# Build
docker build -t scamshield-api .

# Run
docker run -p 8000:8000 --env-file .env scamshield-api
```

## 📡 API Endpoints

### Health Check
- `GET /api/v1/health` - Check API status

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/google` - Google OAuth
- `GET /api/v1/auth/github` - GitHub OAuth

### Users
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update profile
- `POST /api/v1/users/me/api-key` - Generate API key

### Scans
- `POST /api/v1/scans/scan` - Analyze text for scams
- `GET /api/v1/scans/history` - Get scan history

### Threats
- `GET /api/v1/threats` - List threats
- `POST /api/v1/threats/report` - Report a threat

### Analytics
- `GET /api/v1/analytics/stats` - Get statistics
- `GET /api/v1/analytics/dashboard` - Dashboard data

## 🧪 Testing

```bash
pytest -v
pytest --cov=app  # With coverage
```

## 📄 API Documentation

When running locally, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

