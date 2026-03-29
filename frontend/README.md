# Reimbursement Management System - Frontend

React + TypeScript + Vite frontend application for the Reimbursement Management System.

## Tech Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS v4** - Utility-first CSS framework
- **React Router DOM** - Client-side routing
- **Axios** - HTTP client with interceptors
- **React Hook Form** - Form validation and management
- **date-fns** - Date utilities

## Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   └── axios.ts          # Axios instance with auth interceptor
│   ├── types/
│   │   └── index.ts          # TypeScript interfaces
│   ├── App.tsx               # Main app component
│   ├── main.tsx              # Entry point
│   └── index.css             # Global styles with Tailwind
├── .env                      # Environment variables
├── .env.example              # Environment variables template
└── package.json              # Dependencies
```

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and set:
```
VITE_API_BASE_URL=http://localhost:8000/api
```

3. Start development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Available Scripts

- `npm run dev` - Start development server with HMR
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Configuration

### Tailwind CSS

Custom colors are configured in `src/index.css`:
- **Primary**: `#2563EB` (blue)
- **Neutral**: `#F4F4F5` (light gray)

### Axios Instance

The axios instance (`src/lib/axios.ts`) includes:
- Base URL configuration from environment variables
- Request interceptor to add JWT token from localStorage
- Response interceptor to handle 401 errors and redirect to login

## Development

The frontend communicates with the FastAPI backend running on `http://localhost:8000`.

Authentication flow:
1. User logs in via `/api/auth/login`
2. JWT token is stored in localStorage
3. Token is automatically added to all API requests via axios interceptor
4. On 401 response, user is redirected to login page

## Building for Production

```bash
npm run build
```

The production build will be output to the `dist/` directory.
