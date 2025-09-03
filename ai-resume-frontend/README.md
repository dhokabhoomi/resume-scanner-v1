# VU Resume Analyzer Frontend

A modern, responsive frontend for the VU Resume Analyzer built with React and Vite.

## Environment Configuration

The application supports both development and production environments with different API endpoints.

### Development Setup

1. Copy the environment file:
```bash
cp .env.example .env
```

2. Update the `.env` file:
```env
GOOGLE_API_KEY=your_google_api_key_here
VITE_API_URL=http://localhost:8000
```

### Production Deployment

For production deployment (e.g., on Vercel), set the environment variable:
- `VITE_API_URL`: Your backend API URL (e.g., `https://your-api.com`)

### Environment Variables

- `VITE_API_URL`: Backend API base URL
  - Development: `http://localhost:8000`
  - Production: Your deployed backend URL

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## API Configuration

The app automatically detects the environment:
- **Localhost**: Uses `http://localhost:8000`
- **Production**: Uses the `VITE_API_URL` environment variable
- **Fallback**: Uses hostname detection

## Deployment

This project is deployed on Vercel at: https://resume-scanner-v1.vercel.app/

Make sure to set the `VITE_API_URL` environment variable in your Vercel project settings.