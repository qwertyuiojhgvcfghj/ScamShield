/**
 * ScamShield Pro - Admin Panel
 * Admin-specific JavaScript for managing users, viewing system stats, etc.
 */

// ============================================
// STATE
// ============================================
const adminState = {
  users: [],
  sessions: [],
  currentPage: 1,
  totalPages: 1,
  searchQuery: '',
  selectedUser: null,
  stats: null,
};

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  initAdminPanel();
});

async function initAdminPanel() {
  const api = window.ScamShieldAPI;
  
  // Check if user is authenticated and is admin
  if (!api || !api.isAuthenticated()) {
    window.location.href = './login.html';
    return;
  }
  
  const user = api.getUser();
  if (user?.role !== 'admin') {
    showToast('Access denied. Admin privileges required.', 'error');
    window.location.href = './dashboard.html';
    return;
  }
  
  // Setup event listeners
  setupAdminNavigation();
  setupUserSearch();
  setupModals();
  
  // Load initial data
  await Promise.all([
    loadUsers(),
    loadSystemStats(),
    loadActiveSessions(),
  ]);
}

// ============================================
// NAVIGATION
// ============================================
function setupAdminNavigation() {
  const tabs = document.querySelectorAll('.admin-tab');
  
  tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      e.preventDefault();
      const target = tab.getAttribute('data-tab');
      switchAdminTab(target);
    });
  });
}

function switchAdminTab(tabName) {
  const tabs = document.querySelectorAll('.admin-tab');
  const panels = document.querySelectorAll('.admin-panel');
  
  tabs.forEach(t => t.classList.remove('active'));
  panels.forEach(p => p.classList.remove('active'));
  
  const activeTab = document.querySelector(`.admin-tab[data-tab="${tabName}"]`);
  const activePanel = document.getElementById(`panel-${tabName}`);
  
  if (activeTab) activeTab.classList.add('active');
  if (activePanel) activePanel.classList.add('active');
}

// ============================================
// USER MANAGEMENT
// ============================================
async function loadUsers(page = 1, search = '') {
  const api = window.ScamShieldAPI;
  
  try {
    showLoading('usersTable');
    
    const response = await api.get(`/admin/users?page=${page}&limit=20&search=${encodeURIComponent(search)}`);
    
    adminState.users = response.items || [];
    adminState.currentPage = response.page || 1;
    adminState.totalPages = Math.ceil((response.total || 0) / (response.limit || 20));
    
    renderUsersTable();
    renderPagination();
    
  } catch (error) {
    console.error('Failed to load users:', error);
    showToast('Failed to load users', 'error');
  }
}

function renderUsersTable() {
  const tbody = document.getElementById('usersTableBody');
  if (!tbody) return;
  
  if (adminState.users.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" class="empty-state">No users found</td>
      </tr>
    `;
    return;
  }
  
  tbody.innerHTML = adminState.users.map(user => `
    <tr data-user-id="${user.id}">
      <td>
        <div class="user-cell">
          <div class="user-avatar">${getInitials(user.full_name || user.email)}</div>
          <div>
            <div class="user-name">${user.full_name || 'N/A'}</div>
            <div class="user-email">${user.email}</div>
          </div>
        </div>
      </td>
      <td>
        <span class="role-badge role-${user.role}">${user.role}</span>
      </td>
      <td>
        <span class="status-badge status-${user.is_active ? 'active' : 'inactive'}">
          ${user.is_active ? 'Active' : 'Inactive'}
        </span>
      </td>
      <td>
        <span class="status-badge status-${user.is_verified ? 'verified' : 'unverified'}">
          ${user.is_verified ? '✓ Verified' : '✗ Unverified'}
        </span>
      </td>
      <td>${formatDate(user.created_at)}</td>
      <td>${user.last_login ? formatDate(user.last_login) : 'Never'}</td>
      <td>
        <div class="action-buttons">
          <button class="btn-icon" onclick="viewUser('${user.id}')" title="View">
            👁️
          </button>
          <button class="btn-icon" onclick="editUser('${user.id}')" title="Edit">
            ✏️
          </button>
          ${user.is_active 
            ? `<button class="btn-icon danger" onclick="deactivateUser('${user.id}')" title="Deactivate">🚫</button>`
            : `<button class="btn-icon success" onclick="activateUser('${user.id}')" title="Activate">✅</button>`
          }
        </div>
      </td>
    </tr>
  `).join('');
}

function renderPagination() {
  const container = document.getElementById('usersPagination');
  if (!container) return;
  
  if (adminState.totalPages <= 1) {
    container.innerHTML = '';
    return;
  }
  
  let html = '<div class="pagination">';
  
  // Previous button
  html += `
    <button class="page-btn" ${adminState.currentPage === 1 ? 'disabled' : ''} 
            onclick="loadUsers(${adminState.currentPage - 1}, '${adminState.searchQuery}')">
      ← Prev
    </button>
  `;
  
  // Page numbers
  for (let i = 1; i <= adminState.totalPages; i++) {
    if (i === 1 || i === adminState.totalPages || Math.abs(i - adminState.currentPage) <= 2) {
      html += `
        <button class="page-btn ${i === adminState.currentPage ? 'active' : ''}" 
                onclick="loadUsers(${i}, '${adminState.searchQuery}')">
          ${i}
        </button>
      `;
    } else if (i === adminState.currentPage - 3 || i === adminState.currentPage + 3) {
      html += '<span class="page-ellipsis">...</span>';
    }
  }
  
  // Next button
  html += `
    <button class="page-btn" ${adminState.currentPage === adminState.totalPages ? 'disabled' : ''} 
            onclick="loadUsers(${adminState.currentPage + 1}, '${adminState.searchQuery}')">
      Next →
    </button>
  `;
  
  html += '</div>';
  container.innerHTML = html;
}

function setupUserSearch() {
  const searchInput = document.getElementById('userSearch');
  if (!searchInput) return;
  
  let debounceTimer;
  
  searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      adminState.searchQuery = e.target.value;
      loadUsers(1, e.target.value);
    }, 300);
  });
}

async function viewUser(userId) {
  const api = window.ScamShieldAPI;
  
  try {
    const user = await api.get(`/admin/users/${userId}`);
    adminState.selectedUser = user;
    
    showUserModal(user, 'view');
    
  } catch (error) {
    console.error('Failed to load user:', error);
    showToast('Failed to load user details', 'error');
  }
}

function editUser(userId) {
  const user = adminState.users.find(u => u.id === userId);
  if (!user) return;
  
  adminState.selectedUser = user;
  showUserModal(user, 'edit');
}

function showUserModal(user, mode = 'view') {
  const modal = document.getElementById('userModal');
  const title = document.getElementById('userModalTitle');
  const body = document.getElementById('userModalBody');
  
  if (!modal || !body) return;
  
  title.textContent = mode === 'view' ? 'User Details' : 'Edit User';
  
  if (mode === 'view') {
    body.innerHTML = `
      <div class="user-detail-card">
        <div class="user-detail-header">
          <div class="user-avatar large">${getInitials(user.full_name || user.email)}</div>
          <div>
            <h3>${user.full_name || 'N/A'}</h3>
            <p>${user.email}</p>
          </div>
        </div>
        
        <div class="detail-grid">
          <div class="detail-item">
            <label>Role</label>
            <span class="role-badge role-${user.role}">${user.role}</span>
          </div>
          <div class="detail-item">
            <label>Status</label>
            <span class="status-badge status-${user.is_active ? 'active' : 'inactive'}">
              ${user.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
          <div class="detail-item">
            <label>Verified</label>
            <span>${user.is_verified ? '✓ Yes' : '✗ No'}</span>
          </div>
          <div class="detail-item">
            <label>Phone</label>
            <span>${user.phone || 'N/A'}</span>
          </div>
          <div class="detail-item">
            <label>Joined</label>
            <span>${formatDate(user.created_at)}</span>
          </div>
          <div class="detail-item">
            <label>Last Login</label>
            <span>${user.last_login ? formatDate(user.last_login) : 'Never'}</span>
          </div>
        </div>
      </div>
    `;
  } else {
    body.innerHTML = `
      <form id="editUserForm" onsubmit="saveUser(event)">
        <div class="form-group">
          <label>Full Name</label>
          <input type="text" name="full_name" value="${user.full_name || ''}" required>
        </div>
        <div class="form-group">
          <label>Email</label>
          <input type="email" name="email" value="${user.email}" disabled>
        </div>
        <div class="form-group">
          <label>Role</label>
          <select name="role" required>
            <option value="user" ${user.role === 'user' ? 'selected' : ''}>User</option>
            <option value="moderator" ${user.role === 'moderator' ? 'selected' : ''}>Moderator</option>
            <option value="admin" ${user.role === 'admin' ? 'selected' : ''}>Admin</option>
          </select>
        </div>
        <div class="form-group">
          <label>
            <input type="checkbox" name="is_active" ${user.is_active ? 'checked' : ''}>
            Active
          </label>
        </div>
        <div class="form-group">
          <label>
            <input type="checkbox" name="is_verified" ${user.is_verified ? 'checked' : ''}>
            Email Verified
          </label>
        </div>
        <div class="form-actions">
          <button type="button" class="btn btn-secondary" onclick="closeModal('userModal')">Cancel</button>
          <button type="submit" class="btn btn-primary">Save Changes</button>
        </div>
      </form>
    `;
  }
  
  modal.classList.add('active');
}

async function saveUser(event) {
  event.preventDefault();
  
  const api = window.ScamShieldAPI;
  const form = event.target;
  const userId = adminState.selectedUser?.id;
  
  if (!userId) return;
  
  const data = {
    role: form.role.value,
    is_active: form.is_active.checked,
    is_verified: form.is_verified.checked,
  };
  
  try {
    // Update role
    await api.put(`/admin/users/${userId}/role`, { role: data.role });
    
    // Update status
    if (!data.is_active) {
      await api.post(`/admin/users/${userId}/deactivate`, {});
    }
    
    showToast('User updated successfully', 'success');
    closeModal('userModal');
    loadUsers(adminState.currentPage, adminState.searchQuery);
    
  } catch (error) {
    console.error('Failed to update user:', error);
    showToast('Failed to update user', 'error');
  }
}

async function deactivateUser(userId) {
  if (!confirm('Are you sure you want to deactivate this user?')) return;
  
  const api = window.ScamShieldAPI;
  
  try {
    await api.post(`/admin/users/${userId}/deactivate`, {});
    showToast('User deactivated', 'success');
    loadUsers(adminState.currentPage, adminState.searchQuery);
  } catch (error) {
    console.error('Failed to deactivate user:', error);
    showToast('Failed to deactivate user', 'error');
  }
}

async function activateUser(userId) {
  const api = window.ScamShieldAPI;
  
  try {
    await api.post(`/admin/users/${userId}/activate`, {});
    showToast('User activated', 'success');
    loadUsers(adminState.currentPage, adminState.searchQuery);
  } catch (error) {
    console.error('Failed to activate user:', error);
    showToast('Failed to activate user', 'error');
  }
}

// ============================================
// SYSTEM STATS
// ============================================
async function loadSystemStats() {
  const api = window.ScamShieldAPI;
  
  try {
    const stats = await api.get('/admin/stats');
    adminState.stats = stats;
    renderSystemStats(stats);
  } catch (error) {
    console.error('Failed to load system stats:', error);
  }
}

function renderSystemStats(stats) {
  // Update stat cards
  updateStatCard('total-users', stats.total_users || 0);
  updateStatCard('active-users', stats.active_users || 0);
  updateStatCard('total-scans', stats.total_scans || 0);
  updateStatCard('threats-blocked', stats.threats_blocked || 0);
  
  // Update charts if they exist
  if (typeof Chart !== 'undefined') {
    renderStatsCharts(stats);
  }
}

function updateStatCard(id, value) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = formatNumber(value);
  }
}

function renderStatsCharts(stats) {
  // User growth chart
  const userChartEl = document.getElementById('userGrowthChart');
  if (userChartEl && stats.user_growth) {
    new Chart(userChartEl, {
      type: 'line',
      data: {
        labels: stats.user_growth.map(d => d.date),
        datasets: [{
          label: 'New Users',
          data: stats.user_growth.map(d => d.count),
          borderColor: '#e94560',
          backgroundColor: 'rgba(233, 69, 96, 0.1)',
          fill: true,
          tension: 0.4,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  }
  
  // Scam types chart
  const scamChartEl = document.getElementById('scamTypesChart');
  if (scamChartEl && stats.scam_types) {
    new Chart(scamChartEl, {
      type: 'doughnut',
      data: {
        labels: stats.scam_types.map(t => t.type),
        datasets: [{
          data: stats.scam_types.map(t => t.count),
          backgroundColor: [
            '#e94560',
            '#ff6b6b',
            '#ffa502',
            '#1dd1a1',
            '#54a0ff',
            '#5f27cd',
          ]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'right' }
        }
      }
    });
  }
}

// ============================================
// ACTIVE SESSIONS (HONEYPOT)
// ============================================
async function loadActiveSessions() {
  const api = window.ScamShieldAPI;
  
  try {
    const response = await api.get('/admin/sessions?status=active');
    adminState.sessions = response.items || [];
    renderSessions();
  } catch (error) {
    console.error('Failed to load sessions:', error);
  }
}

function renderSessions() {
  const container = document.getElementById('sessionsContainer');
  if (!container) return;
  
  if (adminState.sessions.length === 0) {
    container.innerHTML = '<p class="empty-state">No active sessions</p>';
    return;
  }
  
  container.innerHTML = adminState.sessions.map(session => `
    <div class="session-card">
      <div class="session-header">
        <span class="session-id">${session.session_id}</span>
        <span class="session-status status-${session.status}">${session.status}</span>
      </div>
      <div class="session-info">
        <div><strong>Scammer:</strong> ${session.scammer_phone || session.scammer_email || 'Unknown'}</div>
        <div><strong>Messages:</strong> ${session.message_count || 0}</div>
        <div><strong>Duration:</strong> ${formatDuration(session.duration_seconds)}</div>
        <div><strong>Started:</strong> ${formatDate(session.created_at)}</div>
      </div>
      <div class="session-actions">
        <button class="btn btn-sm" onclick="viewSession('${session.session_id}')">View Chat</button>
        <button class="btn btn-sm btn-danger" onclick="endSession('${session.session_id}')">End Session</button>
      </div>
    </div>
  `).join('');
}

async function viewSession(sessionId) {
  const api = window.ScamShieldAPI;
  
  try {
    const session = await api.get(`/admin/sessions/${sessionId}`);
    showSessionModal(session);
  } catch (error) {
    console.error('Failed to load session:', error);
    showToast('Failed to load session details', 'error');
  }
}

function showSessionModal(session) {
  const modal = document.getElementById('sessionModal');
  const body = document.getElementById('sessionModalBody');
  
  if (!modal || !body) return;
  
  body.innerHTML = `
    <div class="session-detail">
      <div class="session-meta">
        <p><strong>Session ID:</strong> ${session.session_id}</p>
        <p><strong>Scammer:</strong> ${session.scammer_phone || session.scammer_email || 'Unknown'}</p>
        <p><strong>Status:</strong> ${session.status}</p>
        <p><strong>Duration:</strong> ${formatDuration(session.duration_seconds)}</p>
      </div>
      <div class="chat-log">
        <h4>Chat History</h4>
        ${(session.messages || []).map(msg => `
          <div class="chat-message ${msg.role}">
            <div class="message-header">
              <span class="sender">${msg.role === 'scammer' ? '🦹 Scammer' : '🤖 Agent'}</span>
              <span class="time">${formatTime(msg.timestamp)}</span>
            </div>
            <div class="message-content">${msg.content}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
  
  modal.classList.add('active');
}

async function endSession(sessionId) {
  if (!confirm('Are you sure you want to end this session?')) return;
  
  const api = window.ScamShieldAPI;
  
  try {
    await api.post(`/admin/sessions/${sessionId}/end`, {});
    showToast('Session ended', 'success');
    loadActiveSessions();
  } catch (error) {
    console.error('Failed to end session:', error);
    showToast('Failed to end session', 'error');
  }
}

// ============================================
// MODALS
// ============================================
function setupModals() {
  // Close modal when clicking outside
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  });
  
  // Close modal buttons
  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modalId = btn.getAttribute('data-close-modal');
      closeModal(modalId);
    });
  });
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================
function getInitials(name) {
  if (!name) return '?';
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatTime(dateStr) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatDuration(seconds) {
  if (!seconds) return '0s';
  
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
}

function showLoading(containerId) {
  const container = document.getElementById(containerId);
  if (container) {
    container.innerHTML = `
      <tr>
        <td colspan="7" class="loading-state">
          <div class="spinner"></div>
          <p>Loading...</p>
        </td>
      </tr>
    `;
  }
}

function showToast(message, type = 'info') {
  // Remove existing toasts
  document.querySelectorAll('.toast').forEach(t => t.remove());
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-content">
      <span class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
      <span class="toast-message">${message}</span>
    </div>
  `;
  
  document.body.appendChild(toast);
  
  setTimeout(() => toast.classList.add('show'), 10);
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Export for external use
window.AdminPanel = {
  loadUsers,
  loadSystemStats,
  loadActiveSessions,
  viewUser,
  editUser,
  deactivateUser,
  activateUser,
  viewSession,
  endSession,
};
