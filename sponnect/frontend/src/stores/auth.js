import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

// Create axios instance with base URL
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000'
})

// Add interceptor to add token to requests
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Add response interceptor to normalize data format
api.interceptors.response.use(response => {
  // If response has data property and is an object, check for nested data
  if (response.data && typeof response.data === 'object') {
    // If response.data has a data property, normalize it
    if ('data' in response.data) {
      // Keep original response but normalize the data
      const normalizedResponse = { ...response };
      normalizedResponse.originalData = response.data;
      normalizedResponse.data = response.data.data;
      return normalizedResponse;
    }
  }
  return response;
}, async error => {
  const originalRequest = error.config;
  
  // Log the error for debugging
  console.error('API error:', {
    url: originalRequest.url,
    method: originalRequest.method,
    status: error.response?.status,
    data: error.response?.data
  });
  
  // If it's an unauthorized error and we haven't tried refreshing yet
  if (error.response && error.response.status === 401 && !originalRequest._retry) {
    originalRequest._retry = true;
    
    try {
      // Try to refresh the token - for this we'd need a backend endpoint
      // Assuming /api/refresh exists and works with the current token
      const refreshToken = localStorage.getItem('refreshToken');
      
      if (refreshToken) {
        const response = await axios.post(`${api.defaults.baseURL}/api/refresh`, {
          refresh_token: refreshToken
        });
        
        if (response.data.access_token) {
          // Store the new tokens
          localStorage.setItem('token', response.data.access_token);
          if (response.data.refresh_token) {
            localStorage.setItem('refreshToken', response.data.refresh_token);
          }
          
          // Update the auth header with the new token
          api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
          originalRequest.headers['Authorization'] = `Bearer ${response.data.access_token}`;
          
          // Retry the original request
          return api(originalRequest);
        }
      } else {
        console.error('No refresh token available for token refresh');
      }
    } catch (refreshError) {
      console.error('Token refresh failed:', refreshError);
      // Redirect to login page
      localStorage.removeItem('token');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userRole');
      window.location.href = '/login';
    }
  }
  
  return Promise.reject(error);
});

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem('token') || null)
  const userRole = ref(localStorage.getItem('userRole') || null)
  const user = ref(null)
  
  // Getters
  const isAuthenticated = computed(() => !!token.value)
  
  // Actions
  const login = async (credentials) => {
    try {
      const response = await api.post('/api/login', credentials)
      
      // Store token and role in local storage and state
      const accessToken = response.data.access_token
      const role = response.data.user_role
      
      localStorage.setItem('token', accessToken)
      localStorage.setItem('userRole', role)
      
      token.value = accessToken
      userRole.value = role
      
      // Fetch user profile after successful login
      await getProfile()
      
      return response
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }
  
  const register = async (userData) => {
    try {
      const response = await api.post('/api/register', userData)
      return response
    } catch (error) {
      console.error('Registration error:', error)
      throw error
    }
  }
  
  const logout = () => {
    // Clear token and user data from local storage and state
    localStorage.removeItem('token')
    localStorage.removeItem('userRole')
    
    token.value = null
    userRole.value = null
    
    // Redirect to home page (handled by the router)
    window.location.href = '/'
  }
  
  const getProfile = async () => {
    try {
      const response = await api.get('/api/profile')
      user.value = response.data
      return response.data
    } catch (error) {
      console.error('Get profile error:', error)
      if (error.response && error.response.status === 401) {
        // Token expired or invalid, logout
        logout()
      }
      throw error
    }
  }
  
  return {
    token,
    userRole,
    user,
    isAuthenticated,
    login,
    register,
    logout,
    getProfile
  }
})

// Export the API instance for use in other services
export const apiService = api 