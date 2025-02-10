# Getting Started

## Prerequisites
- Node.js (v14 or higher)
- npm or yarn
- Firebase account

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/budget-app.git
cd budget-app
```

2. Install dependencies
```bash
npm install
```

3. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` with your Firebase configuration:
```
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_auth_domain
VITE_FIREBASE_PROJECT_ID=your_project_id
```

4. Start development server
```bash
npm run dev
```

## Firebase Setup

1. Create a new Firebase project
2. Enable Authentication
3. Set up Firestore database
4. Configure security rules

## Development Workflow

1. Create a new branch for your feature
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit
```bash
git add .
git commit -m "feat: add new feature"
```

3. Push changes and create a pull request
```bash
git push origin feature/your-feature-name
```

## Building for Production

```bash
npm run build
```

## Running Tests

```bash
npm run test
npm run test:e2e
```

