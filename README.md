# GateLock

GateLock is an access-control platform with integrated Face Recognition technology.

Its purpose is to serve as a security system capable of detecting, recognizing, and allowing access to a given room.

## Architecture

- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS
- **Backend**: Node.js + Express + MongoDB
- **Database**: MongoDB Atlas
- **Raspberry Pi**: Python (face recognition, video capture, API integration)
- **CI/CD**: GitHub Actions for unit tests


## Quick Start

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The application will be available at `http://localhost:3000`

### Simulate Notifications

To test notifications, open the browser console and run:

```javascript
simulateNotification()
```

Or with a specific name:

```javascript
simulateNotification('Person Name')
```

## Features

### Frontend (Implemented)

- Login/register screen
- Main screen with real-time notifications
- Alert history with details
- Person management (add new)
- Settings page with logout
- Responsive design (mobile and desktop)
- Dark mode
- Notification simulation

### Backend (Implemented)

- REST API with Node.js + Express
- JWT Authentication
- MongoDB integration
- Real-time notifications via API
- Video upload from Raspberry Pi
- Nuki Smart Lock integration (optional)
- Face recognition integration via Raspberry Pi

## Project Structure

```
GateLock/
├── frontend/          # React application
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── layouts/      # Application layouts
│   │   ├── pages/        # Main pages
│   │   ├── services/     # API services
│   │   └── store/        # State management (Zustand)
│   └── package.json
├── backend/           # Node.js API
│   ├── src/
│   │   ├── config/       # Configuration (database, etc.)
│   │   ├── controllers/  # Route controllers
│   │   ├── middleware/   # Middleware (auth, error handling)
│   │   ├── models/       # Mongoose models
│   │   ├── routes/       # Route definitions
│   │   ├── services/     # Nuki, etc.
│   │   └── utils/        # Utilities (JWT, etc.)
│   └── package.json
├── raspberry-pi/      # Face recognition (runs locally on device)
│   ├── api/           # Backend API client
│   ├── config/        # Configuration
│   ├── database/      # Embeddings database
│   ├── detection/     # Face detection
│   ├── recognition/   # Face recognition
│   └── main.py
├── spikes/            # Prototypes and experiments
│   └── FaceRecognitionPOC/
└── .github/
    └── workflows/    # GitHub Actions
```

## Tests

Unit tests run automatically in GitHub Actions on every push and pull request.

### Running Tests Locally

**Frontend:**
```bash
cd frontend
npm run test          # Run tests in watch mode
npm run test -- --run # Run tests once (CI mode)
npm run test:coverage # Run tests with coverage report
```

**Backend:**
```bash
cd backend
npm run test          # Run tests in watch mode
npm run test -- --run # Run tests once (CI mode)
npm run test:coverage # Run tests with coverage report
```

**Raspberry Pi:**
```bash
cd raspberry-pi
pytest tests/unit/ -v
```

### Test Coverage

Tests are organized as follows:

**Frontend:**
- `src/components/__tests__/` - Component tests
- `src/pages/__tests__/` - Page component tests
- `src/store/__tests__/` - Store/state management tests

**Backend:**
- `src/utils/__tests__/` - Utility function tests
- `src/controllers/__tests__/` - Controller tests
- `src/middleware/__tests__/` - Middleware tests

**Raspberry Pi:**
- `tests/unit/` - Unit tests (pytest)

### GitHub Actions

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Only when relevant files change (frontend/backend/raspberry-pi paths)

## Raspberry Pi Face Recognition

The main face recognition system runs on a Raspberry Pi. See [raspberry-pi/README.md](raspberry-pi/README.md) for setup and usage.

## Face Recognition Proof of Concept

A standalone facial-recognition prototype is available at **[Face Recognition POC](spikes/FaceRecognitionPOC)**. It demonstrates InsightFace models and video-based recognition. The main production system is in `raspberry-pi/`.

---

## Project Status

- Frontend (React + TypeScript + Vite)
- Backend (Node.js + Express + MongoDB)
- JWT Authentication
- REST API for persons, alerts, videos, Nuki
- Frontend-backend integration
- Raspberry Pi face recognition (InsightFace)

Modules within `/spikes` are experimental.

## Complete Quick Start

### Prerequisites

- **Node.js** >= 20.0.0
- **npm** >= 10.0.0
- **MongoDB** (MongoDB Atlas account or local instance)

### 1. Clone the repository

```bash
git clone <repository-url>
cd GateLock
```

### 2. Configure the Backend

```bash
cd backend
npm install
cp .env.example .env
```

Edit the `.env` file with your credentials:

```env
PORT=5000
NODE_ENV=development
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/gatelock?retryWrites=true&w=majority
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_EXPIRES_IN=7d
CORS_ORIGIN=http://localhost:3000
```

**Important**: Replace `MONGODB_URI` with your MongoDB Atlas connection string.

Start the backend server:

```bash
npm run dev
```

The backend will be available at `http://localhost:5000`

**Verification**: Open `http://localhost:5000/api/health` in your browser to confirm the backend is running.

### 3. Configure the Frontend

In a new terminal:

```bash
cd frontend
npm install
cp .env.example .env
```

The frontend `.env` file is already configured by default to connect to `http://localhost:5000/api`. If your backend runs on a different port, adjust `VITE_API_URL`.

Start the development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 4. Access the application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000/api
- **Health Check**: http://localhost:5000/api/health

### 5. First run

1. Open http://localhost:3000 in your browser
2. Create a new account using the registration form
3. Log in with your credentials
4. You can now use the application!

### Simulate notifications

To test real-time notifications, open the browser console (F12) and run:

```javascript
simulateNotification()
```

Or with a specific name:

```javascript
simulateNotification('Person Name')
```

### Available Scripts

**Backend:**
- `npm run dev` - Start server in development mode with hot-reload
- `npm run build` - Compile TypeScript to JavaScript
- `npm start` - Start server in production mode (requires previous build)
- `npm test` - Run unit tests
- `npm run lint` - Run linter

**Frontend:**
- `npm run dev` - Start development server
- `npm run build` - Build application for production
- `npm run preview` - Preview production build
- `npm test` - Run unit tests
- `npm run lint` - Run linter

---

## License

To be defined.
