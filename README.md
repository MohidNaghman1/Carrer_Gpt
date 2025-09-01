# 🚀 CareerGPT - AI-Powered Career Intelligence Platform

CareerGPT is a comprehensive AI-powered career assistance platform that helps professionals with resume analysis, career guidance, learning paths, and job search. Built with modern technologies and powered by advanced AI agents.

## ✨ Features

### 🎯 **Multi-Agent AI System**
- **CareerAdvisor**: General career guidance with RAG (Retrieval Augmented Generation)
- **ResumeAnalyst**: Comprehensive resume analysis and optimization recommendations
- **ResumeQAAgent**: Answers questions about uploaded resumes
- **LearningPath**: Creates personalized learning roadmaps for career transitions
- **JobSearch**: Searches for job opportunities using real-time web data

### 💬 **Real-time Chat Interface**
- Server-sent events (SSE) for streaming AI responses
- Markdown rendering with emoji support
- Persistent chat history with session management
- File upload for resume analysis (PDF, DOCX)

### 🔐 **Authentication & Security**
- JWT-based authentication with bcrypt password hashing
- Protected routes and API endpoints
- CORS configuration for production deployment

### 📊 **Smart Routing System**
- Hybrid supervisor with Python rules + LLM routing
- Context-aware decision making based on conversation history
- Resume follow-up detection for seamless user experience

## 🏗️ Architecture

### Backend (FastAPI + Python)
```
Backend/
├── api/routes/          # FastAPI route handlers
│   ├── auth.py         # Authentication endpoints
│   └── chat.py         # Chat and session management
├── core/               # Configuration and security
│   ├── config.py       # Environment configuration
│   └── security.py     # JWT and password handling
├── db/                 # Database models and schemas
│   ├── database.py     # SQLAlchemy configuration
│   ├── models.py       # Database models
│   └── schemas.py      # Pydantic schemas
├── langgraph_core/     # AI agent orchestration
│   ├── agents/         # Specialized AI agents
│   ├── graph_backend.py # LangGraph workflow
│   └── utils/          # File processing utilities
├── services/           # Business logic
└── main.py            # Application entry point
```

### Frontend (Next.js + TypeScript)
```
frontend/src/
├── app/               # Next.js app router pages
│   ├── chat/         # Chat interface
│   ├── login/        # Authentication pages
│   └── register/     # User registration
├── context/           # React context providers
├── services/          # API client configuration
└── types/             # TypeScript type definitions
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: MySQL with SQLAlchemy ORM
- **AI/ML**: LangChain + LangGraph
- **LLM Provider**: Groq (llama-3.3-70b-versatile)
- **Authentication**: JWT with bcrypt
- **File Processing**: PyMuPDF, python-docx
- **Vector Database**: FAISS
- **Web Search**: Tavily API
- **Migrations**: Alembic

### Frontend
- **Framework**: Next.js 15 with React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Context
- **HTTP Client**: Axios
- **Markdown**: React Markdown
- **Notifications**: React Hot Toast

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- API Keys: Groq, Google AI, Tavily

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd CareerGPT/Backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
Create a `.env` file in the Backend directory:
```env
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/careergpt_db
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_ORIGIN=http://localhost:3000
```

5. **Database Setup**
```bash
# Run migrations
alembic upgrade head
```

6. **Start the backend**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd ../frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Environment Configuration**
Create a `.env.local` file:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

4. **Start the frontend**
```bash
npm run dev
```

## 📱 Usage

### 1. **User Registration & Authentication**
- Register a new account or login with existing credentials
- JWT tokens are automatically managed

### 2. **Chat Interface**
- Start a new chat session
- Ask career-related questions
- Upload resumes for analysis
- Get personalized guidance

### 3. **Resume Analysis**
- Upload PDF or DOCX resumes
- Receive comprehensive analysis including:
  - ATS compatibility scoring
  - Strengths and weaknesses identification
  - Keyword optimization recommendations
  - Professional formatting suggestions

### 4. **Learning Paths**
- Describe your current skills and target role
- Receive step-by-step learning roadmaps
- Get project recommendations and resource suggestions

### 5. **Job Search**
- Search for job opportunities by skills and location
- Get real-time job market intelligence
- Receive application strategies and insights

## 🔧 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/token` - User login

### Chat Management
- `GET /chat/` - Get all user sessions
- `POST /chat/` - Create new chat session
- `GET /chat/{session_id}` - Get specific session
- `PUT /chat/{session_id}` - Update session title
- `DELETE /chat/{session_id}` - Delete session

### Chat Messages
- `POST /chat/{session_id}/messages/stream` - Send message (streaming)
- `POST /chat/resume-analysis` - Upload resume for new session
- `POST /chat/{session_id}/resume-analysis` - Upload resume to existing session

## 🚀 Deployment

### Backend (Render)
1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard
3. Deploy with the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Frontend (Vercel)
1. Connect your GitHub repository to Vercel
2. Set environment variables:
   - `NEXT_PUBLIC_API_BASE_URL`: Your Render backend URL
3. Deploy automatically on push to main branch

## 🧪 Development

### Running Tests
```bash
# Backend tests
cd Backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality
```bash
# Backend linting
cd Backend
black .
flake8 .

# Frontend linting
cd frontend
npm run lint
```

## 📊 Database Schema

### Users Table
- `id`: Primary key
- `email`: Unique email address
- `hashed_password`: Bcrypt hashed password

### Chat Sessions Table
- `id`: Primary key
- `title`: Session title
- `created_at`: Creation timestamp
- `resume_text`: Extracted resume content
- `user_id`: Foreign key to users

### Chat Messages Table
- `id`: Primary key
- `role`: 'human' or 'ai'
- `content`: Message content
- `timestamp`: Message timestamp
- `session_id`: Foreign key to chat_sessions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) for AI orchestration
- [Groq](https://groq.com/) for fast LLM inference
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Next.js](https://nextjs.org/) for the frontend framework
- [Tailwind CSS](https://tailwindcss.com/) for styling

## 📞 Support

For support, email support@careergpt.com or create an issue in the GitHub repository.

---

**Built with ❤️ for career advancement**