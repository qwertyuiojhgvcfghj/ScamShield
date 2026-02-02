/**
 * ScamShield Pro - X-Ray Dashboard
 * Interactive JavaScript
 */

// ==========================================
// STATE
// ==========================================
const state = {
  user: null,
  currentView: 'dashboard',
  scans: [],
  threats: []
};

// Mock Data
const mockScans = [
  { id: 1, content: "Congratulations! You've won $1,000,000 in our international lottery. Click here to claim...", source: 'Email', isThreat: true, threatType: 'lottery', risk: 95, timestamp: new Date(Date.now() - 300000) },
  { id: 2, content: "Your Amazon account has been suspended. Verify your identity immediately...", source: 'Email', isThreat: true, threatType: 'phishing', risk: 98, timestamp: new Date(Date.now() - 900000) },
  { id: 3, content: "Meeting reminder: Quarterly review tomorrow at 3pm", source: 'Email', isThreat: false, threatType: null, risk: 2, timestamp: new Date(Date.now() - 1800000) },
  { id: 4, content: "Hello dear, I am Princess Amara from Nigeria. I have $5 million to share with you...", source: 'SMS', isThreat: true, threatType: 'romance', risk: 92, timestamp: new Date(Date.now() - 3600000) },
  { id: 5, content: "Your Microsoft subscription has expired. Call this number immediately to renew...", source: 'Email', isThreat: true, threatType: 'tech', risk: 88, timestamp: new Date(Date.now() - 7200000) },
  { id: 6, content: "Invoice #45678 attached for your recent order", source: 'Email', isThreat: false, threatType: null, risk: 5, timestamp: new Date(Date.now() - 10800000) },
  { id: 7, content: "URGENT: Your bank account will be frozen. Update your information now...", source: 'SMS', isThreat: true, threatType: 'phishing', risk: 96, timestamp: new Date(Date.now() - 14400000) },
];

// Scam detection patterns
const scamPatterns = {
  urgency: ['urgent', 'immediately', 'now', 'hurry', 'limited time', 'act fast', 'don\'t delay'],
  money: ['won', 'lottery', 'million', 'prize', 'inheritance', 'free money', 'cash'],
  fear: ['suspended', 'frozen', 'locked', 'verify', 'confirm', 'unauthorized', 'illegal'],
  authority: ['bank', 'irs', 'amazon', 'microsoft', 'apple', 'google', 'government'],
  personal: ['dear', 'beloved', 'princess', 'prince', 'widow', 'dying wish'],
  action: ['click here', 'call now', 'send', 'wire', 'transfer', 'bank details', 'password']
};

// ==========================================
// INITIALIZATION
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  // Check auth using API service
  const api = window.ScamShieldAPI;
  
  if (!api || !api.isAuthenticated()) {
    window.location.href = './login.html';
    return;
  }
  
  state.user = api.getUser();
  
  // If admin user, show admin panel link in sidebar (don't auto-redirect)
  if (state.user && state.user.role === 'admin') {
    console.log('Admin user detected - showing admin panel link');
    const adminLink = document.getElementById('adminPanelLink');
    if (adminLink) {
      adminLink.style.display = 'flex';
    }
  }
  
  // Load data from API (with fallback to mock data)
  try {
    await loadDashboardData();
  } catch (error) {
    console.warn('Failed to load API data, using mock data:', error);
    state.scans = mockScans;
    state.threats = mockScans.filter(s => s.isThreat);
  }
  
  // Setup
  setupUserInfo();
  setupNavigation();
  setupXrayScanner();
  setupQuickScan();
  setupCodeTabs();
  
  // Populate content
  populateActivityFeed();
  populateRadarBlips();
  populateTimeline();
  populateEvidenceBoard();
  
  // Load dashboard stats
  await loadDashboardStats();
  
  // Check for existing API key
  checkExistingApiKey();
  
  // Initialize API Keys table
  if (typeof renderApiKeysTable === 'function') {
    renderApiKeysTable();
  }
  
  // Start animations
  animateCounters();
}

// ==========================================
// API DATA LOADING
// ==========================================
async function loadDashboardData() {
  const api = window.ScamShieldAPI;
  
  // Load scan history
  try {
    const historyResponse = await api.getScanHistory(1, 10);
    if (historyResponse && historyResponse.scans) {
      state.scans = historyResponse.scans.map(scan => ({
        id: scan.id,
        content: scan.message_text,
        source: scan.channel || 'SMS',
        isThreat: scan.is_scam,
        threatType: scan.scam_type,
        risk: Math.round(scan.risk_score * 100),
        timestamp: new Date(scan.created_at)
      }));
    }
  } catch (e) {
    console.warn('Could not load scan history:', e);
  }
  
  // Load threats
  try {
    const threatsResponse = await api.getThreats(1, 10, 'active');
    if (threatsResponse && threatsResponse.threats) {
      state.threats = threatsResponse.threats.map(threat => ({
        id: threat.id,
        content: threat.indicator || threat.message,
        source: threat.indicator_type || 'Unknown',
        isThreat: true,
        threatType: threat.threat_type,
        risk: Math.round(threat.severity * 100),
        timestamp: new Date(threat.created_at)
      }));
    }
  } catch (e) {
    console.warn('Could not load threats:', e);
  }
  
  // Fallback if no data loaded
  if (state.scans.length === 0) {
    state.scans = mockScans;
  }
  if (state.threats.length === 0) {
    state.threats = mockScans.filter(s => s.isThreat);
  }
}

async function loadDashboardStats() {
  const api = window.ScamShieldAPI;
  
  try {
    const stats = await api.getDashboardStats();
    
    // Update stat counters
    if (stats) {
      updateStatCounter('total-scans', stats.total_scans || 0);
      updateStatCounter('threats-blocked', stats.threats_blocked || 0);
      updateStatCounter('protection-rate', stats.protection_rate || 100, '%');
      updateStatCounter('risk-score', stats.avg_risk_score ? Math.round(stats.avg_risk_score * 100) : 0, '%');
    }
  } catch (e) {
    console.warn('Could not load dashboard stats:', e);
  }
}

function updateStatCounter(id, value, suffix = '') {
  const el = document.querySelector(`[data-stat="${id}"]`) || document.getElementById(id);
  if (el) {
    el.setAttribute('data-target', value);
    el.setAttribute('data-suffix', suffix);
  }
}

// ==========================================
// USER INFO
// ==========================================
function setupUserInfo() {
  const name = state.user?.full_name || state.user?.name || 'Agent';
  const email = state.user?.email || '';
  
  const userNameEl = document.getElementById('userName');
  const userInitialsEl = document.getElementById('userInitials');
  
  if (userNameEl) userNameEl.textContent = name;
  if (userInitialsEl) userInitialsEl.textContent = name.split(' ').map(n => n[0]).join('').toUpperCase();
  
  // Settings
  const settingsName = document.getElementById('settingsName');
  const settingsEmail = document.getElementById('settingsEmail');
  if (settingsName) settingsName.value = name;
  if (settingsEmail) settingsEmail.value = email;
}

// ==========================================
// NAVIGATION
// ==========================================
function setupNavigation() {
  const links = document.querySelectorAll('.sidebar-link[data-view]');
  
  links.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const view = link.getAttribute('data-view');
      switchView(view);
      
      // Close mobile sidebar after navigation
      closeMobileSidebar();
    });
  });
  
  // Setup mobile menu toggle
  setupMobileMenu();
}

// ==========================================
// MOBILE MENU
// ==========================================
function setupMobileMenu() {
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const sidebar = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');
  
  if (mobileMenuBtn && sidebar) {
    mobileMenuBtn.addEventListener('click', () => {
      toggleMobileSidebar();
    });
  }
  
  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', () => {
      closeMobileSidebar();
    });
  }
  
  // Close sidebar on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeMobileSidebar();
    }
  });
}

function toggleMobileSidebar() {
  const sidebar = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');
  const body = document.body;
  
  if (sidebar) {
    sidebar.classList.toggle('active');
  }
  
  if (sidebarOverlay) {
    sidebarOverlay.classList.toggle('active');
  }
  
  // Prevent body scroll when sidebar is open
  body.style.overflow = sidebar?.classList.contains('active') ? 'hidden' : '';
}

function closeMobileSidebar() {
  const sidebar = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');
  const body = document.body;
  
  if (sidebar) {
    sidebar.classList.remove('active');
  }
  
  if (sidebarOverlay) {
    sidebarOverlay.classList.remove('active');
  }
  
  body.style.overflow = '';
}

function switchView(viewName) {
  const views = document.querySelectorAll('.view');
  const links = document.querySelectorAll('.sidebar-link[data-view]');
  
  views.forEach(v => v.classList.remove('active'));
  links.forEach(l => l.classList.remove('active'));
  
  const targetView = document.getElementById(`view-${viewName}`);
  const targetLink = document.querySelector(`.sidebar-link[data-view="${viewName}"]`);
  
  if (targetView) targetView.classList.add('active');
  if (targetLink) targetLink.classList.add('active');
  
  state.currentView = viewName;
  
  // Re-animate counters when switching views
  if (viewName === 'dashboard') {
    animateCounters();
  }
}

// ==========================================
// ANIMATED COUNTERS
// ==========================================
function animateCounters() {
  const counters = document.querySelectorAll('[data-target]');
  
  counters.forEach(counter => {
    const target = parseInt(counter.getAttribute('data-target'));
    const suffix = counter.getAttribute('data-suffix') || '';
    const duration = 1500;
    const start = 0;
    const startTime = performance.now();
    
    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(start + (target - start) * easeProgress);
      
      counter.textContent = current + suffix;
      
      if (progress < 1) {
        requestAnimationFrame(update);
      }
    }
    
    requestAnimationFrame(update);
  });
}

// ==========================================
// ACTIVITY FEED
// ==========================================
function populateActivityFeed() {
  const feed = document.getElementById('activityFeed');
  if (!feed) return;
  
  const items = state.scans.slice(0, 5);
  
  feed.innerHTML = items.map(scan => `
    <div class="feed-item">
      <div class="feed-icon ${scan.isThreat ? 'danger' : 'safe'}">
        ${scan.isThreat ? '⚠️' : '✓'}
      </div>
      <div class="feed-content">
        <div class="feed-title">${scan.isThreat ? 'Threat Blocked' : 'Message Safe'}</div>
        <div class="feed-meta">
          <span>${scan.source}</span>
          ${scan.threatType ? `<span class="timeline-tag ${scan.threatType}">${formatThreatType(scan.threatType)}</span>` : ''}
        </div>
      </div>
      <div class="feed-time">${timeAgo(scan.timestamp)}</div>
    </div>
  `).join('');
}

// ==========================================
// RADAR BLIPS
// ==========================================
function populateRadarBlips() {
  const container = document.getElementById('radarBlips');
  if (!container) return;
  
  const threats = state.threats.slice(0, 5);
  const positions = [
    { top: '20%', left: '60%' },
    { top: '35%', left: '25%' },
    { top: '55%', left: '70%' },
    { top: '70%', left: '35%' },
    { top: '45%', left: '55%' }
  ];
  
  container.innerHTML = threats.map((threat, i) => `
    <div class="radar-blip ${threat.threatType}" style="top: ${positions[i].top}; left: ${positions[i].left}"></div>
  `).join('');
}

// ==========================================
// TIMELINE
// ==========================================
function populateTimeline() {
  const container = document.getElementById('timelineFeed');
  if (!container) return;
  
  container.innerHTML = state.scans.map(scan => `
    <div class="timeline-item" data-type="${scan.isThreat ? 'threat' : 'safe'}">
      <div class="timeline-dot ${scan.isThreat ? 'danger' : 'safe'}"></div>
      <div class="timeline-content">
        <div class="timeline-title">${scan.isThreat ? 'Threat Detected & Blocked' : 'Message Verified Safe'}</div>
        <div class="timeline-preview">${scan.content.substring(0, 80)}...</div>
        <div class="timeline-meta">
          <span>${scan.source}</span>
          ${scan.threatType ? `<span class="timeline-tag ${scan.threatType}">${formatThreatType(scan.threatType)}</span>` : ''}
          <span>${timeAgo(scan.timestamp)}</span>
        </div>
      </div>
    </div>
  `).join('');
  
  // Setup filters
  setupTimelineFilters();
}

function setupTimelineFilters() {
  const pills = document.querySelectorAll('.filter-pills .pill');
  
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      
      const filter = pill.getAttribute('data-filter');
      const items = document.querySelectorAll('.timeline-item');
      
      items.forEach(item => {
        const type = item.getAttribute('data-type');
        if (filter === 'all' || type === filter) {
          item.style.display = 'flex';
        } else {
          item.style.display = 'none';
        }
      });
    });
  });
}

// ==========================================
// EVIDENCE BOARD
// ==========================================
function populateEvidenceBoard() {
  const board = document.getElementById('corkBoard');
  if (!board) return;
  
  const threats = state.threats.slice(0, 5);
  const positions = [
    { top: 40, left: 50, rotate: -5 },
    { top: 80, left: 280, rotate: 3 },
    { top: 180, left: 120, rotate: -2 },
    { top: 60, left: 500, rotate: 4 },
    { top: 200, left: 380, rotate: -3 }
  ];
  
  const icons = {
    phishing: '🎣',
    lottery: '🎰',
    romance: '💔',
    tech: '🖥️'
  };
  
  board.innerHTML += threats.map((threat, i) => `
    <div class="evidence-card" style="top: ${positions[i].top}px; left: ${positions[i].left}px; transform: rotate(${positions[i].rotate}deg)">
      <div class="evidence-photo">${icons[threat.threatType] || '⚠️'}</div>
      <div class="evidence-label">${formatThreatType(threat.threatType)}</div>
      <div class="evidence-date">${formatDate(threat.timestamp)}</div>
      <div class="evidence-stamp">BLOCKED</div>
    </div>
  `).join('');
}

// ==========================================
// X-RAY SCANNER
// ==========================================
function setupXrayScanner() {
  const scanBtn = document.getElementById('startScanBtn');
  if (!scanBtn) return;
  
  scanBtn.addEventListener('click', startXrayScan);
}

async function startXrayScan() {
  const input = document.getElementById('xrayInput');
  const content = input?.value.trim();
  
  if (!content) {
    showToast('Please enter content to analyze', 'warning');
    return;
  }
  
  // Switch to scanning state
  const inputState = document.getElementById('xrayInputState');
  const scanningState = document.getElementById('xrayScanningState');
  const resultState = document.getElementById('xrayResultState');
  
  inputState.classList.add('hidden');
  scanningState.classList.remove('hidden');
  resultState.classList.add('hidden');
  
  // Show content being scanned
  const scannerText = document.getElementById('scannerTextDisplay');
  scannerText.textContent = content;
  
  // Animate progress steps
  const steps = document.querySelectorAll('.step');
  const progressFill = document.querySelector('.progress-fill');
  
  for (let i = 0; i < steps.length; i++) {
    await delay(600);
    steps.forEach((s, j) => {
      s.classList.remove('active');
      if (j < i) s.classList.add('done');
    });
    steps[i].classList.add('active');
    progressFill.style.width = ((i + 1) / steps.length * 100) + '%';
  }
  
  await delay(400);
  
  // Try API scan first, fallback to local analysis
  let result;
  try {
    const api = window.ScamShieldAPI;
    const apiResult = await api.scanMessage(content, 'SMS');
    
    result = {
      isThreat: apiResult.is_scam,
      risk: Math.round((apiResult.risk_score || 0) * 100),
      threatType: apiResult.scam_type,
      tactics: apiResult.indicators || [],
      explanation: apiResult.analysis || apiResult.explanation || (apiResult.is_scam 
        ? 'This message contains multiple red flags commonly associated with scam attempts.'
        : 'This message appears to be legitimate. No significant threat indicators were detected.')
    };
    
    // Add to local state
    state.scans.unshift({
      id: apiResult.scan_id,
      content: content,
      source: 'SMS',
      isThreat: result.isThreat,
      threatType: result.threatType,
      risk: result.risk,
      timestamp: new Date()
    });
    
    // Update UI
    populateActivityFeed();
    populateTimeline();
    
  } catch (error) {
    console.warn('API scan failed, using local analysis:', error);
    result = analyzeContent(content);
  }
  
  displayXrayResult(content, result);
}

function analyzeContent(content) {
  const lowerContent = content.toLowerCase();
  
  // Detect tactics used
  const tacticsFound = [];
  Object.entries(scamPatterns).forEach(([tactic, patterns]) => {
    if (patterns.some(p => lowerContent.includes(p))) {
      tacticsFound.push(tactic);
    }
  });
  
  // Calculate risk
  let risk = tacticsFound.length * 15 + Math.random() * 10;
  risk = Math.min(99, Math.max(5, risk));
  
  const isThreat = tacticsFound.length >= 2;
  
  // Determine type
  let threatType = null;
  if (lowerContent.includes('lottery') || lowerContent.includes('won') || lowerContent.includes('prize')) {
    threatType = 'lottery';
  } else if (lowerContent.includes('verify') || lowerContent.includes('suspended') || lowerContent.includes('account')) {
    threatType = 'phishing';
  } else if (lowerContent.includes('love') || lowerContent.includes('princess') || lowerContent.includes('dear')) {
    threatType = 'romance';
  } else if (lowerContent.includes('microsoft') || lowerContent.includes('support') || lowerContent.includes('computer')) {
    threatType = 'tech';
  } else if (isThreat) {
    threatType = 'phishing';
  }
  
  return {
    isThreat,
    risk: Math.round(risk),
    threatType,
    tactics: tacticsFound,
    explanation: isThreat 
      ? 'This message contains multiple red flags commonly associated with scam attempts. It uses manipulation tactics to create urgency and pressure you into taking action without thinking.'
      : 'This message appears to be legitimate. No significant threat indicators were detected during our analysis.'
  };
}

function displayXrayResult(originalContent, result) {
  const scanningState = document.getElementById('xrayScanningState');
  const resultState = document.getElementById('xrayResultState');
  
  scanningState.classList.add('hidden');
  resultState.classList.remove('hidden');
  
  // Populate scammer view (original content)
  const scammerContent = document.getElementById('scammerContent');
  scammerContent.textContent = originalContent;
  
  // Populate truth view (highlighted version)
  const truthContent = document.getElementById('truthContent');
  truthContent.innerHTML = highlightThreats(originalContent, result.tactics);
  
  // Verdict stamp
  const stamp = document.getElementById('verdictStamp');
  stamp.className = `verdict-stamp ${result.isThreat ? 'danger' : 'safe'}`;
  stamp.querySelector('span').textContent = result.isThreat ? 'SCAM' : 'SAFE';
  
  // Risk bar
  const riskFill = document.getElementById('riskFill');
  const riskValue = document.getElementById('riskValue');
  setTimeout(() => {
    riskFill.style.width = result.risk + '%';
    riskValue.textContent = result.risk + '%';
  }, 100);
  
  // Scam type
  const scamTypeEl = document.getElementById('scamTypeValue');
  scamTypeEl.textContent = result.threatType ? formatThreatType(result.threatType) : 'None detected';
  
  // Tactics
  const tacticsEl = document.getElementById('tacticsChips');
  tacticsEl.innerHTML = result.tactics.length 
    ? result.tactics.map(t => `<span class="tactic-chip">${formatTactic(t)}</span>`).join('')
    : '<span class="tactic-chip" style="background: rgba(27,94,32,0.2); color: var(--safe);">No manipulation tactics</span>';
  
  // Analysis text
  const analysisEl = document.getElementById('verdictAnalysis');
  analysisEl.textContent = result.explanation;
}

function highlightThreats(content, tactics) {
  let highlighted = content;
  
  // Highlight dangerous patterns
  Object.entries(scamPatterns).forEach(([tactic, patterns]) => {
    if (tactics.includes(tactic)) {
      patterns.forEach(pattern => {
        const regex = new RegExp(`(${pattern})`, 'gi');
        highlighted = highlighted.replace(regex, '<span class="highlight-danger">$1</span>');
      });
    }
  });
  
  return highlighted;
}

function resetXray() {
  const inputState = document.getElementById('xrayInputState');
  const scanningState = document.getElementById('xrayScanningState');
  const resultState = document.getElementById('xrayResultState');
  
  inputState.classList.remove('hidden');
  scanningState.classList.add('hidden');
  resultState.classList.add('hidden');
  
  // Reset progress
  document.querySelectorAll('.step').forEach(s => {
    s.classList.remove('active', 'done');
  });
  document.querySelector('.progress-fill').style.width = '0%';
  
  // Clear input
  document.getElementById('xrayInput').value = '';
  document.getElementById('xrayInput').focus();
}

// ==========================================
// QUICK SCAN
// ==========================================
function setupQuickScan() {
  const btn = document.getElementById('quickScanBtn');
  const modal = document.getElementById('quickScanModal');
  
  btn?.addEventListener('click', () => {
    modal?.classList.add('active');
  });
}

function closeQuickScan() {
  document.getElementById('quickScanModal')?.classList.remove('active');
}

function quickScan() {
  const input = document.getElementById('quickScanInput');
  const content = input?.value.trim();
  
  if (!content) {
    showToast('Please enter content to scan', 'warning');
    return;
  }
  
  closeQuickScan();
  
  // Switch to X-Ray view and populate
  switchView('xray');
  document.getElementById('xrayInput').value = content;
  
  // Auto-start scan after a brief delay
  setTimeout(() => {
    startXrayScan();
  }, 500);
}

// ==========================================
// UTILITY FUNCTIONS
// ==========================================
function timeAgo(date) {
  const seconds = Math.floor((new Date() - date) / 1000);
  
  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
  if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
  return Math.floor(seconds / 86400) + 'd ago';
}

function formatDate(date) {
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function formatThreatType(type) {
  const types = {
    phishing: 'Phishing',
    lottery: 'Lottery Scam',
    romance: 'Romance Scam',
    tech: 'Tech Support'
  };
  return types[type] || type || 'Unknown';
}

function formatTactic(tactic) {
  const tactics = {
    urgency: '⚡ Urgency',
    money: '💰 Money Lure',
    fear: '😨 Fear Tactics',
    authority: '🏛️ Fake Authority',
    personal: '💕 Personal Appeal',
    action: '👆 Call to Action'
  };
  return tactics[tactic] || tactic;
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'toastIn 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function reportThreat() {
  showToast('Threat reported to authorities', 'success');
}

function blockSender() {
  showToast('Sender has been blocked', 'success');
}

// ==========================================
// API KEY MANAGEMENT
// ==========================================
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';
let currentApiKey = null;
let isApiKeyVisible = false;

// Check for existing API key on load
async function checkExistingApiKey() {
  // Check localStorage first (for demo without backend)
  const storedKey = localStorage.getItem('scamshield_api_key');
  if (storedKey) {
    try {
      const keyData = JSON.parse(storedKey);
      currentApiKey = keyData.key;
      showApiKeyState(true, keyData);
      return;
    } catch (e) {
      localStorage.removeItem('scamshield_api_key');
    }
  }
  
  // Try backend (if available)
  try {
    const token = getAuthToken();
    if (token) {
      const response = await fetch(`${API_BASE_URL}/users/me/api-key`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        showApiKeyState(true, data);
      } else {
        showApiKeyState(false);
      }
    } else {
      showApiKeyState(false);
    }
  } catch (e) {
    // Backend not available, use localStorage state
    showApiKeyState(false);
  }
}

function getAuthToken() {
  // Get JWT token from storage if using backend auth
  return localStorage.getItem('scamshield_token') || null;
}

async function generateApiKey() {
  const btn = event.target.closest('button');
  const originalText = btn.innerHTML;
  btn.innerHTML = '<span class="spinner"></span> Generating...';
  btn.disabled = true;
  
  try {
    // Try backend first
    const token = getAuthToken();
    let keyData = null;
    
    if (token) {
      try {
        const response = await fetch(`${API_BASE_URL}/users/me/api-key`, {
          method: 'POST',
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          keyData = await response.json();
          currentApiKey = keyData.api_key;
        }
      } catch (e) {
        console.log('Backend not available, using local generation');
      }
    }
    
    // Fallback: Generate locally for demo
    if (!keyData) {
      const randomBytes = new Uint8Array(32);
      crypto.getRandomValues(randomBytes);
      const hexString = Array.from(randomBytes).map(b => b.toString(16).padStart(2, '0')).join('');
      
      currentApiKey = `sk_live_${hexString.slice(0, 32)}`;
      keyData = {
        api_key: currentApiKey,
        prefix: `sk_live_${hexString.slice(0, 8)}...`,
        created_at: new Date().toISOString(),
        status: 'active'
      };
      
      // Store in localStorage for demo persistence
      localStorage.setItem('scamshield_api_key', JSON.stringify({
        key: currentApiKey,
        ...keyData
      }));
    }
    
    showApiKeyState(true, keyData);
    isApiKeyVisible = true;
    updateApiKeyDisplay();
    
    showToast('API key generated successfully!', 'success');
    
  } catch (error) {
    showToast('Failed to generate API key. Please try again.', 'danger');
    console.error('API Key generation error:', error);
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

async function regenerateApiKey() {
  if (!confirm('Are you sure you want to regenerate your API key? Your current key will stop working immediately.')) {
    return;
  }
  
  // Remove old key
  localStorage.removeItem('scamshield_api_key');
  currentApiKey = null;
  
  // Generate new one
  await generateApiKey();
  
  showToast('API key regenerated successfully!', 'success');
}

async function revokeApiKey() {
  if (!confirm('Are you sure you want to revoke your API key? This action cannot be undone.')) {
    return;
  }
  
  try {
    // Try backend
    const token = getAuthToken();
    if (token) {
      try {
        await fetch(`${API_BASE_URL}/users/me/api-key`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${token}` }
        });
      } catch (e) {
        console.log('Backend not available');
      }
    }
    
    // Clear local storage
    localStorage.removeItem('scamshield_api_key');
    currentApiKey = null;
    isApiKeyVisible = false;
    
    showApiKeyState(false);
    showToast('API key revoked successfully', 'success');
    
  } catch (error) {
    showToast('Failed to revoke API key', 'danger');
  }
}

function showApiKeyState(hasKey, keyData = null) {
  const noKeyState = document.getElementById('apiKeyNoKey');
  const hasKeyState = document.getElementById('apiKeyHasKey');
  
  if (!noKeyState || !hasKeyState) return;
  
  if (hasKey && keyData) {
    noKeyState.classList.add('hidden');
    hasKeyState.classList.remove('hidden');
    
    // Update created date
    const createdEl = document.getElementById('apiKeyCreated');
    if (createdEl && keyData.created_at) {
      const date = new Date(keyData.created_at);
      createdEl.textContent = `Created: ${date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
      })}`;
    }
    
    updateApiKeyDisplay();
  } else {
    noKeyState.classList.remove('hidden');
    hasKeyState.classList.add('hidden');
  }
}

function toggleApiKeyVisibility() {
  isApiKeyVisible = !isApiKeyVisible;
  updateApiKeyDisplay();
  
  const eyeIcon = document.getElementById('eyeIcon');
  if (eyeIcon) {
    if (isApiKeyVisible) {
      eyeIcon.innerHTML = `
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
        <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
        <line x1="1" y1="1" x2="23" y2="23"/>
      `;
    } else {
      eyeIcon.innerHTML = `
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
        <circle cx="12" cy="12" r="3"/>
      `;
    }
  }
}

function updateApiKeyDisplay() {
  const valueEl = document.getElementById('apiKeyValue');
  if (!valueEl) return;
  
  if (isApiKeyVisible && currentApiKey) {
    valueEl.textContent = currentApiKey;
  } else if (currentApiKey) {
    // Show masked version
    const prefix = currentApiKey.slice(0, 12);
    valueEl.textContent = `${prefix}${'•'.repeat(20)}`;
  } else {
    valueEl.textContent = 'sk_live_••••••••••••••••••••••••';
  }
}

function copyApiKey() {
  if (currentApiKey) {
    navigator.clipboard.writeText(currentApiKey);
    showToast('API key copied to clipboard', 'success');
  } else {
    // Try to get from storage
    const stored = localStorage.getItem('scamshield_api_key');
    if (stored) {
      const data = JSON.parse(stored);
      navigator.clipboard.writeText(data.key);
      showToast('API key copied to clipboard', 'success');
    } else {
      showToast('No API key to copy', 'warning');
    }
  }
}

function copyCodeExample(lang = 'curl') {
  const codeExamples = {
    curl: `curl -X POST "https://api.scamshield.io/v1/scan" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "Your suspicious message here"}'`,
    python: `import requests

response = requests.post(
    "https://api.scamshield.io/v1/scan",
    headers={"Authorization": "Bearer YOUR_API_KEY"},
    json={"text": "Check this message for scams"}
)
print(response.json())`,
    javascript: `const response = await fetch('https://api.scamshield.io/v1/scan', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ text: 'Check this message' })
});
const data = await response.json();`
  };
  
  navigator.clipboard.writeText(codeExamples[lang] || codeExamples.curl);
  showToast('Code copied to clipboard', 'success');
}

// ==========================================
// CODE TABS
// ==========================================
function setupCodeTabs() {
  const tabs = document.querySelectorAll('.code-tab');
  
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const lang = tab.getAttribute('data-lang');
      const parent = tab.closest('.docs-card, .api-quickstart');
      
      // Update active tab within the same parent
      parent.querySelectorAll('.code-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      
      // Show corresponding code block within the same parent
      parent.querySelectorAll('.code-block').forEach(block => {
        block.classList.add('hidden');
      });
      
      // Try different ID patterns
      const capitalizedLang = lang.charAt(0).toUpperCase() + lang.slice(1);
      let targetBlock = parent.querySelector(`#docsCode${capitalizedLang}`) || 
                        parent.querySelector(`#codeBlock${capitalizedLang}`);
      if (targetBlock) {
        targetBlock.classList.remove('hidden');
      }
    });
  });
}

// Copy code example function
function copyCodeExample(lang) {
  const capitalizedLang = lang.charAt(0).toUpperCase() + lang.slice(1);
  const codeBlock = document.getElementById(`docsCode${capitalizedLang}`) ||
                    document.getElementById(`codeBlock${capitalizedLang}`);
  
  if (codeBlock) {
    const code = codeBlock.querySelector('pre code').textContent;
    navigator.clipboard.writeText(code).then(() => {
      showNotification('Code copied to clipboard!', 'success');
    });
  }
}

// ==========================================
// SETTINGS FUNCTIONS
// ==========================================
function saveSettings() {
  // Gather all settings
  const settings = {
    name: document.getElementById('settingsName')?.value || '',
    email: document.getElementById('settingsEmail')?.value || '',
    phone: document.getElementById('settingsPhone')?.value || '',
    organization: document.getElementById('settingsOrg')?.value || '',
    realtime: document.getElementById('toggleRealtime')?.checked || false,
    deepAnalysis: document.getElementById('toggleDeepAnalysis')?.checked || false,
    autoBlock: document.getElementById('toggleAutoBlock')?.checked || false,
    linkScanner: document.getElementById('toggleLinkScanner')?.checked || false,
    sensitivity: document.getElementById('sensitivityRange')?.value || 2,
    emailAlerts: document.getElementById('toggleEmailAlerts')?.checked || false,
    pushNotif: document.getElementById('togglePushNotif')?.checked || false,
    weekly: document.getElementById('toggleWeekly')?.checked || false,
    criticalOnly: document.getElementById('toggleCriticalOnly')?.checked || false,
    history: document.getElementById('toggleHistory')?.checked || false,
    analytics: document.getElementById('toggleAnalytics')?.checked || false
  };
  
  // Save to localStorage
  localStorage.setItem('scamshield_settings', JSON.stringify(settings));
  
  // Update user data if name/email changed
  if (state.user) {
    state.user.name = settings.name;
    state.user.email = settings.email;
    localStorage.setItem('scamshield_user', JSON.stringify(state.user));
    setupUserInfo();
  }
  
  showToast('Settings saved successfully!', 'success');
}

function resetSettings() {
  if (!confirm('Reset all settings to defaults?')) return;
  
  localStorage.removeItem('scamshield_settings');
  
  // Reset toggles to defaults
  const defaults = {
    toggleRealtime: true,
    toggleDeepAnalysis: true,
    toggleAutoBlock: false,
    toggleLinkScanner: true,
    toggleEmailAlerts: true,
    togglePushNotif: false,
    toggleWeekly: true,
    toggleCriticalOnly: false,
    toggleHistory: true,
    toggleAnalytics: true
  };
  
  Object.entries(defaults).forEach(([id, value]) => {
    const el = document.getElementById(id);
    if (el) el.checked = value;
  });
  
  const sensitivityEl = document.getElementById('sensitivityRange');
  if (sensitivityEl) sensitivityEl.value = 2;
  
  showToast('Settings reset to defaults', 'success');
}

function exportData() {
  const data = {
    user: state.user,
    settings: JSON.parse(localStorage.getItem('scamshield_settings') || '{}'),
    scans: state.scans,
    exportDate: new Date().toISOString()
  };
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `scamshield-data-${new Date().toISOString().split('T')[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);
  
  showToast('Data exported successfully!', 'success');
}

function clearHistory() {
  if (!confirm('Clear all scan history? This cannot be undone.')) return;
  
  state.scans = [];
  state.threats = [];
  
  // Clear UI
  const timelineFeed = document.getElementById('timelineFeed');
  if (timelineFeed) timelineFeed.innerHTML = '<p class="empty-message">No scan history</p>';
  
  const corkBoard = document.getElementById('corkBoard');
  if (corkBoard) corkBoard.innerHTML = '';
  
  showToast('History cleared', 'success');
}

function logout() {
  // Clear all auth data
  localStorage.removeItem('scamshield_user');
  localStorage.removeItem('scamshield_access_token');
  localStorage.removeItem('scamshield_refresh_token');
  localStorage.removeItem('isLoggedIn');
  localStorage.removeItem('userEmail');
  localStorage.removeItem('userName');
  localStorage.removeItem('userRole');
  // Redirect to login page
  window.location.href = './login.html';
}

// Make functions globally available
window.switchView = switchView;
window.resetXray = resetXray;
window.closeQuickScan = closeQuickScan;
window.quickScan = quickScan;
window.reportThreat = reportThreat;
window.blockSender = blockSender;
window.copyApiKey = copyApiKey;
window.logout = logout;
window.generateApiKey = generateApiKey;
window.regenerateApiKey = regenerateApiKey;
window.revokeApiKey = revokeApiKey;
window.toggleApiKeyVisibility = toggleApiKeyVisibility;
window.copyCodeExample = copyCodeExample;
window.saveSettings = saveSettings;
window.resetSettings = resetSettings;
window.exportData = exportData;
window.clearHistory = clearHistory;

// ==========================================
// API PLAYGROUND
// ==========================================
const playgroundEndpoints = {
  'scan': { method: 'POST', url: 'https://api.scamshield.io/v1/scan', hasBody: true },
  'scan-url': { method: 'POST', url: 'https://api.scamshield.io/v1/scan/url', hasBody: true },
  'scan-batch': { method: 'POST', url: 'https://api.scamshield.io/v1/scan/batch', hasBody: true },
  'threats': { method: 'GET', url: 'https://api.scamshield.io/v1/threats', hasBody: false },
  'stats': { method: 'GET', url: 'https://api.scamshield.io/v1/stats', hasBody: false }
};

const sampleRequests = {
  'scan': {
    text: "Congratulations! You've won $1,000,000! Click here to claim your prize immediately!",
    options: {
      deep_analysis: true,
      include_tactics: true
    }
  },
  'scan-url': {
    url: "https://suspicious-lottery-winner.com/claim-prize",
    options: {
      check_ssl: true,
      follow_redirects: true
    }
  },
  'scan-batch': {
    items: [
      { text: "Your account has been suspended. Verify now!" },
      { text: "Meeting tomorrow at 3pm in conference room B" },
      { text: "URGENT: Wire $500 to unlock your inheritance" }
    ]
  },
  'threats': null,
  'stats': null
};

let playgroundHistory = [];

function updatePlaygroundEndpoint() {
  const select = document.getElementById('playgroundEndpoint');
  const endpoint = playgroundEndpoints[select.value];
  const methodBadge = document.getElementById('playgroundMethod');
  const urlInput = document.getElementById('playgroundUrl');
  const bodySection = document.getElementById('bodySection');
  const bodyTextarea = document.getElementById('playgroundBody');
  
  methodBadge.textContent = endpoint.method;
  methodBadge.className = `method-badge ${endpoint.method.toLowerCase()}`;
  urlInput.value = endpoint.url;
  
  if (endpoint.hasBody) {
    bodySection.style.display = 'block';
    const sample = sampleRequests[select.value];
    if (sample) {
      bodyTextarea.value = JSON.stringify(sample, null, 2);
    }
  } else {
    bodySection.style.display = 'none';
  }
}

function toggleSection(sectionId) {
  const section = document.getElementById(sectionId);
  section.style.display = section.style.display === 'none' ? 'block' : 'none';
}

function formatJson() {
  const textarea = document.getElementById('playgroundBody');
  try {
    const parsed = JSON.parse(textarea.value);
    textarea.value = JSON.stringify(parsed, null, 2);
    showToast('JSON formatted', 'success');
  } catch (e) {
    showToast('Invalid JSON', 'error');
  }
}

function loadSampleRequest() {
  const select = document.getElementById('playgroundEndpoint');
  const sample = sampleRequests[select.value];
  const bodyTextarea = document.getElementById('playgroundBody');
  
  if (sample) {
    bodyTextarea.value = JSON.stringify(sample, null, 2);
    showToast('Sample loaded', 'success');
  }
}

async function sendPlaygroundRequest() {
  const select = document.getElementById('playgroundEndpoint');
  const endpoint = playgroundEndpoints[select.value];
  const authHeader = document.getElementById('playgroundAuthHeader').value;
  const bodyTextarea = document.getElementById('playgroundBody');
  
  const responseContent = document.getElementById('responseContent');
  const responseMeta = document.getElementById('responseMeta');
  const responseStatus = document.getElementById('responseStatus');
  const responseTime = document.getElementById('responseTime');
  const responseActions = document.getElementById('responseActions');
  
  // Show loading
  responseContent.innerHTML = '<div class="response-placeholder"><div class="loading-spinner"></div><p>Sending request...</p></div>';
  
  const startTime = Date.now();
  
  // Simulate API call (replace with real API call in production)
  await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000));
  
  const elapsed = Date.now() - startTime;
  
  // Generate mock response
  let mockResponse;
  const isScam = select.value === 'scan' || select.value === 'scan-url';
  
  if (select.value === 'scan') {
    mockResponse = {
      success: true,
      analysis: {
        is_scam: true,
        confidence: 0.94,
        threat_level: "HIGH",
        category: "lottery_scam",
        tactics_detected: ["urgency", "prize_lure", "action_required"],
        risk_score: 94
      },
      timestamp: new Date().toISOString()
    };
  } else if (select.value === 'scan-url') {
    mockResponse = {
      success: true,
      analysis: {
        is_malicious: true,
        domain_age_days: 3,
        ssl_valid: false,
        phishing_score: 0.89,
        known_threat: true
      },
      timestamp: new Date().toISOString()
    };
  } else if (select.value === 'threats') {
    mockResponse = {
      success: true,
      threats: [
        { id: 1, type: "phishing", severity: "high", detected_at: "2026-02-01T14:23:45Z" },
        { id: 2, type: "lottery_scam", severity: "high", detected_at: "2026-02-01T14:20:12Z" }
      ],
      total: 127,
      page: 1
    };
  } else if (select.value === 'stats') {
    mockResponse = {
      success: true,
      stats: {
        total_scans: 1247,
        threats_detected: 234,
        scams_blocked: 189,
        accuracy_rate: 0.982
      }
    };
  } else {
    mockResponse = {
      success: true,
      batch_results: [
        { index: 0, is_scam: true, confidence: 0.92 },
        { index: 1, is_scam: false, confidence: 0.05 },
        { index: 2, is_scam: true, confidence: 0.97 }
      ]
    };
  }
  
  // Display response
  responseMeta.style.display = 'flex';
  responseStatus.textContent = '200 OK';
  responseStatus.className = 'status-badge success';
  responseTime.textContent = `${elapsed}ms`;
  responseActions.style.display = 'flex';
  
  // Syntax highlight JSON
  responseContent.innerHTML = `<pre>${syntaxHighlight(JSON.stringify(mockResponse, null, 2))}</pre>`;
  
  // Add to history
  addToPlaygroundHistory(endpoint.method, endpoint.url, 200, elapsed);
}

function syntaxHighlight(json) {
  return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) => {
    let cls = 'json-number';
    if (/^"/.test(match)) {
      if (/:$/.test(match)) {
        cls = 'json-key';
      } else {
        cls = 'json-string';
      }
    } else if (/true|false/.test(match)) {
      cls = 'json-boolean';
    } else if (/null/.test(match)) {
      cls = 'json-null';
    }
    return `<span class="${cls}">${match}</span>`;
  });
}

function addToPlaygroundHistory(method, url, status, time) {
  const historyList = document.getElementById('playgroundHistory');
  
  playgroundHistory.unshift({ method, url, status, time, timestamp: new Date() });
  if (playgroundHistory.length > 10) playgroundHistory.pop();
  
  renderPlaygroundHistory();
}

function renderPlaygroundHistory() {
  const historyList = document.getElementById('playgroundHistory');
  
  if (playgroundHistory.length === 0) {
    historyList.innerHTML = '<div class="history-empty"><p>No recent requests</p></div>';
    return;
  }
  
  historyList.innerHTML = playgroundHistory.map((item, i) => `
    <div class="history-item" onclick="replayRequest(${i})">
      <span class="method-badge ${item.method.toLowerCase()}">${item.method}</span>
      <span class="endpoint">${new URL(item.url).pathname}</span>
      <span class="status ${item.status < 400 ? 'success' : 'error'}">${item.status}</span>
      <span class="time">${item.time}ms</span>
    </div>
  `).join('');
}

function replayRequest(index) {
  const item = playgroundHistory[index];
  // Find matching endpoint
  for (const [key, value] of Object.entries(playgroundEndpoints)) {
    if (value.url === item.url) {
      document.getElementById('playgroundEndpoint').value = key;
      updatePlaygroundEndpoint();
      break;
    }
  }
}

function clearPlayground() {
  document.getElementById('playgroundBody').value = '';
  document.getElementById('responseContent').innerHTML = `
    <div class="response-placeholder">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
      </svg>
      <p>Send a request to see the response</p>
    </div>
  `;
  document.getElementById('responseMeta').style.display = 'none';
  document.getElementById('responseActions').style.display = 'none';
}

function copyResponse() {
  const responseContent = document.getElementById('responseContent').innerText;
  navigator.clipboard.writeText(responseContent);
  showToast('Response copied!', 'success');
}

function downloadResponse() {
  const responseContent = document.getElementById('responseContent').innerText;
  const blob = new Blob([responseContent], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `response-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
  showToast('Response downloaded', 'success');
}

// ==========================================
// REQUEST LOGS
// ==========================================
function filterLogs() {
  const status = document.getElementById('logsStatusFilter').value;
  const endpoint = document.getElementById('logsEndpointFilter').value;
  const time = document.getElementById('logsTimeFilter').value;
  
  showToast('Filters applied', 'success');
  // In production, this would fetch filtered data from API
}

function refreshLogs() {
  showToast('Logs refreshed', 'success');
  // In production, this would fetch fresh data from API
}

function exportLogs() {
  const csvContent = `Timestamp,Method,Endpoint,Status,Latency,API Key
2026-02-01 14:23:45,POST,/v1/scan,200,89ms,sk_live_...3f8a
2026-02-01 14:22:18,POST,/v1/scan/url,200,156ms,sk_live_...3f8a
2026-02-01 14:20:02,GET,/v1/stats,200,45ms,sk_test_...9c2b
2026-02-01 14:18:33,POST,/v1/scan,429,12ms,sk_live_...7d4e
2026-02-01 14:15:21,POST,/v1/scan/batch,200,892ms,sk_live_...3f8a`;

  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `api-logs-${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  
  showToast('Logs exported as CSV', 'success');
}

function viewLogDetails(logId) {
  // In production, this would show a modal with full request/response details
  alert(`Viewing details for log #${logId}\n\nIn production, this would show:\n- Full request headers\n- Request body\n- Response body\n- Error details (if any)`);
}

// ==========================================
// WEBHOOKS
// ==========================================
let webhooks = [
  {
    id: 1,
    url: 'https://myapp.com/api/webhooks/scam',
    events: ['threat.detected', 'threat.high_risk'],
    active: true,
    created: '2026-01-15',
    delivered: 1234
  },
  {
    id: 2,
    url: 'https://hooks.slack.com/services/T00/B00/xxxx',
    events: ['report.daily'],
    active: true,
    created: '2026-01-20',
    delivered: 12
  }
];

function createWebhook() {
  const url = document.getElementById('webhookUrl').value;
  const secret = document.getElementById('webhookSecret').value;
  
  if (!url) {
    showToast('Please enter a webhook URL', 'error');
    return;
  }
  
  // Validate URL
  try {
    new URL(url);
  } catch {
    showToast('Invalid URL format', 'error');
    return;
  }
  
  // Get selected events
  const events = [];
  if (document.getElementById('eventThreatDetected').checked) events.push('threat.detected');
  if (document.getElementById('eventHighRisk').checked) events.push('threat.high_risk');
  if (document.getElementById('eventQuotaWarning').checked) events.push('quota.warning');
  if (document.getElementById('eventDailySummary').checked) events.push('report.daily');
  
  if (events.length === 0) {
    showToast('Please select at least one event', 'error');
    return;
  }
  
  // Add webhook (in production, send to API)
  const newWebhook = {
    id: webhooks.length + 1,
    url,
    events,
    active: true,
    created: new Date().toISOString().split('T')[0],
    delivered: 0
  };
  
  webhooks.push(newWebhook);
  
  // Clear form
  document.getElementById('webhookUrl').value = '';
  document.getElementById('webhookSecret').value = '';
  document.getElementById('eventThreatDetected').checked = true;
  document.getElementById('eventHighRisk').checked = false;
  document.getElementById('eventQuotaWarning').checked = false;
  document.getElementById('eventDailySummary').checked = false;
  
  showToast('Webhook created successfully!', 'success');
  renderWebhooks();
}

function testWebhook(id) {
  showToast(`Testing webhook #${id}...`, 'success');
  // In production, send test event to webhook
  setTimeout(() => {
    showToast('Test webhook sent successfully!', 'success');
  }, 1000);
}

function editWebhook(id) {
  const webhook = webhooks.find(w => w.id === id);
  if (!webhook) return;
  
  // Populate form with existing data
  document.getElementById('webhookUrl').value = webhook.url;
  document.getElementById('eventThreatDetected').checked = webhook.events.includes('threat.detected');
  document.getElementById('eventHighRisk').checked = webhook.events.includes('threat.high_risk');
  document.getElementById('eventQuotaWarning').checked = webhook.events.includes('quota.warning');
  document.getElementById('eventDailySummary').checked = webhook.events.includes('report.daily');
  
  // Remove old webhook
  webhooks = webhooks.filter(w => w.id !== id);
  renderWebhooks();
  
  showToast('Edit the webhook and click Create to save', 'success');
}

function deleteWebhook(id) {
  if (!confirm('Are you sure you want to delete this webhook?')) return;
  
  webhooks = webhooks.filter(w => w.id !== id);
  renderWebhooks();
  showToast('Webhook deleted', 'success');
}

function renderWebhooks() {
  const list = document.getElementById('webhooksList');
  const count = document.querySelector('.webhook-count');
  
  if (count) count.textContent = `${webhooks.length} webhook${webhooks.length !== 1 ? 's' : ''}`;
  
  if (!list) return;
  
  list.innerHTML = webhooks.map(webhook => `
    <div class="webhook-item">
      <div class="webhook-status ${webhook.active ? 'active' : 'inactive'}"></div>
      <div class="webhook-info">
        <div class="webhook-url">${webhook.url}</div>
        <div class="webhook-meta">
          <span class="webhook-events">
            ${webhook.events.map(e => `<span class="event-tag">${e}</span>`).join('')}
          </span>
          <span class="webhook-created">Created ${webhook.created}</span>
        </div>
        <div class="webhook-stats">
          <span class="stat-item success">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            ${webhook.delivered.toLocaleString()} delivered
          </span>
        </div>
      </div>
      <div class="webhook-actions">
        <button class="btn-icon" onclick="testWebhook(${webhook.id})" title="Test">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
        </button>
        <button class="btn-icon" onclick="editWebhook(${webhook.id})" title="Edit">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        </button>
        <button class="btn-icon danger" onclick="deleteWebhook(${webhook.id})" title="Delete">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
          </svg>
        </button>
      </div>
    </div>
  `).join('');
}

// Make new functions globally available
window.updatePlaygroundEndpoint = updatePlaygroundEndpoint;
window.toggleSection = toggleSection;
window.formatJson = formatJson;
window.loadSampleRequest = loadSampleRequest;
window.sendPlaygroundRequest = sendPlaygroundRequest;
window.clearPlayground = clearPlayground;
window.copyResponse = copyResponse;
window.downloadResponse = downloadResponse;
window.replayRequest = replayRequest;
window.filterLogs = filterLogs;
window.refreshLogs = refreshLogs;
window.exportLogs = exportLogs;
window.viewLogDetails = viewLogDetails;
window.createWebhook = createWebhook;
window.testWebhook = testWebhook;
window.editWebhook = editWebhook;
window.deleteWebhook = deleteWebhook;

// ==========================================
// MULTIPLE API KEYS MANAGEMENT
// ==========================================
let apiKeys = [
  {
    id: 1,
    label: 'Production App',
    key: 'your_production_api_key_here',
    maskedKey: 'sk_live_••••••••3f8a',
    env: 'production',
    permissions: ['scan:read', 'scan:write', 'threats:read'],
    usage: 2847,
    created: '2026-01-15',
    primary: true
  },
  {
    id: 2,
    label: 'Development',
    key: 'your_development_api_key_here',
    maskedKey: 'sk_test_••••••••9c2b',
    env: 'test',
    permissions: ['scan:read', 'scan:write'],
    usage: 156,
    created: '2026-01-28',
    primary: false
  }
];

let keyVisibility = {};

function createNewApiKey() {
  const label = document.getElementById('newKeyLabel').value.trim();
  const env = document.getElementById('newKeyEnv').value;
  const expiration = document.getElementById('newKeyExpiration').value;
  
  if (!label) {
    showToast('Please enter a key label', 'error');
    return;
  }
  
  // Get selected permissions
  const permissions = [];
  document.querySelectorAll('.permission-checkbox input:checked').forEach(cb => {
    permissions.push(cb.parentElement.querySelector('span').textContent);
  });
  
  // Generate new key
  const prefix = env === 'production' ? 'sk_live_' : 'sk_test_';
  const keyChars = 'abcdef0123456789';
  let keyBody = '';
  for (let i = 0; i < 32; i++) {
    keyBody += keyChars.charAt(Math.floor(Math.random() * keyChars.length));
  }
  const fullKey = prefix + keyBody;
  const suffix = keyBody.slice(-4);
  
  const newKey = {
    id: apiKeys.length + 1,
    label,
    key: fullKey,
    maskedKey: `${prefix}••••••••${suffix}`,
    env,
    permissions,
    usage: 0,
    created: new Date().toISOString().split('T')[0],
    primary: false
  };
  
  apiKeys.push(newKey);
  
  // Clear form
  document.getElementById('newKeyLabel').value = '';
  
  // Refresh table
  renderApiKeysTable();
  
  // Show the new key (one-time)
  showToast(`API Key created: ${fullKey.slice(0, 20)}... Copy it now!`, 'success');
}

function toggleKeyVisibility(id) {
  const key = apiKeys.find(k => k.id === id);
  if (!key) return;
  
  keyVisibility[id] = !keyVisibility[id];
  
  const valueEl = document.getElementById(`key${id}Value`);
  if (valueEl) {
    valueEl.textContent = keyVisibility[id] ? key.key : key.maskedKey;
  }
}

function copyKey(id) {
  const key = apiKeys.find(k => k.id === id);
  if (!key) return;
  
  navigator.clipboard.writeText(key.key);
  showToast('API key copied to clipboard!', 'success');
}

function editKey(id) {
  const key = apiKeys.find(k => k.id === id);
  if (!key) return;
  
  const newLabel = prompt('Enter new label for this key:', key.label);
  if (newLabel && newLabel.trim()) {
    key.label = newLabel.trim();
    renderApiKeysTable();
    showToast('Key label updated', 'success');
  }
}

function revokeKey(id) {
  const key = apiKeys.find(k => k.id === id);
  if (!key) return;
  
  if (!confirm(`Are you sure you want to revoke "${key.label}"? This cannot be undone.`)) {
    return;
  }
  
  apiKeys = apiKeys.filter(k => k.id !== id);
  renderApiKeysTable();
  showToast('API key revoked', 'success');
}

function renderApiKeysTable() {
  const tbody = document.getElementById('apiKeysTableBody');
  const countEl = document.getElementById('apiKeysCount');
  
  if (countEl) {
    countEl.textContent = `${apiKeys.length} key${apiKeys.length !== 1 ? 's' : ''}`;
  }
  
  if (!tbody) return;
  
  tbody.innerHTML = apiKeys.map(key => `
    <tr>
      <td>
        <div class="key-label-cell">
          <span class="key-name">${key.label}</span>
          ${key.primary ? '<span class="key-primary-badge">PRIMARY</span>' : ''}
        </div>
      </td>
      <td>
        <div class="key-display">
          <code class="key-value" id="key${key.id}Value">${keyVisibility[key.id] ? key.key : key.maskedKey}</code>
          <button class="btn-icon btn-tiny" onclick="toggleKeyVisibility(${key.id})" title="Show">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </button>
          <button class="btn-icon btn-tiny" onclick="copyKey(${key.id})" title="Copy">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2"/>
              <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
            </svg>
          </button>
        </div>
      </td>
      <td><span class="env-badge ${key.env === 'production' ? 'live' : 'test'}">${key.env === 'production' ? 'Live' : 'Test'}</span></td>
      <td>
        <div class="permissions-badges">
          ${key.permissions.slice(0, 2).map(p => `<span class="perm-badge">${p}</span>`).join('')}
          ${key.permissions.length > 2 ? `<span class="perm-more">+${key.permissions.length - 2}</span>` : ''}
        </div>
      </td>
      <td>
        <div class="usage-cell">
          <span class="usage-count">${key.usage.toLocaleString()}</span>
          <div class="usage-mini-bar">
            <div class="usage-mini-fill" style="width: ${Math.min(key.usage / 100, 100)}%"></div>
          </div>
        </div>
      </td>
      <td class="date-cell">${formatDate(key.created)}</td>
      <td>
        <div class="key-actions">
          <button class="btn-icon" onclick="editKey(${key.id})" title="Edit">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
          <button class="btn-icon danger" onclick="revokeKey(${key.id})" title="Revoke">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
          </button>
        </div>
      </td>
    </tr>
  `).join('');
}

function formatDate(dateStr) {
  const date = new Date(dateStr);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${months[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}`;
}

function updateAnalytics() {
  const period = document.getElementById('analyticsPeriod').value;
  showToast(`Analytics updated for ${period}`, 'success');
  // In production, fetch new data based on period
}

function clearPlaygroundHistory() {
  playgroundHistory = [];
  renderPlaygroundHistory();
  showToast('History cleared', 'success');
}

// Make new key management functions globally available
window.createNewApiKey = createNewApiKey;
window.toggleKeyVisibility = toggleKeyVisibility;
window.copyKey = copyKey;
window.editKey = editKey;
window.revokeKey = revokeKey;
window.updateAnalytics = updateAnalytics;
window.clearPlaygroundHistory = clearPlaygroundHistory;

// ==========================================
// VERIFICATION FUNCTIONS
// ==========================================

let verificationPhone = '';
let otpCountdownInterval = null;

// Check verification status on page load
async function loadVerificationStatus() {
  const api = window.ScamShieldAPI;
  if (!api || !api.isAuthenticated()) return;
  
  try {
    const response = await api.apiCall('/auth/verification-status');
    
    if (response) {
      updateVerificationUI(response);
    }
  } catch (error) {
    console.warn('Failed to load verification status:', error);
    // Default to showing verification options
    document.getElementById('emailVerificationStatus').textContent = 'Please verify your email';
    document.getElementById('phoneVerificationStatus').textContent = 'Not verified';
  }
}

function updateVerificationUI(status) {
  const emailStatusEl = document.getElementById('emailVerificationStatus');
  const phoneStatusEl = document.getElementById('phoneVerificationStatus');
  const emailVerifiedBadge = document.getElementById('emailVerifiedBadge');
  const phoneVerifiedBadge = document.getElementById('phoneVerifiedBadge');
  const resendEmailBtn = document.getElementById('resendEmailBtn');
  const verifyPhoneBtn = document.getElementById('verifyPhoneBtn');
  
  // Email verification
  if (status.email_verified) {
    emailStatusEl.textContent = 'Email verified';
    emailStatusEl.classList.add('verified');
    emailVerifiedBadge.style.display = 'flex';
    resendEmailBtn.style.display = 'none';
  } else {
    emailStatusEl.textContent = 'Pending verification';
    emailStatusEl.classList.add('pending');
    emailVerifiedBadge.style.display = 'none';
    resendEmailBtn.style.display = 'block';
  }
  
  // Phone verification
  if (status.phone_verified) {
    phoneStatusEl.textContent = status.phone ? `Verified: ${status.phone}` : 'Phone verified';
    phoneStatusEl.classList.add('verified');
    phoneVerifiedBadge.style.display = 'flex';
    verifyPhoneBtn.style.display = 'none';
  } else {
    phoneStatusEl.textContent = status.phone ? `Pending: ${status.phone}` : 'Not verified';
    phoneVerifiedBadge.style.display = 'none';
    verifyPhoneBtn.style.display = 'block';
  }
}

// Resend verification email
async function resendVerificationEmail() {
  const api = window.ScamShieldAPI;
  const user = api.getUser();
  
  if (!user || !user.email) {
    showToast('Email not found', 'error');
    return;
  }
  
  try {
    const response = await fetch('http://localhost:8001/api/v1/auth/resend-verification', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email: user.email })
    });
    
    if (response.ok) {
      showToast('Verification email sent! Check your inbox.', 'success');
    } else {
      const data = await response.json();
      showToast(data.detail || 'Failed to send email', 'error');
    }
  } catch (error) {
    console.error('Error resending verification:', error);
    showToast('Failed to send verification email', 'error');
  }
}

// Phone verification modal
function openPhoneVerificationModal() {
  document.getElementById('phoneVerificationModal').classList.add('active');
  resetPhoneVerificationModal();
}

function closePhoneVerificationModal() {
  document.getElementById('phoneVerificationModal').classList.remove('active');
  if (otpCountdownInterval) {
    clearInterval(otpCountdownInterval);
    otpCountdownInterval = null;
  }
}

function resetPhoneVerificationModal() {
  document.getElementById('phoneStep1').style.display = 'block';
  document.getElementById('phoneStep2').style.display = 'none';
  document.getElementById('phoneStep3').style.display = 'none';
  document.getElementById('verifyPhoneInput').value = '';
  
  // Reset OTP inputs
  const otpInputs = document.querySelectorAll('.otp-input');
  otpInputs.forEach(input => input.value = '');
}

// Send phone OTP
async function sendPhoneOTP() {
  const phoneInput = document.getElementById('verifyPhoneInput');
  const phone = phoneInput ? phoneInput.value.trim() : verificationPhone;
  
  if (!phone) {
    showToast('Please enter your phone number', 'error');
    return;
  }
  
  // Clean phone number
  const cleanPhone = phone.replace(/[\s\-\(\)]/g, '');
  if (!/^\+?[1-9]\d{9,14}$/.test(cleanPhone)) {
    showToast('Please enter a valid phone number', 'error');
    return;
  }
  
  verificationPhone = cleanPhone;
  
  const api = window.ScamShieldAPI;
  
  try {
    const response = await api.apiCall('/auth/send-phone-otp', {
      method: 'POST',
      body: JSON.stringify({ phone: cleanPhone })
    });
    
    if (response.status === 'success') {
      showToast('Verification code sent to your email!', 'success');
      
      // Show OTP step
      document.getElementById('phoneStep1').style.display = 'none';
      document.getElementById('phoneStep2').style.display = 'block';
      
      // Start countdown
      startOTPCountdown();
      
      // Focus first OTP input
      document.querySelector('.otp-input').focus();
    } else {
      showToast(response.detail || 'Failed to send OTP', 'error');
    }
  } catch (error) {
    console.error('Error sending OTP:', error);
    showToast(error.message || 'Failed to send verification code', 'error');
  }
}

// OTP countdown timer
function startOTPCountdown() {
  let timeLeft = 600; // 10 minutes
  const countdownEl = document.getElementById('otpCountdown');
  const resendBtn = document.getElementById('resendOTPBtn');
  
  resendBtn.disabled = true;
  
  if (otpCountdownInterval) {
    clearInterval(otpCountdownInterval);
  }
  
  otpCountdownInterval = setInterval(() => {
    timeLeft--;
    
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    countdownEl.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    if (timeLeft <= 0) {
      clearInterval(otpCountdownInterval);
      countdownEl.textContent = 'Expired';
      resendBtn.disabled = false;
    }
    
    // Enable resend after 60 seconds
    if (timeLeft <= 540) {
      resendBtn.disabled = false;
    }
  }, 1000);
}

// Handle OTP input
function handleOTPInput(input) {
  const index = parseInt(input.dataset.index);
  const value = input.value;
  
  // Only allow digits
  if (!/^\d*$/.test(value)) {
    input.value = '';
    return;
  }
  
  // Move to next input
  if (value && index < 5) {
    const nextInput = document.querySelector(`.otp-input[data-index="${index + 1}"]`);
    if (nextInput) nextInput.focus();
  }
  
  // Auto-submit when all fields are filled
  const allInputs = document.querySelectorAll('.otp-input');
  const otp = Array.from(allInputs).map(i => i.value).join('');
  
  if (otp.length === 6) {
    verifyPhoneOTP();
  }
}

// Handle backspace in OTP inputs
document.addEventListener('keydown', (e) => {
  if (e.target.classList.contains('otp-input') && e.key === 'Backspace' && !e.target.value) {
    const index = parseInt(e.target.dataset.index);
    if (index > 0) {
      const prevInput = document.querySelector(`.otp-input[data-index="${index - 1}"]`);
      if (prevInput) {
        prevInput.focus();
        prevInput.value = '';
      }
    }
  }
});

// Verify phone OTP
async function verifyPhoneOTP() {
  const otpInputs = document.querySelectorAll('.otp-input');
  const otp = Array.from(otpInputs).map(i => i.value).join('');
  
  if (otp.length !== 6) {
    showToast('Please enter the complete 6-digit code', 'error');
    return;
  }
  
  const api = window.ScamShieldAPI;
  
  try {
    const response = await api.apiCall('/auth/verify-phone', {
      method: 'POST',
      body: JSON.stringify({ 
        phone: verificationPhone, 
        otp: otp 
      })
    });
    
    if (response.status === 'success') {
      // Show success step
      document.getElementById('phoneStep2').style.display = 'none';
      document.getElementById('phoneStep3').style.display = 'block';
      
      // Update verification UI
      loadVerificationStatus();
      
      showToast('Phone number verified successfully!', 'success');
    } else {
      showToast(response.detail || 'Invalid verification code', 'error');
    }
  } catch (error) {
    console.error('Error verifying OTP:', error);
    showToast(error.message || 'Failed to verify phone number', 'error');
  }
}

// Make verification functions globally available
window.loadVerificationStatus = loadVerificationStatus;
window.resendVerificationEmail = resendVerificationEmail;
window.openPhoneVerificationModal = openPhoneVerificationModal;
window.closePhoneVerificationModal = closePhoneVerificationModal;
window.sendPhoneOTP = sendPhoneOTP;
window.verifyPhoneOTP = verifyPhoneOTP;
window.handleOTPInput = handleOTPInput;

// Load verification status when settings view is opened
document.addEventListener('DOMContentLoaded', () => {
  // Add click listener to settings link
  const settingsLink = document.querySelector('[data-view="settings"]');
  if (settingsLink) {
    settingsLink.addEventListener('click', () => {
      loadVerificationStatus();
    });
  }
});
