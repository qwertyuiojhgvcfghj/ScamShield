/**
 * ScamShield Pro - Core JavaScript
 * Clean, functional, no unnecessary effects
 */

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
  initMobileMenu();
  initRevealAnimations();
  initDemoForm();
  initSmoothScroll();
  initAuthForms();
});

// ============================================
// AUTHENTICATION FORMS
// ============================================

function initAuthForms() {
  const loginForm = document.getElementById('loginForm');
  const signupForm = document.getElementById('signupForm');
  
  // Login Form Handler - Skip if login.html has its own inline handler
  // The login.html page has specific logic for admin vs user redirection
  // so we don't attach a handler here to avoid conflicts
  
  // Signup Form Handler
  if (signupForm) {
    signupForm.addEventListener('submit', function(e) {
      e.preventDefault();
      
      const name = document.getElementById('fullName')?.value.trim();
      const email = document.getElementById('email')?.value.trim();
      const password = document.getElementById('password')?.value;
      const confirmPassword = document.getElementById('confirmPassword')?.value;
      
      if (!name || !email || !password) {
        showToast('Please fill in all fields', 'error');
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
      
      if (confirmPassword && password !== confirmPassword) {
        showToast('Passwords do not match', 'error');
        return;
      }
      
      // Store user data
      const userData = {
        email: email,
        name: name,
        plan: 'Free Trial',
        loggedInAt: new Date().toISOString()
      };
      
      localStorage.setItem('scamshield_user', JSON.stringify(userData));
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('userEmail', email);
      localStorage.setItem('userName', name);
      
      showToast('Account created! Redirecting...', 'success');
      
      // Redirect to dashboard
      setTimeout(() => {
        window.location.href = './dashboard.html';
      }, 1000);
    });
  }
  
  // Password toggle functionality
  document.querySelectorAll('.password-toggle').forEach(btn => {
    btn.addEventListener('click', function() {
      const wrapper = this.closest('.password-wrapper');
      const input = wrapper?.querySelector('input');
      if (input) {
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        this.innerHTML = isPassword 
          ? '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'
          : '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
      }
    });
  });
}

// ============================================
// MOBILE MENU
// ============================================

function initMobileMenu() {
  const toggle = document.querySelector('.menu-toggle');
  const mobileNav = document.getElementById('mobileNav');
  
  if (!toggle || !mobileNav) return;
  
  toggle.addEventListener('click', function() {
    mobileNav.classList.toggle('active');
    toggle.classList.toggle('active');
    document.body.style.overflow = mobileNav.classList.contains('active') ? 'hidden' : '';
  });
  
  // Close on link click
  mobileNav.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      mobileNav.classList.remove('active');
      toggle.classList.remove('active');
      document.body.style.overflow = '';
    });
  });
}

// ============================================
// REVEAL ANIMATIONS - Single strong entrance
// ============================================

function initRevealAnimations() {
  const reveals = document.querySelectorAll('.reveal, .stagger, .text-reveal');
  
  if (!reveals.length) return;
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('active');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.15,
    rootMargin: '0px 0px -50px 0px'
  });
  
  reveals.forEach(el => observer.observe(el));
  
  // Trigger hero animations immediately
  document.querySelectorAll('.hero .text-reveal, .hero .stagger').forEach(el => {
    setTimeout(() => el.classList.add('active'), 100);
  });
}

// ============================================
// SMOOTH SCROLL
// ============================================

function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      
      const target = document.querySelector(targetId);
      if (!target) return;
      
      e.preventDefault();
      const headerHeight = document.querySelector('.site-header')?.offsetHeight || 0;
      const targetPosition = target.offsetTop - headerHeight - 20;
      
      window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
      });
    });
  });
}

// ============================================
// DEMO FORM
// ============================================

const sampleMessages = [
  "🎉 CONGRATULATIONS! You've been selected to receive a $10,000 Walmart Gift Card! Click here NOW to claim: bit.ly/free-gift-2024 Reply STOP to unsubscribe",
  "URGENT: Your Bank of America account has been suspended due to suspicious activity. Verify your identity immediately at secure-boa-verify.com or your account will be permanently closed.",
  "Hi! I saw your profile on LinkedIn and I'm impressed. I have an amazing remote job opportunity - work from home and earn $5000/week! No experience needed. Reply for details."
];

function initDemoForm() {
  const form = document.getElementById('demoForm');
  if (!form) return;
  
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    analyzeDemo();
  });
}

function loadSample(index) {
  const input = document.getElementById('demoInput');
  if (input && sampleMessages[index]) {
    input.value = sampleMessages[index];
    input.focus();
  }
}

async function analyzeDemo() {
  const input = document.getElementById('demoInput');
  const btn = document.querySelector('#demoForm button[type="submit"]');
  const resultContainer = document.getElementById('demoResult');
  
  const message = input?.value.trim();
  if (!message) {
    showToast('Please enter a message to analyze', 'error');
    return;
  }
  
  // Show loading state
  btn?.classList.add('loading');
  
  // Simulate analysis delay
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  // Perform local analysis
  const analysis = analyzeMessage(message);
  
  // Display result
  displayResult(analysis, resultContainer);
  
  // Reset button
  btn?.classList.remove('loading');
}

function analyzeMessage(message) {
  const text = message.toLowerCase();
  let score = 0;
  const indicators = [];
  
  // Check for urgency
  const urgencyWords = ['urgent', 'immediately', 'now', 'fast', 'hurry', 'limited time', 'expires', 'act now'];
  if (urgencyWords.some(word => text.includes(word))) {
    score += 20;
    indicators.push('Urgency tactics detected');
  }
  
  // Check for money/prizes
  const moneyWords = ['win', 'winner', 'prize', 'reward', 'gift card', 'free money', 'lottery', 'jackpot', 'million', 'thousand'];
  if (moneyWords.some(word => text.includes(word))) {
    score += 25;
    indicators.push('Unrealistic rewards promised');
  }
  
  // Check for suspicious links
  const linkPatterns = ['bit.ly', 'tinyurl', 'click here', 'verify', 'confirm', 'secure-', 'login-'];
  if (linkPatterns.some(pattern => text.includes(pattern))) {
    score += 20;
    indicators.push('Suspicious link pattern');
  }
  
  // Check for personal info requests
  const infoWords = ['ssn', 'social security', 'password', 'credit card', 'bank account', 'verify your', 'confirm your'];
  if (infoWords.some(word => text.includes(word))) {
    score += 25;
    indicators.push('Requests sensitive information');
  }
  
  // Check for impersonation
  const impersonationWords = ['irs', 'fbi', 'bank of america', 'paypal', 'amazon', 'microsoft', 'apple support'];
  if (impersonationWords.some(word => text.includes(word))) {
    score += 20;
    indicators.push('Potential brand impersonation');
  }
  
  // Check for emotional manipulation
  const emotionWords = ['congratulations', 'selected', 'exclusive', 'special', 'lucky', 'chosen'];
  if (emotionWords.some(word => text.includes(word))) {
    score += 15;
    indicators.push('Emotional manipulation');
  }
  
  // Check for threats
  const threatWords = ['suspended', 'closed', 'terminated', 'legal action', 'arrest', 'blocked'];
  if (threatWords.some(word => text.includes(word))) {
    score += 20;
    indicators.push('Threatening language');
  }
  
  // Check for grammatical issues
  const grammarIssues = ['kindly', 'dear valued', 'dear customer', 'dear friend'];
  if (grammarIssues.some(issue => text.includes(issue))) {
    score += 10;
    indicators.push('Unusual phrasing');
  }
  
  score = Math.min(score, 100);
  
  let riskLevel, verdict;
  if (score >= 70) {
    riskLevel = 'danger';
    verdict = 'HIGH RISK - Likely a Scam';
  } else if (score >= 40) {
    riskLevel = 'warning';
    verdict = 'MEDIUM RISK - Be Cautious';
  } else {
    riskLevel = 'safe';
    verdict = 'LOW RISK - Appears Legitimate';
  }
  
  return { score, riskLevel, verdict, indicators };
}

function displayResult(analysis, container) {
  if (!container) return;
  
  container.innerHTML = `
    <div class="result-card card ${analysis.riskLevel}">
      <div class="result-score">${analysis.score}%</div>
      <div class="result-verdict">${analysis.verdict}</div>
      ${analysis.indicators.length > 0 ? `
        <div class="result-details">
          <h4>Detected Indicators</h4>
          <ul>
            ${analysis.indicators.map(i => `<li>• ${i}</li>`).join('')}
          </ul>
        </div>
      ` : ''}
    </div>
  `;
  
  container.classList.add('active');
  container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ============================================
// TOAST NOTIFICATIONS
// ============================================

function showToast(message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${message}</span>
    <button onclick="this.parentElement.remove()" style="background:none;border:none;color:inherit;cursor:pointer;margin-left:auto;">✕</button>
  `;
  
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'toastOut 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Add toast out animation
const toastStyle = document.createElement('style');
toastStyle.textContent = `
  @keyframes toastOut {
    to {
      transform: translateX(100%);
      opacity: 0;
    }
  }
`;
document.head.appendChild(toastStyle);

// ============================================
// FORM VALIDATION
// ============================================

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePassword(password) {
  return password.length >= 8;
}

function showFormError(inputId, message) {
  const input = document.getElementById(inputId);
  const errorEl = document.getElementById(`${inputId}Error`);
  
  if (input) input.classList.add('error');
  if (errorEl) errorEl.textContent = message;
}

function clearFormErrors(formId) {
  const form = document.getElementById(formId);
  if (!form) return;
  
  form.querySelectorAll('.form-input').forEach(input => {
    input.classList.remove('error');
  });
  
  form.querySelectorAll('.form-error').forEach(error => {
    error.textContent = '';
  });
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function formatNumber(num) {
  return new Intl.NumberFormat().format(num);
}

function formatCurrency(num) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0
  }).format(num);
}

function formatDate(date) {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }).format(new Date(date));
}

// ============================================
// SESSION MANAGEMENT
// ============================================

function isLoggedIn() {
  return localStorage.getItem('isLoggedIn') === 'true';
}

function getUserRole() {
  return localStorage.getItem('userRole') || 'user';
}

function getUserName() {
  return localStorage.getItem('userName') || 'User';
}

function logout() {
  localStorage.removeItem('isLoggedIn');
  localStorage.removeItem('userRole');
  localStorage.removeItem('userName');
  localStorage.removeItem('userEmail');
  localStorage.removeItem('scamshield_user');
  window.location.href = 'index.html';
}

// ============================================
// MULTI-STEP SIGNUP FORM
// ============================================

function nextStep(step) {
  const form = document.getElementById('signupForm');
  if (!form) return;
  
  // Validate current step before moving
  const currentStep = document.querySelector('.form-step.active');
  const inputs = currentStep?.querySelectorAll('input[required]');
  
  let isValid = true;
  inputs?.forEach(input => {
    if (!input.value.trim()) {
      input.classList.add('error');
      isValid = false;
    } else {
      input.classList.remove('error');
    }
  });
  
  // Check password match on step 1
  if (currentStep?.dataset.step === '1') {
    const password = document.getElementById('password')?.value;
    const confirm = document.getElementById('confirmPassword')?.value;
    if (password !== confirm) {
      showToast('Passwords do not match', 'error');
      return;
    }
    if (password.length < 8) {
      showToast('Password must be at least 8 characters', 'error');
      return;
    }
  }
  
  if (!isValid) {
    showToast('Please fill in all required fields', 'error');
    return;
  }
  
  // Hide all steps
  document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.step-indicator').forEach(s => s.classList.remove('active'));
  
  // Show target step
  document.querySelector(`.form-step[data-step="${step}"]`)?.classList.add('active');
  
  // Mark steps up to current as active
  for (let i = 1; i <= step; i++) {
    document.querySelector(`.step-indicator[data-step="${i}"]`)?.classList.add('active');
  }
}

function prevStep(step) {
  // Hide all steps
  document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.step-indicator').forEach(s => s.classList.remove('active'));
  
  // Show target step
  document.querySelector(`.form-step[data-step="${step}"]`)?.classList.add('active');
  
  // Mark steps up to current as active
  for (let i = 1; i <= step; i++) {
    document.querySelector(`.step-indicator[data-step="${i}"]`)?.classList.add('active');
  }
}

// ============================================
// EXPORTS
// ============================================

window.loadSample = loadSample;
window.showToast = showToast;
window.logout = logout;
window.validateEmail = validateEmail;
window.validatePassword = validatePassword;
window.showFormError = showFormError;
window.clearFormErrors = clearFormErrors;
window.nextStep = nextStep;
window.prevStep = prevStep;