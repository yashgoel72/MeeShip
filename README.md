# Meesho Image Optimizer

A high-performance image optimization service built with FastAPI (Python) and React (TypeScript). Optimize your e-commerce product images for faster loading times and better user experience.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![React](https://img.shields.io/badge/react-18+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)

## 🚀 Features

- **Image Optimization**: Compress and resize images while maintaining quality
- **Batch Processing**: Optimize multiple images at once
- **Format Conversion**: Convert between JPEG, PNG, and WebP formats
- **User Authentication**: Secure JWT-based authentication
- **API First**: RESTful API with comprehensive documentation
- **Modern UI**: Beautiful, responsive React interface with TailwindCSS
- **Docker Ready**: Full containerization for easy deployment

## 📋 Prerequisites

- **Python 3.11+** (for backend)
- **Node.js 20+** (for frontend)
- **Docker & Docker Compose** (optional, for containerized deployment)
- **PostgreSQL 15+** (or use Docker)

## 🛠️ Quick Start

### Option 1: Docker Compose (Recommended)

The easiest way to get started is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/yourusername/meesho-image-optimizer.git
cd meesho-image-optimizer

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

Services will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001

### Option 2: Local Development

#### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# Ensure DATABASE_URL points to your PostgreSQL instance

# Run database migrations (if using Alembic)
# alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start the development server
npm run dev
```

## 📁 Project Structure

```
meesho-image-optimizer/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # Application entry point
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # Database connection
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── routers/           # API routes
│   │   ├── services/          # Business logic
│   │   └── middlewares/       # Custom middlewares
│   ├── tests/                 # Backend tests
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── main.tsx           # React entry point
│   │   ├── App.tsx            # Main App component
│   │   ├── components/        # Reusable components
│   │   ├── pages/             # Page components
│   │   └── index.css          # Global styles
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── .env.example
│
├── docs/                       # Documentation
│   └── API.md                 # API documentation
│
├── infra/                      # Infrastructure
│   └── azure-pipelines.yml    # CI/CD pipeline
│
├── docker-compose.yml          # Development compose
├── docker-compose.prod.yml     # Production compose
├── .gitignore
└── README.md
```

## 🔧 Configuration

### Backend Environment Variables

| Variable                    | Description                                 | Default                |
|-----------------------------|---------------------------------------------|------------------------|
| `DATABASE_URL`              | PostgreSQL connection string                | Required               |
| `SECRET_KEY`                | JWT secret key                              | Required               |
| `DEBUG`                     | Enable debug mode                           | `false`                |
| `ALLOWED_ORIGINS`           | CORS allowed origins                        | `http://localhost:3000`|
| `REDIS_URL`                 | Redis connection string                     | Optional               |
| `AZURE_FOUNDRY_ENDPOINT`    | FLUX API endpoint URL (must include protocol, e.g. `https://`; if missing, `https://` will be auto-prepended) | Required for FLUX      |
| `AZURE_FOUNDRY_MODEL_NAME`  | FLUX model name (e.g., FLUX.1-Kontext-pro)  | Required for FLUX      |
| `AZURE_FOUNDRY_API_KEY`     | FLUX API key                                | Required for FLUX      |
| `AZURE_OPENAI_ENDPOINT`     | Azure OpenAI endpoint (for `gpt-image-1.5`) | Required for GPT Image |
| `AZURE_OPENAI_API_KEY`      | Azure OpenAI API key (used as Bearer token) | Required for GPT Image |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Azure OpenAI deployment name (e.g. `gpt-image-1.5`) | Optional |
| `OPENAI_API_VERSION`        | Azure OpenAI API version (e.g. `2024-02-01`) | Optional |

#### FLUX Integration

To use the FLUX optimizer, set both the endpoint and model name in your `.env` file:

```env
AZURE_FOUNDRY_ENDPOINT=https://your-flux-endpoint.openai.azure.com/openai/deployments/your-deployment/chat/completions?api-version=2023-07-01-preview
AZURE_FOUNDRY_MODEL_NAME=FLUX.1-Kontext-pro
AZURE_FOUNDRY_API_KEY=your-api-key
```

- `AZURE_FOUNDRY_ENDPOINT`: The full URL to your FLUX deployment endpoint. **Must include `http://` or `https://`. If omitted, `https://` will be automatically added.**
- `AZURE_FOUNDRY_MODEL_NAME`: The model name required by the FLUX API (not the endpoint).

**Both fields are required for FLUX integration.** The backend will use these values to call the FLUX API with the correct payload.
If the protocol is missing from the endpoint, `https://` will be automatically prepended to ensure valid requests.
If unset, the system will fall back to the local optimizer.

#### GPT Image (gpt-image-1.5) Integration

To use `gpt-image-1.5`, set these variables in `backend/.env`:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-image-1.5
OPENAI_API_VERSION=2024-02-01
```

### Frontend Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |

## 📖 API Documentation

Once the backend is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

For detailed API documentation, see [docs/API.md](docs/API.md).

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm run test

# Run with coverage
npm run test:coverage
```

## 🚢 Deployment

### Production with Docker Compose

```bash
# Create production environment file
cp .env.example .env.prod

# Edit .env.prod with production values
# Make sure to set strong passwords and secrets!

# Deploy
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Environment Variables for Production

```bash
# Required for production
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
SECRET_KEY=<random-256-bit-key>
MINIO_ROOT_USER=<minio-user>
MINIO_ROOT_PASSWORD=<minio-password>
ALLOWED_ORIGINS=https://your-domain.com
API_URL=https://api.your-domain.com
```

### Frontend Deployment on Vercel

The frontend is configured for deployment on [Vercel](https://vercel.com/) with SPA (Single Page Application) support.

**Why `vercel.json` is needed:**  
React Router uses client-side routing with `BrowserRouter`. When users directly access URLs like `/privacy` or refresh on those pages, Vercel needs to serve `index.html` for all routes so React Router can handle the navigation. Without this configuration, direct URL access returns a 404 error.

The `vercel.json` in the project root configures rewrites to redirect all requests to `index.html`:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

**Deployment steps:**
1. Connect your GitHub repository to Vercel
2. Set the **Root Directory** to `frontend`
3. Vercel will auto-detect Vite and configure build settings
4. Set environment variables (e.g., `VITE_API_URL`)
5. Deploy!

All routes (`/privacy`, `/terms`, `/refund`, `/contact`) will work on direct access and refresh.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - JavaScript library for building UIs
- [TailwindCSS](https://tailwindcss.com/) - Utility-first CSS framework
- [Vite](https://vitejs.dev/) - Next-generation frontend tooling

## 📞 Support

For support, please open an issue in the GitHub repository or contact the maintainers.

---

Made with ❤️ for Meesho
## Local Development Database Setup (PostgreSQL via Docker Compose)

1. **Start the database and backend services:**
   ```sh
   cd backend
   docker-compose up db
   ```
   This will start a local PostgreSQL instance with the correct credentials and database name.

2. **Run Prisma migrations:**
   ```sh
   npx prisma migrate dev
   ```
   This will apply all migrations to your local database.

3. **Start the backend server:**
   ```sh
   docker-compose up backend
   ```
   Or run your backend directly if preferred.

4. **Environment variables:**
   - Ensure `DATABASE_URL` in `.env` matches the Docker Compose config:
     ```
     postgresql+asyncpg://postgres:postgres@db:5432/meesho_optimizer
     ```
   - Prisma config uses:
     ```
     postgresql://postgres:postgres@db:5432/meesho_optimizer
     ```

5. **Resetting the database:**
   ```sh
   docker-compose down -v
   ```
   This will remove all data and volumes for a clean slate.

**You can now test the app end-to-end using the local PostgreSQL database.**