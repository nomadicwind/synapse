import axios from 'axios';
import SecureStorage from './SecureStorage';

class APIClient {
  constructor() {
    // Use API_BASE_URL from .env file
    this.baseURL = process.env.API_BASE_URL || 'http://localhost:8000';
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'X-Client-Version': '1.0.0',
      },
    });

    // Add retry logic for failed requests
    this.retryCount = 3;
    this.retryDelay = 1000;

    // Add request interceptor to include auth token
    this.client.interceptors.request.use(
      async (config) => {
        const token = await SecureStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor to handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          await SecureStorage.deleteItem('auth_token');
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(credentials) {
    const response = await this.client.post('/auth/login', credentials);
    const { token, user } = response.data;
    await SecureStorage.setItem('auth_token', token);
    return { token, user };
  }

  async logout() {
    await this.client.post('/auth/logout');
    await SecureStorage.deleteItem('auth_token');
  }


  // STT service endpoints
  async transcribeAudio(formData) {
    // Use STT_SERVICE_URL from environment variables
    const sttURL = process.env.STT_SERVICE_URL || 'http://localhost:5000';
    try {
      const response = await axios.post(`${sttURL}/transcribe`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000, // Longer timeout for audio processing
      });
      return response.data;
    } catch (error) {
      throw new Error(`STT Service Error: ${error.response?.data?.detail || error.message}`);
    }
  }

  // Health check
  async healthCheck() {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      throw new Error(`Health Check Failed: ${error.response?.status || error.message}`);
    }
  }

  // Enhanced request with retry logic
  async requestWithRetry(config) {
    let lastError;
    
    for (let i = 0; i < this.retryCount; i++) {
      try {
        return await this.client(config);
      } catch (error) {
        lastError = error;
        
        // Don't retry on 4xx errors (client errors)
        if (error.response && error.response.status >= 400 && error.response.status < 500) {
          break;
        }
        
        // Wait before retrying
        if (i < this.retryCount - 1) {
          await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, i)));
        }
      }
    }
    
    throw lastError;
  }

  // Enhanced methods with retry logic
  async getKnowledgeItems() {
    const response = await this.requestWithRetry({
      method: 'get',
      url: '/api/v1/knowledge-items',
    });
    return response.data;
  }

  async captureItem(captureData) {
    const response = await this.requestWithRetry({
      method: 'post',
      url: '/api/v1/capture',
      data: captureData,
    });
    return response.data;
  }

  async getKnowledgeItem(id) {
    const response = await this.requestWithRetry({
      method: 'get',
      url: `/api/v1/knowledge-items/${id}`,
    });
    return response.data;
  }
}

// Create and export a singleton instance
export const apiClient = new APIClient();

export default APIClient;
