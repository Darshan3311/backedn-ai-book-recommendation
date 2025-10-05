# 📚 AI Book Recommendations API - Backend

A complete, production-ready FastAPI backend that provides AI-powered book recommendations using Google Gemini AI, with secure user authentication and MongoDB integration.

## 🚀 Render Deployment Guide

### Prerequisites
- MongoDB Atlas database (configured)
- Google Gemini API key (configured)
- Render account

### Environment Variables for Render
Set these in your Render service:

```
MONGO_CONNECTION_STRING=mongodb+srv://bookRecom:bookRecommend@cluster0.kpm1vpd.mongodb.net/book_recommendations?retryWrites=true&w=majority
JWT_SECRET_KEY=a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
GEMINI_API_KEY=AIzaSyDETxPeZEOBkk9pvwbvXSk5T5JiAkDVLIM
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Deployment Steps
1. Create new **Web Service** on Render
2. Connect your GitHub repository (backend folder)
3. Set service configuration:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Python Version**: 3.11.0
4. Add environment variables from above
5. Deploy!

## ✨ Features Complete

- ✅ **FastAPI Framework** - Modern, fast web framework with automatic API documentation
- ✅ **JWT Authentication** - Secure user registration and login with bcrypt password hashing
- ✅ **MongoDB Integration** - User data stored securely with Beanie ODM
- ✅ **Google Gemini Integration** - AI-powered book recommendations using Gemini Pro
- ✅ **CORS Support** - Configured for frontend integration
- ✅ **Error Handling** - Comprehensive error management throughout
- ✅ **Input Validation** - Pydantic schemas for request/response validation
- ✅ **API Documentation** - Auto-generated interactive docs

## 🏗️ Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI application & CORS setup
│   ├── config.py            # Settings management with environment variables
│   ├── database.py          # MongoDB connection initialization
│   ├── models.py            # Beanie Document models (User)
│   ├── schemas.py           # Pydantic API schemas
│   ├── security.py          # Password hashing & JWT utilities
│   └── routers/
│       ├── auth.py          # Authentication endpoints
│       └── recommendations.py # AI book recommendations
├── requirements.txt         # Python dependencies
├── .env                     # Environment configuration
├── run.py                   # Development server runner
└── test_api.py              # Comprehensive API testing
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Edit `.env` file:
```env
MONGO_CONNECTION_STRING=mongodb+srv://user:pass@cluster.mongodb.net/book_recommendations?retryWrites=true&w=majority
JWT_SECRET_KEY=your_secure_jwt_secret_key_here
OPENAI_API_KEY=your_openai_api_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Generate JWT secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Start Server
```bash
python run.py
```

Server starts at: `http://localhost:8000`

## 📖 API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 🔧 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user (OAuth2 form)

### Book Recommendations (Protected)
- `POST /recommendations/` - Get AI book recommendations

### System
- `GET /` - Welcome message
- `GET /health` - Health check

## 🧪 Testing

Run comprehensive API tests:
```bash
python test_api.py
```

Tests cover:
- ✅ Root endpoint
- ✅ Health check
- ✅ User registration
- ✅ User login
- ✅ Protected recommendations endpoint
- ✅ API documentation access

## 📝 Usage Examples

### Register User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "bookworm", "password": "securepass123"}'
```

### Login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=bookworm&password=securepass123"
```

### Get Book Recommendations
```bash
curl -X POST "http://localhost:8000/recommendations/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "psychological thrillers with twist endings"}'
```

## 🔒 Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: Secure authentication with expiration
- **Input Validation**: Pydantic schema validation
- **Error Handling**: No sensitive data in error responses
- **CORS**: Configured for specific frontend origins

## 📦 Dependencies

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Beanie** - MongoDB ODM
- **Motor** - Async MongoDB driver
- **Pydantic** - Data validation
- **PassLib** - Password hashing
- **Python-JOSE** - JWT handling
- **OpenAI** - AI integration
- **Python-dotenv** - Environment management

## 🌐 Production Deployment

### Environment Variables Required:
- `MONGO_CONNECTION_STRING` - MongoDB Atlas connection
- `JWT_SECRET_KEY` - Secure random key
- `OPENAI_API_KEY` - OpenAI API access

### Security Checklist:
- ✅ Secure JWT secret key (32+ random bytes)
- ✅ MongoDB connection with authentication
- ✅ OpenAI API key with appropriate limits
- ✅ CORS configured for production domain
- ✅ HTTPS in production (handled by reverse proxy)

## 🎯 Example Queries That Work

Try these natural language queries:

- "psychological thrillers with twist endings"
- "sci-fi books about space exploration"
- "historical romance novels"
- "mystery books like Agatha Christie"
- "fantasy books with strong female protagonists"
- "non-fiction about productivity and success"

## 🔍 Response Format

Book recommendations return:
```json
[
  {
    "title": "The Silent Patient",
    "author": "Alex Michaelides",
    "genre": "Psychological Thriller",
    "brief_summary": "A woman refuses to speak after allegedly murdering her husband...",
    "short_description": "Perfect psychological thriller with an unexpected twist ending..."
  }
]
```

## 🛠️ Development

### Run in Development Mode
```bash
python run.py
```
- Auto-reload on code changes
- Detailed logging
- Interactive API docs

### Code Structure
- **Modular Design**: Separate concerns (auth, recommendations, database)
- **Async/Await**: Full async support for database and API calls
- **Type Hints**: Complete type annotations throughout
- **Error Handling**: Comprehensive exception management
- **Documentation**: Detailed docstrings and comments

## 🎉 Status: Complete & Production Ready!

This backend is a fully functional, secure, and scalable API ready for production use. It follows FastAPI best practices and includes everything needed for a modern AI-powered book recommendation service.

**Ready to integrate with any frontend framework! 🚀**