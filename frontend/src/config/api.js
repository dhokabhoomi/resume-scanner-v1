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
  BULK_ANALYZE: `${API_BASE_URL}/bulk_analyze_resumes`,
  BULK_JOB_STATUS: `${API_BASE_URL}/bulk_job_status`,
  EXPORT_RESULTS: `${API_BASE_URL}/export_results`,
};

// Debug logging and health check
console.log('API Configuration:', {
  hostname: window.location.hostname,
  envApiUrl: import.meta.env.VITE_API_URL,
  finalApiUrl: API_BASE_URL
});

// Test backend connection with timeout
export const testBackendConnection = async (timeoutMs = 5000) => {
  try {
    console.log('Testing backend connection to:', API_BASE_URL);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    if (response.ok) {
      const data = await response.json();
      console.log('Backend health check successful:', data);
      return { success: true, data, timestamp: new Date().toISOString() };
    } else {
      console.log('Backend health check failed:', response.status, response.statusText);
      return { 
        success: false, 
        error: `HTTP ${response.status}: ${response.statusText}`,
        timestamp: new Date().toISOString()
      };
    }
  } catch (error) {
    console.log('Backend connection error:', error);

    let errorMessage = 'Connection failed';
    if (error.name === 'AbortError') {
      errorMessage = 'Connection timeout (5s)';
    } else if (error.message.includes('Failed to fetch')) {
      errorMessage = 'Backend unavailable';
    } else if (error.message.includes('429') || error.message.includes('rate limit')) {
      errorMessage = 'Rate limited - too many requests';
    } else {
      errorMessage = error.message;
    }

    return {
      success: false,
      error: errorMessage,
      timestamp: new Date().toISOString(),
      isRateLimit: errorMessage.includes('rate limit') || errorMessage.includes('429')
    };
  }
};

// Periodic health check manager
export class BackendHealthMonitor {
  constructor(onStatusChange) {
    this.onStatusChange = onStatusChange;
    this.intervalId = null;
    this.isMonitoring = false;
    this.checkInterval = 120000; // 2 minutes to reduce rate limiting
    this.lastStatus = null;
  }

  start() {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    console.log('Starting backend health monitoring...');
    
    // Initial check
    this.performHealthCheck();
    
    // Periodic checks
    this.intervalId = setInterval(() => {
      this.performHealthCheck();
    }, this.checkInterval);
  }

  stop() {
    if (!this.isMonitoring) return;
    
    this.isMonitoring = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    console.log('Stopped backend health monitoring');
  }

  async performHealthCheck() {
    const status = await testBackendConnection(3000); // Shorter timeout for periodic checks
    
    // Only notify if status changed
    if (!this.lastStatus || this.lastStatus.success !== status.success) {
      console.log('Backend status changed:', status);
      if (this.onStatusChange) {
        this.onStatusChange(status);
      }
    }
    
    this.lastStatus = status;
  }

  // Manual check (for retry scenarios)
  async checkNow() {
    return await this.performHealthCheck();
  }
}