# Frontend Application Documentation

## Overview
The frontend is a Vue 3 single-page application (SPA) that provides an interactive interface for the math learning platform. It features a modern UI built with Tailwind CSS and uses Pinia for state management.

## Technology Stack
- Vue 3
- Vite
- Pinia for state management
- Vue Router
- Tailwind CSS
- KaTeX for math rendering
- Axios for API requests
- Vitest for testing

## Setup

### Prerequisites
- Node.js 16+
- npm or yarn

### Development Setup
1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env
```

Required environment variables:
- `VITE_API_URL`: Backend API URL
- `VITE_AUTH_TOKEN_KEY`: Local storage key for auth token

3. Start development server:
```bash
npm run dev
```

### Production Build
```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/         # Reusable Vue components
│   │   ├── common/        # Shared components
│   │   └── lesson/        # Learning session components
│   ├── router/            # Vue Router configuration
│   ├── services/          # API services
│   ├── stores/            # Pinia stores
│   ├── views/             # Page components
│   ├── App.vue            # Root component
│   └── main.js           # Application entry point
├── public/               # Static assets
└── tests/               # Test files
```

## Key Components

### Views
- `Login.vue`: User authentication
- `Register.vue`: New user registration
- `Dashboard.vue`: User dashboard and progress overview
- `SkillSelection.vue`: Learning category selection
- `LearningSession.vue`: Active learning session
- `KatexTest.vue`: Math rendering test page

### Components
- `QuestionCard.vue`: Question display and answer interface
- `KatexRenderer.vue`: Math formula rendering
- `Nav.vue`: Navigation bar
- `MathText.vue`: Inline math text rendering

### Stores
- `auth.js`: Authentication state and user data
- `lesson.js`: Learning session state and logic

### Services
- `auth.service.js`: Authentication API calls
- `lesson.service.js`: Learning session API calls
- `user.service.js`: User profile and settings
- `axios.js`: Axios instance with interceptors

## Features

### Authentication
- JWT-based authentication
- Persistent login state
- Protected route guards
- Registration with validation

### Learning Session
- Interactive question display
- Multiple choice and single answer support
- Real-time answer validation
- Progress tracking
- Session management

### Math Rendering
- KaTeX integration for math formulas
- Support for inline and block math
- LaTeX syntax support

### User Interface
- Responsive design
- Dark/light mode support
- Loading states
- Error handling
- Toast notifications

## State Management

### Auth Store
```javascript
{
  user: {
    id: string,
    name: string,
    email: string,
    selected_skills: string[]
  },
  token: string,
  isAuthenticated: boolean
}
```

### Lesson Store
```javascript
{
  currentSession: {
    id: string,
    currentQuestion: Object,
    progress: {
      answered: number,
      total: number
    }
  },
  selectedSkills: string[]
}
```

## Testing

Run tests:
```bash
npm run test
```

Key test files:
- `QuestionCard.test.js`: Question component tests
- `auth.store.test.js`: Authentication store tests
- `lesson.service.test.js`: API service tests

## Error Handling
- API error interceptors
- Form validation
- Network error handling
- Session timeout handling

## Build and Deployment

### Docker Build
```bash
docker build -t math-learning-frontend .
```

### Environment Configurations
- `development`: Hot-reloading, source maps
- `production`: Optimized build, minification
- `test`: Test environment settings
