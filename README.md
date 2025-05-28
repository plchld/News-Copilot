# News Copilot v2 - Full Stack Greek News Intelligence Platform

> **Note**: Major architecture upgrade! Django + Next.js stack with AI-powered analysis.

## 🚀 Quick Start

```bash
# 1. Clone and setup environment
git clone https://github.com/yourusername/news-copilot.git
cd news-copilot
cp .env.example .env  # Configure your API keys

# 2. Start databases (PostgreSQL & MongoDB)
docker-compose up -d

# 3. Backend setup (Django)
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# 4. Frontend setup (Next.js) - New terminal
cd frontend
pnpm install
pnpm run dev
```

- Backend API: http://localhost:8000
- Frontend App: http://localhost:3000
- API Docs: http://localhost:8000/api/docs/

## 🎯 Features

### Backend (Django)
- **REST API**: Full CRUD operations for articles, sources, and analyses
- **Authentication**: JWT-based auth with user tiers (free/premium/admin)
- **AI Integration**: 7 specialized agents for comprehensive analysis
- **Background Jobs**: Celery for async article processing
- **Real-time Updates**: WebSocket support for live progress

### Frontend (Next.js)
- **Modern UI**: Tailwind CSS with responsive design
- **Type Safety**: Full TypeScript implementation
- **State Management**: Zustand + React Query
- **Real-time**: SSE/WebSocket integration
- **Auth Flow**: Secure JWT handling with refresh tokens

### AI Analysis Agents
1. **Jargon Agent**: Technical term explanations
2. **Viewpoints Agent**: Alternative perspectives
3. **Fact Check Agent**: Claim verification
4. **Bias Agent**: Political spectrum analysis
5. **Timeline Agent**: Event chronology
6. **Expert Agent**: Domain expert opinions
7. **X Pulse Agent**: Social media sentiment

## 🏗️ Architecture

```
News-Copilot/
├── backend/           # Django REST API
├── frontend/         # Next.js TypeScript
├── news-aggregator/  # Legacy v2 (to be migrated)
├── deprecated_v1/    # Original Flask system
└── docker-compose.yml # PostgreSQL + MongoDB
```

## 📚 Documentation

- [Project Architecture](PROJECT_ARCHITECTURE.md) - Full system design
- [Migration Plan](MIGRATION_PLAN.md) - Upgrade roadmap
- [API Documentation](http://localhost:8000/api/docs/) - Interactive API docs
- [Development Guide](news-aggregator/README.md) - Detailed setup

## 🛠️ Development

```bash
# Run everything with Make
make setup          # Complete initial setup
make run-api       # Start Django server
make run-web       # Start Next.js
make test          # Run all tests
make format        # Format code
```

## 🔧 Configuration

Required environment variables:
- `XAI_API_KEY` - For Grok AI API
- `DJANGO_SECRET_KEY` - Django security
- `POSTGRES_*` - Database credentials
- `NEXT_PUBLIC_API_URL` - Frontend API endpoint

## 🚢 Deployment

- **Backend**: Django on AWS ECS/Kubernetes
- **Frontend**: Next.js on Vercel
- **Databases**: RDS PostgreSQL + DocumentDB
- **Cache**: Redis on ElastiCache

---

> Built with ❤️ for Greek news intelligence
