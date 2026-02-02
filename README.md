# ScamShield

<div align="center">
  <h1>🛡️ ScamShield</h1>
  <p><strong>AI-Powered Scam Detection & Prevention Platform</strong></p>
  
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
  [![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green.svg)](https://mongodb.com)
</div>

---

## 📋 Overview

ScamShield is a comprehensive AI-powered platform designed to detect and prevent scam attempts in real-time. Using advanced machine learning models and pattern recognition, it protects users from phishing, fraud, and social engineering attacks.

### Key Features

- **Real-time Scam Detection** - Analyze messages, emails, and URLs instantly
- **AI-Powered Analysis** - Leveraging Groq and Google Gemini for intelligent threat detection
- **Multi-vector Protection** - Covers phishing, fraud, impersonation, and more
- **User Dashboard** - Comprehensive threat monitoring and analytics
- **REST API** - Integrate protection into your own applications

---

## 📁 Project Structure

```
scamshield/
├── backend/                   # FastAPI Backend (Deploy to Render)
│   ├── app/
│   │   ├── api/v1/           # API routes
│   │   ├── core/             # Core configurations
│   │   ├── db/models/        # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── main.py           # Application entry
│   ├── prompts/              # AI prompts
│   ├── tests/                # Tests
│   ├── requirements.txt      # Dependencies
│   ├── render.yaml           # Render deployment config
│   └── .env.example          # Environment template
│
├── frontend/                  # Static Frontend (Deploy to Vercel)
│   ├── public/
│   │   ├── assets/           # Images, icons
│   │   ├── css/              # Stylesheets
│   │   ├── js/               # JavaScript
│   │   └── *.html            # HTML pages
│   ├── vercel.json           # Vercel deployment config
│   └── README.md             # Frontend docs
│
└── README.md                  # This file
```

---

## 🚀 Deployment

### Frontend → Vercel

1. **Push to GitHub** (if not already)

2. **Deploy to Vercel**:
   - Go to [Vercel](https://vercel.com)
   - Click "New Project"
   - Import your repository
   - Configure:
     - **Root Directory**: `frontend`
     - **Output Directory**: `public`
   - Click Deploy

3. **Update API URL**:
   - After deploying backend, update `frontend/public/js/api.js` with your Render URL

### Backend → Render

1. **Set up MongoDB Atlas**:
   - Create free cluster at [MongoDB Atlas](https://cloud.mongodb.com)
   - Get your connection string

2. **Deploy to Render**:
   - Go to [Render](https://render.com)
   - Click "New" → "Web Service"
   - Connect your repository
   - Configure:
     - **Root Directory**: `backend`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

3. **Set Environment Variables** on Render:
   ```
   MONGODB_URL=mongodb+srv://...
   SECRET_KEY=your-secret-key
   JWT_SECRET_KEY=your-jwt-secret
   GROQ_API_KEY=your-groq-key
   GOOGLE_API_KEY=your-google-key
   CORS_ORIGINS=https://your-frontend.vercel.app
   ```

---

## 💻 Local Development

### Prerequisites

- Python 3.11+
- MongoDB (local or Atlas)
- Node.js (optional, for frontend dev server)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -c "from app.db.mongodb import init_db; import asyncio; asyncio.run(init_db())"

# Run development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend/public

# Simple HTTP server
python -m http.server 3000

# Access at http://localhost:3000
```

---

## 🔌 API Documentation

Once running, access API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/login` | POST | Login user |
| `/api/v1/scans/analyze` | POST | Analyze text/URL for scams |
| `/api/v1/threats` | GET | Get threat database |
| `/api/v1/users/me` | GET | Get current user profile |

---

## ⚙️ Environment Variables

See `backend/.env.example` for all available configuration options:

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URL` | MongoDB connection string | ✅ |
| `SECRET_KEY` | App secret key | ✅ |
| `JWT_SECRET_KEY` | JWT signing key | ✅ |
| `GROQ_API_KEY` | Groq AI API key | ✅ |
| `GOOGLE_API_KEY` | Google Gemini API key | ❌ |
| `CORS_ORIGINS` | Allowed frontend URLs | ✅ |

---

## 🔒 Security Notes

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Generate secure keys** for production:
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```
3. **Update CORS origins** to only allow your frontend domain
4. **Use HTTPS** in production (Vercel and Render provide this)

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

<div align="center">
  <p>Built with ❤️ for a safer digital world</p>
</div>
