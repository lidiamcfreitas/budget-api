import axios from 'axios';

// Create axios instance with custom config
const api = axios.create({
baseURL: process.env.VUE_APP_API_URL || 'http://localhost:8000',
headers: {
    'Content-Type': 'application/json',
},
timeout: 10000
});

// Request interceptor
api.interceptors.request.use(
(config) => {
    // Add auth token if available
    const token = localStorage.getItem('token');
    if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
},
(error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
(response) => response.data,
(error) => {
    if (error.response) {
    // Handle specific HTTP errors
    switch (error.response.status) {
        case 401:
        // Handle unauthorized
        break;
        case 404:
        // Handle not found
        break;
        default:
        // Handle other errors
        break;
    }
    }
    return Promise.reject(error);
}
);

// API service methods
export default {
    // GET request
    get: (endpoint, params = {}) => api.get(endpoint, { params }),

    // POST request
    post: (endpoint, data = {}) => api.post(endpoint, data),

    // PUT request
    put: (endpoint, data = {}) => api.put(endpoint, data),

    // DELETE request
    delete: (endpoint) => api.delete(endpoint)
}
