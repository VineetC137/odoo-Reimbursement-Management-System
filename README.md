# Reimbursement Management System

A full-stack expense reimbursement management system with role-based access control, multi-currency support, OCR receipt scanning, and automated approval workflows.

## Features

- **Role-Based Access Control**: Admin, Manager, and Employee roles with distinct permissions
- **Multi-Currency Support**: Automatic currency conversion using real-time exchange rates
- **OCR Receipt Scanning**: Extract expense details from receipt images using Tesseract OCR
- **Approval Workflows**: Configurable approval rules with manager and special approver assignments
- **Expense Tracking**: Create, view, and manage expense reimbursement requests
- **Dashboard Analytics**: Role-specific dashboards with expense statistics and insights

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Migrations**: Alembic
- **Authentication**: JWT tokens with bcrypt password hashing
- **External APIs**: REST Countries API, ExchangeRate-API
- **OCR**: Tesseract OCR

### Frontend
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS 4
- **Routing**: React Router v7
- **HTTP Client**: Axios
- **Forms**: React Hook Form

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **Tesseract OCR** - Required for receipt scanning functionality
  - **macOS**: `brew install tesseract`
  - **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
  - **Windows**: Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

## Project Structure

```
reimbursement-management-system/
├── backend/                 # FastAPI backend application
│   ├── alembic/            # Database migrations
│   ├── app/                # Application code
│   │   ├── routers/        # API route handlers
│   │   ├── services/       # Business logic layer
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── schemas.py      # Pydantic schemas
│   │   └── main.py         # FastAPI app entry point
│   ├── tests/              # Backend tests
│   ├── seed.py             # Database seed script
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── types/          # TypeScript type definitions
│   │   └── lib/            # Utilities and configurations
│   └── package.json        # Node.js dependencies
└── README.md              # This file
```

## Getting Started

### 1. Backend Setup

#### Step 1: Navigate to backend directory
```bash
cd backend
```

#### Step 2: Create and activate virtual environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

#### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Configure environment variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and configure the following variables:
# DATABASE_URL=sqlite:///./reimbursement.db
# JWT_SECRET=your-secret-key-change-this-in-production
# JWT_ALGORITHM=HS256
# JWT_EXPIRATION_HOURS=24
```

**Important Environment Variables:**
- `DATABASE_URL`: Database connection string (SQLite by default)
- `JWT_SECRET`: Secret key for JWT token generation (change in production!)
- `FX_API_KEY`: (Optional) API key for ExchangeRate-API (uses free tier if not set)

#### Step 5: Run database migrations
```bash
alembic upgrade head
```

#### Step 6: Seed the database with sample data
```bash
python seed.py
```

This creates:
- **Admin**: admin@acme.com / admin123
- **Manager**: manager@acme.com / manager123
- **Employee 1**: john.doe@acme.com / employee123
- **Employee 2**: jane.smith@acme.com / employee123

#### Step 7: Start the backend server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`

### 2. Frontend Setup

#### Step 1: Navigate to frontend directory
```bash
cd frontend
```

#### Step 2: Install dependencies
```bash
npm install
```

#### Step 3: Configure environment variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and configure:
# VITE_API_BASE_URL=http://localhost:8000/api
```

#### Step 4: Start the development server
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Running the Application

### Start Backend
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend
```bash
cd frontend
npm run dev
```

### Access the Application
Open your browser and navigate to `http://localhost:5173`

Login with one of the seeded accounts:
- **Admin**: admin@acme.com / admin123
- **Manager**: manager@acme.com / manager123
- **Employee**: john.doe@acme.com / employee123

## Running Tests

### Backend Tests
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pytest
```

Run specific test files:
```bash
pytest tests/test_auth_endpoints.py
pytest tests/test_expense_service.py
```

Run with verbose output:
```bash
pytest -v
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

### Frontend Tests
Currently, the frontend does not have automated tests configured. You can add testing frameworks like Vitest or Jest as needed.

## API Documentation

Once the backend is running, you can access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Troubleshooting

### Backend Issues

**Issue**: `ModuleNotFoundError` when running the backend
- **Solution**: Ensure virtual environment is activated and dependencies are installed
  ```bash
  source venv/bin/activate
  pip install -r requirements.txt
  ```

**Issue**: Database migration errors
- **Solution**: Delete the database file and re-run migrations
  ```bash
  rm reimbursement.db
  alembic upgrade head
  python seed.py
  ```

**Issue**: Tesseract OCR not found
- **Solution**: Install Tesseract OCR for your operating system (see Prerequisites)
- On Windows, you may need to add Tesseract to your PATH

### Frontend Issues

**Issue**: `ECONNREFUSED` when making API calls
- **Solution**: Ensure the backend server is running on port 8000
- Check that `VITE_API_BASE_URL` in `.env` matches your backend URL

**Issue**: Module not found errors
- **Solution**: Delete `node_modules` and reinstall
  ```bash
  rm -rf node_modules package-lock.json
  npm install
  ```

**Issue**: Port 5173 already in use
- **Solution**: Kill the process using the port or specify a different port
  ```bash
  npm run dev -- --port 3000
  ```

## Development Workflow

1. **Create a new feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes to backend or frontend**

3. **Run tests to ensure nothing breaks**
   ```bash
   cd backend && pytest
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add your feature description"
   ```

5. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## License

This project is for educational and demonstration purposes.

## Support

For issues, questions, or contributions, please open an issue in the project repository.
