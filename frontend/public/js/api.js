/**
 * ScamShield Pro - API Service
 * Handles all communication with the backend API
 */

// ============================================
// API CONFIGURATION
// ============================================

// Determine API URL based on environment
const getApiBaseUrl = () => {
  // Check for custom API URL (set via environment or config)
  if (window.SCAMSHIELD_API_URL) {
    return window.SCAMSHIELD_API_URL;
  }
  
  const hostname = window.location.hostname;
  
  // Local development
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000/api/v1';
  }
  
  // Vercel preview deployments
  if (hostname.includes('vercel.app')) {
    return 'https://scamshield-k6ww.onrender.com/api/v1';
  }
  
  // Production (custom domain)
  return 'https://scamshield-k6ww.onrender.com/api/v1';
};

const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  
  // Token storage keys
  ACCESS_TOKEN_KEY: 'scamshield_access_token',
  REFRESH_TOKEN_KEY: 'scamshield_refresh_token',
  USER_KEY: 'scamshield_user',
};

// Log the API URL in development for debugging
if (window.location.hostname === 'localhost') {
  console.log('🔌 API Base URL:', API_CONFIG.BASE_URL);
}

// ============================================
// API SERVICE CLASS
// ============================================

class ApiService {
  constructor() {
    this.baseUrl = API_CONFIG.BASE_URL;
  }

  // --- Token Management ---
  
  getAccessToken() {
    return localStorage.getItem(API_CONFIG.ACCESS_TOKEN_KEY);
  }
  
  getRefreshToken() {
    return localStorage.getItem(API_CONFIG.REFRESH_TOKEN_KEY);
  }
  
  setTokens(accessToken, refreshToken) {
    localStorage.setItem(API_CONFIG.ACCESS_TOKEN_KEY, accessToken);
    if (refreshToken) {
      localStorage.setItem(API_CONFIG.REFRESH_TOKEN_KEY, refreshToken);
    }
  }
  
  clearTokens() {
    localStorage.removeItem(API_CONFIG.ACCESS_TOKEN_KEY);
    localStorage.removeItem(API_CONFIG.REFRESH_TOKEN_KEY);
    localStorage.removeItem(API_CONFIG.USER_KEY);
    localStorage.removeItem('isLoggedIn');
  }
  
  getUser() {
    const userData = localStorage.getItem(API_CONFIG.USER_KEY);
    return userData ? JSON.parse(userData) : null;
  }
  
  setUser(user) {
    localStorage.setItem(API_CONFIG.USER_KEY, JSON.stringify(user));
    localStorage.setItem('isLoggedIn', 'true');
    localStorage.setItem('userEmail', user.email);
    localStorage.setItem('userName', user.full_name || user.email.split('@')[0]);
    localStorage.setItem('userRole', user.role || 'user');
  }
  
  isAuthenticated() {
    return !!this.getAccessToken();
  }

  // --- HTTP Methods ---
  
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    // Add auth token if available
    const token = this.getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });
      
      // Handle 401 - try to refresh token
      if (response.status === 401 && !options._isRetry) {
        // Check if using demo token - don't redirect, just throw error
        const currentToken = this.getAccessToken();
        if (currentToken && currentToken.startsWith('demo_token_')) {
          // Demo mode - don't redirect, just throw error for caller to handle
          throw new Error('Demo mode - API not available');
        }
        
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          return this.request(endpoint, { ...options, _isRetry: true });
        } else {
          this.clearTokens();
          window.location.href = '/login.html';
          throw new Error('Session expired. Please login again.');
        }
      }
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Request failed');
      }
      
      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }
  
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }
  
  async post(endpoint, body) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }
  
  async put(endpoint, body) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }
  
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // --- Auth Endpoints ---
  
  async register(email, password, fullName, phone = null) {
    const data = await this.post('/auth/register', {
      email,
      password,
      full_name: fullName,
      phone,
    });
    
    if (data.tokens) {
      this.setTokens(data.tokens.access_token, data.tokens.refresh_token);
    }
    if (data.user) {
      this.setUser(data.user);
    }
    
    return data;
  }
  
  async login(email, password) {
    const data = await this.post('/auth/login', { email, password });
    
    if (data.tokens) {
      this.setTokens(data.tokens.access_token, data.tokens.refresh_token);
    }
    if (data.user) {
      this.setUser(data.user);
    }
    
    return data;
  }
  
  async logout() {
    try {
      await this.post('/auth/logout', {});
    } catch (e) {
      // Ignore errors on logout
    }
    this.clearTokens();
  }
  
  async refreshAccessToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;
    
    try {
      const data = await this.post('/auth/refresh', {
        refresh_token: refreshToken,
      });
      
      if (data.access_token) {
        this.setTokens(data.access_token, data.refresh_token);
        return true;
      }
    } catch (e) {
      console.error('Token refresh failed:', e);
    }
    
    return false;
  }
  
  async forgotPassword(email) {
    return this.post('/auth/forgot-password', { email });
  }
  
  async resetPassword(token, newPassword) {
    return this.post('/auth/reset-password', {
      token,
      new_password: newPassword,
    });
  }
  
  async changePassword(currentPassword, newPassword) {
    return this.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  // --- User Endpoints ---
  
  async getProfile() {
    return this.get('/users/me');
  }
  
  async updateProfile(data) {
    return this.put('/users/me', data);
  }
  
  async getSettings() {
    return this.get('/users/me/settings');
  }
  
  async updateSettings(data) {
    return this.put('/users/me/settings', data);
  }
  
  async getStats() {
    return this.get('/users/me/stats');
  }

  // --- Scan Endpoints ---
  
  async scanMessage(messageText, channel = 'SMS', senderInfo = null) {
    return this.post('/scans/', {
      message_text: messageText,
      channel,
      sender_info: senderInfo,
    });
  }
  
  async getScanHistory(page = 1, limit = 20, scamsOnly = null) {
    let url = `/scans/history?page=${page}&limit=${limit}`;
    if (scamsOnly !== null) {
      url += `&scams_only=${scamsOnly}`;
    }
    return this.get(url);
  }
  
  async getScanDetail(scanId) {
    return this.get(`/scans/${scanId}`);
  }
  
  async addScanFeedback(scanId, feedback, comment = null) {
    return this.post(`/scans/${scanId}/feedback`, { feedback, comment });
  }

  // --- Threat Endpoints ---
  
  async getThreats(page = 1, limit = 20, status = null) {
    let url = `/threats/?page=${page}&limit=${limit}`;
    if (status) {
      url += `&status=${status}`;
    }
    return this.get(url);
  }
  
  async getThreatDetail(threatId) {
    return this.get(`/threats/${threatId}`);
  }
  
  async reportThreat(messageText, senderInfo = null, channel = 'SMS', threatType = null, notes = null) {
    return this.post('/threats/report', {
      message_text: messageText,
      sender_info: senderInfo,
      channel,
      threat_type: threatType,
      notes,
    });
  }
  
  async whitelistThreat(threatId) {
    return this.post(`/threats/${threatId}/whitelist`, {});
  }
  
  async deleteThreat(threatId) {
    return this.delete(`/threats/${threatId}`);
  }

  // --- Analytics Endpoints ---
  
  async getDashboardStats() {
    return this.get('/analytics/dashboard');
  }
  
  async getTrends(days = 30) {
    return this.get(`/analytics/trends?days=${days}`);
  }
  
  async getScamBreakdown() {
    return this.get('/analytics/breakdown');
  }
  
  async getGlobalStats() {
    // This endpoint doesn't require auth
    return this.request('/analytics/global', { method: 'GET' });
  }

  // --- Subscription Endpoints ---
  
  async getPlans() {
    return this.get('/subscriptions/plans');
  }
  
  async getSubscription() {
    return this.get('/subscriptions/me');
  }
  
  async subscribe(planId, billingPeriod = 'monthly') {
    return this.post('/subscriptions/subscribe', {
      plan_id: planId,
      billing_period: billingPeriod,
    });
  }
  
  async cancelSubscription(reason = null) {
    return this.post('/subscriptions/cancel', { reason });
  }
  
  async getUsage() {
    return this.get('/subscriptions/usage');
  }

  // --- OAuth Endpoints ---
  
  async getGoogleAuthUrl() {
    return this.get('/auth/google');
  }
  
  async googleTokenLogin(idToken) {
    const data = await this.post('/auth/google/token', { id_token: idToken });
    
    if (data.tokens) {
      this.setTokens(data.tokens.access_token, data.tokens.refresh_token);
    }
    if (data.user) {
      this.setUser(data.user);
    }
    
    return data;
  }
  
  async googleCodeLogin(code, redirectUri = null) {
    const payload = { code };
    if (redirectUri) {
      payload.redirect_uri = redirectUri;
    }
    
    const data = await this.post('/auth/google/code', payload);
    
    if (data.tokens) {
      this.setTokens(data.tokens.access_token, data.tokens.refresh_token);
    }
    if (data.user) {
      this.setUser(data.user);
    }
    
    return data;
  }
  
  async getGitHubAuthUrl() {
    return this.get('/auth/github');
  }
  
  async githubCodeLogin(code) {
    const data = await this.post('/auth/github/code', { code });
    
    if (data.tokens) {
      this.setTokens(data.tokens.access_token, data.tokens.refresh_token);
    }
    if (data.user) {
      this.setUser(data.user);
    }
    
    return data;
  }
}

// ============================================
// GLOBAL INSTANCE
// ============================================

const api = new ApiService();

// Export for use in other scripts
window.ScamShieldAPI = api;
