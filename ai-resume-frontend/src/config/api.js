// API Configuration
const getApiUrl = () => {
  // Use environment variable if available
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // Fallback: Check if we're in development (localhost)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  
  // For production (Vercel deployment)
  // Replace this with your actual backend API URL
  return 'https://your-backend-api-url.com';
};

export const API_BASE_URL = getApiUrl();

export const API_ENDPOINTS = {
  ANALYZE_RESUME: `${API_BASE_URL}/analyze_resume`,
};

// Debug logging and health check
console.log('API Configuration:', {
  hostname: window.location.hostname,
  envApiUrl: import.meta.env.VITE_API_URL,
  finalApiUrl: API_BASE_URL
});

// Test backend connection
export const testBackendConnection = async () => {
  try {
    console.log('Testing backend connection to:', API_BASE_URL);
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('Backend health check successful:', data);
      return { success: true, data };
    } else {
      console.log('Backend health check failed:', response.status, response.statusText);
      return { success: false, error: `HTTP ${response.status}` };
    }
  } catch (error) {
    console.log('Backend connection error:', error);
    return { success: false, error: error.message };
  }
};