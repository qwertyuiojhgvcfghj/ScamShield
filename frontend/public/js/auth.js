/**
 * ScamShield Pro - Authentication Integration
 * Integrates login/signup forms with the backend API
 * Includes Google and GitHub OAuth support
 */

// ============================================
// GOOGLE OAUTH CONFIGURATION
// Get your Client ID at: https://console.cloud.google.com/apis/credentials
// ============================================
const GOOGLE_CLIENT_ID = ''; // Add your Google Client ID here

// ============================================
// AUTH FUNCTIONS
// ============================================

/**
 * Handle login form submission
 */
async function handleLogin(event) {
  event.preventDefault();
  
  const form = event.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalBtnText = submitBtn.innerHTML;
  
  const email = document.getElementById('email')?.value.trim();
  const password = document.getElementById('password')?.value;
  
  // Validation
  if (!email || !password) {
    showToast('Please fill in all fields', 'error');
    return;
  }
  
  if (!validateEmail(email)) {
    showToast('Please enter a valid email address', 'error');
    return;
  }
  
  // Show loading state
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> Logging in...';
  
  try {
    // Call API
    const response = await api.login(email, password);
    
    showToast('Login successful! Redirecting...', 'success');
    
    // Redirect to dashboard
    setTimeout(() => {
      window.location.href = './dashboard.html';
    }, 1000);
    
  } catch (error) {
    showToast(error.message || 'Login failed. Please check your credentials.', 'error');
    
    // Reset button
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalBtnText;
  }
}

/**
 * Handle signup form submission
 */
async function handleSignup(event) {
  event.preventDefault();
  
  const form = event.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalBtnText = submitBtn.innerHTML;
  
  const fullName = document.getElementById('fullName')?.value.trim();
  const email = document.getElementById('email')?.value.trim();
  const password = document.getElementById('password')?.value;
  const confirmPassword = document.getElementById('confirmPassword')?.value;
  const phone = document.getElementById('phone')?.value.trim() || null;
  
  // Validation
  if (!fullName || !email || !password) {
    showToast('Please fill in all required fields', 'error');
    return;
  }
  
  if (!validateEmail(email)) {
    showToast('Please enter a valid email address', 'error');
    return;
  }
  
  if (password.length < 8) {
    showToast('Password must be at least 8 characters', 'error');
    return;
  }
  
  // Check for uppercase, lowercase, and digit
  if (!/[A-Z]/.test(password)) {
    showToast('Password must contain at least one uppercase letter', 'error');
    return;
  }
  
  if (!/[a-z]/.test(password)) {
    showToast('Password must contain at least one lowercase letter', 'error');
    return;
  }
  
  if (!/\d/.test(password)) {
    showToast('Password must contain at least one digit', 'error');
    return;
  }
  
  if (confirmPassword && password !== confirmPassword) {
    showToast('Passwords do not match', 'error');
    return;
  }
  
  // Show loading state
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> Creating account...';
  
  try {
    // Call API
    const response = await api.register(email, password, fullName, phone);
    
    showToast('Account created successfully! Redirecting...', 'success');
    
    // Redirect to dashboard
    setTimeout(() => {
      window.location.href = './dashboard.html';
    }, 1000);
    
  } catch (error) {
    showToast(error.message || 'Registration failed. Please try again.', 'error');
    
    // Reset button
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalBtnText;
  }
}

/**
 * Handle logout
 */
async function handleLogout() {
  try {
    await api.logout();
  } catch (e) {
    // Ignore errors
  }
  
  showToast('Logged out successfully', 'success');
  
  setTimeout(() => {
    window.location.href = './login.html';
  }, 500);
}

/**
 * Handle forgot password form
 */
async function handleForgotPassword(event) {
  event.preventDefault();
  
  const form = event.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalBtnText = submitBtn.innerHTML;
  
  const email = document.getElementById('email')?.value.trim();
  
  if (!email) {
    showToast('Please enter your email address', 'error');
    return;
  }
  
  if (!validateEmail(email)) {
    showToast('Please enter a valid email address', 'error');
    return;
  }
  
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> Sending...';
  
  try {
    await api.forgotPassword(email);
    showToast('If the email exists, a password reset link has been sent.', 'success');
    
    // Reset form
    form.reset();
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalBtnText;
    
  } catch (error) {
    showToast(error.message || 'Failed to send reset email', 'error');
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalBtnText;
  }
}

/**
 * Check if user is authenticated
 */
function checkAuth() {
  if (!api.isAuthenticated()) {
    window.location.href = './login.html';
    return false;
  }
  return true;
}

/**
 * Validate email format
 */
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
  // Remove existing toasts
  document.querySelectorAll('.toast').forEach(t => t.remove());
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-content">
      <span class="toast-icon">${getToastIcon(type)}</span>
      <span class="toast-message">${message}</span>
    </div>
  `;
  
  document.body.appendChild(toast);
  
  // Animate in
  setTimeout(() => toast.classList.add('show'), 10);
  
  // Remove after delay
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function getToastIcon(type) {
  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };
  return icons[type] || icons.info;
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
  // Initialize login form
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }
  
  // Initialize signup form
  const signupForm = document.getElementById('signupForm');
  if (signupForm) {
    signupForm.addEventListener('submit', handleSignup);
  }
  
  // Initialize forgot password form
  const forgotForm = document.getElementById('forgotPasswordForm');
  if (forgotForm) {
    forgotForm.addEventListener('submit', handleForgotPassword);
  }
  
  // Logout button
  document.querySelectorAll('[data-action="logout"]').forEach(btn => {
    btn.addEventListener('click', handleLogout);
  });
  
  // Initialize Google OAuth buttons
  initGoogleAuth();
  
  // Initialize GitHub OAuth buttons
  initGitHubAuth();
  
  // Handle OAuth callback tokens in URL hash
  handleOAuthCallback();
  
  // Check if on protected page
  const isProtectedPage = document.body.classList.contains('protected-page');
  if (isProtectedPage) {
    checkAuth();
  }
  
  // Redirect if already logged in (on login/signup pages)
  const isAuthPage = document.body.classList.contains('auth-page');
  if (isAuthPage && api.isAuthenticated()) {
    window.location.href = './dashboard.html';
  }
});

// ============================================
// GOOGLE OAUTH
// ============================================

/**
 * Initialize Google OAuth
 */
function initGoogleAuth() {
  // Find all Google sign-in buttons
  const googleButtons = document.querySelectorAll('.social-btn-google, .social-btn:has(svg path[fill="#4285F4"])');
  
  googleButtons.forEach(btn => {
    // Check if it's actually the Google button by looking at the SVG or text
    if (btn.textContent.includes('Google') || btn.querySelector('svg path[fill="#4285F4"]')) {
      btn.addEventListener('click', handleGoogleLogin);
    }
  });
  
  // Also handle buttons that just say "Google"
  document.querySelectorAll('.social-btn').forEach(btn => {
    if (btn.textContent.trim().includes('Google')) {
      btn.removeEventListener('click', handleGoogleLogin);
      btn.addEventListener('click', handleGoogleLogin);
    }
  });
}

/**
 * Handle Google login button click
 */
async function handleGoogleLogin(event) {
  event.preventDefault();
  
  const btn = event.currentTarget;
  const originalHtml = btn.innerHTML;
  
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Connecting...';
  
  try {
    // Check if Google Client ID is configured
    if (GOOGLE_CLIENT_ID) {
      // Use Google Identity Services (recommended)
      await signInWithGoogleGSI();
    } else {
      // Fallback to backend OAuth flow
      const response = await api.getGoogleAuthUrl();
      if (response.auth_url) {
        window.location.href = response.auth_url;
      } else {
        throw new Error('Google OAuth is not configured');
      }
    }
  } catch (error) {
    showToast(error.message || 'Google login failed', 'error');
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

/**
 * Google Identity Services sign-in
 */
function signInWithGoogleGSI() {
  return new Promise((resolve, reject) => {
    if (!window.google) {
      // Load Google Identity Services script
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => initGoogleGSI(resolve, reject);
      script.onerror = () => reject(new Error('Failed to load Google Sign-In'));
      document.head.appendChild(script);
    } else {
      initGoogleGSI(resolve, reject);
    }
  });
}

function initGoogleGSI(resolve, reject) {
  google.accounts.id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    callback: async (response) => {
      try {
        // Send ID token to backend
        const result = await api.googleTokenLogin(response.credential);
        showToast('Google login successful! Redirecting...', 'success');
        setTimeout(() => {
          window.location.href = './dashboard.html';
        }, 1000);
        resolve(result);
      } catch (error) {
        reject(error);
      }
    },
  });
  
  // Trigger the One Tap prompt
  google.accounts.id.prompt((notification) => {
    if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
      // One Tap not displayed, use redirect flow
      google.accounts.oauth2.initCodeClient({
        client_id: GOOGLE_CLIENT_ID,
        scope: 'email profile',
        callback: async (response) => {
          if (response.code) {
            try {
              const result = await api.googleCodeLogin(response.code);
              showToast('Google login successful! Redirecting...', 'success');
              setTimeout(() => {
                window.location.href = './dashboard.html';
              }, 1000);
              resolve(result);
            } catch (error) {
              reject(error);
            }
          }
        },
      }).requestCode();
    }
  });
}

// ============================================
// GITHUB OAUTH
// ============================================

/**
 * Initialize GitHub OAuth
 */
function initGitHubAuth() {
  document.querySelectorAll('.social-btn').forEach(btn => {
    if (btn.textContent.trim().includes('GitHub')) {
      btn.addEventListener('click', handleGitHubLogin);
    }
  });
}

/**
 * Handle GitHub login button click
 */
async function handleGitHubLogin(event) {
  event.preventDefault();
  
  const btn = event.currentTarget;
  const originalHtml = btn.innerHTML;
  
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Connecting...';
  
  try {
    const response = await api.getGitHubAuthUrl();
    if (response.auth_url) {
      window.location.href = response.auth_url;
    } else {
      throw new Error('GitHub OAuth is not configured');
    }
  } catch (error) {
    showToast(error.message || 'GitHub login failed', 'error');
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

// ============================================
// OAUTH CALLBACK HANDLER
// ============================================

/**
 * Handle OAuth callback with tokens in URL
 */
function handleOAuthCallback() {
  // Check URL hash for tokens (from OAuth callback)
  const hash = window.location.hash.substring(1);
  if (hash) {
    const params = new URLSearchParams(hash);
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');
    
    if (accessToken) {
      // Store tokens
      api.setTokens(accessToken, refreshToken);
      
      // Clean up URL
      window.history.replaceState(null, null, window.location.pathname);
      
      showToast('Login successful! Redirecting...', 'success');
      
      // Fetch user info and redirect
      api.getProfile().then(user => {
        if (user) {
          api.setUser(user);
        }
        setTimeout(() => {
          window.location.href = './dashboard.html';
        }, 1000);
      }).catch(() => {
        setTimeout(() => {
          window.location.href = './dashboard.html';
        }, 1000);
      });
      
      return;
    }
  }
  
  // Check URL query for errors
  const urlParams = new URLSearchParams(window.location.search);
  const error = urlParams.get('error');
  if (error) {
    showToast(decodeURIComponent(error), 'error');
    // Clean up URL
    window.history.replaceState(null, null, window.location.pathname);
  }
}

// Add CSS for toast and spinner
const style = document.createElement('style');
style.textContent = `
  .toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    padding: 16px 20px;
    background: #1a1a1a;
    color: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    z-index: 10000;
    transform: translateY(100px);
    opacity: 0;
    transition: all 0.3s ease;
  }
  
  .toast.show {
    transform: translateY(0);
    opacity: 1;
  }
  
  .toast-content {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .toast-icon {
    font-size: 18px;
  }
  
  .toast-success { border-left: 4px solid #22c55e; }
  .toast-success .toast-icon { color: #22c55e; }
  
  .toast-error { border-left: 4px solid #ef4444; }
  .toast-error .toast-icon { color: #ef4444; }
  
  .toast-warning { border-left: 4px solid #f59e0b; }
  .toast-warning .toast-icon { color: #f59e0b; }
  
  .toast-info { border-left: 4px solid #3b82f6; }
  .toast-info .toast-icon { color: #3b82f6; }
  
  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255,255,255,0.3);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 0.8s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  .social-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
`;
document.head.appendChild(style);
