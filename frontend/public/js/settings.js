/**
 * ScamShield Pro - Settings Management
 * Handles user settings, preferences, and account management
 */

// ============================================
// STATE
// ============================================
const settingsState = {
  user: null,
  settings: null,
  subscription: null,
  isLoading: false,
};

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  initSettings();
});

async function initSettings() {
  const api = window.ScamShieldAPI;
  
  if (!api || !api.isAuthenticated()) {
    return; // Will be handled by main dashboard auth check
  }
  
  settingsState.user = api.getUser();
  
  // Setup form handlers
  setupProfileForm();
  setupPreferencesForm();
  setupSecurityForm();
  setupNotificationForm();
  setupDangerZone();
  
  // Load settings data
  await Promise.all([
    loadUserProfile(),
    loadUserSettings(),
    loadSubscription(),
  ]);
}

// ============================================
// DATA LOADING
// ============================================
async function loadUserProfile() {
  const api = window.ScamShieldAPI;
  
  try {
    const profile = await api.getProfile();
    settingsState.user = profile;
    populateProfileForm(profile);
  } catch (error) {
    console.error('Failed to load profile:', error);
  }
}

async function loadUserSettings() {
  const api = window.ScamShieldAPI;
  
  try {
    const settings = await api.getSettings();
    settingsState.settings = settings;
    populateSettingsForm(settings);
  } catch (error) {
    console.error('Failed to load settings:', error);
  }
}

async function loadSubscription() {
  const api = window.ScamShieldAPI;
  
  try {
    const subscription = await api.getSubscription();
    settingsState.subscription = subscription;
    displaySubscriptionInfo(subscription);
  } catch (error) {
    console.error('Failed to load subscription:', error);
    // Show free plan info
    displaySubscriptionInfo(null);
  }
}

// ============================================
// PROFILE FORM
// ============================================
function setupProfileForm() {
  const form = document.getElementById('profileForm');
  if (!form) return;
  
  form.addEventListener('submit', handleProfileUpdate);
}

function populateProfileForm(profile) {
  const nameInput = document.getElementById('settingsName');
  const emailInput = document.getElementById('settingsEmail');
  const phoneInput = document.getElementById('settingsPhone');
  
  if (nameInput) nameInput.value = profile.full_name || '';
  if (emailInput) emailInput.value = profile.email || '';
  if (phoneInput) phoneInput.value = profile.phone || '';
  
  // Update header display
  const userNameEl = document.getElementById('userName');
  const userInitialsEl = document.getElementById('userInitials');
  
  if (userNameEl) userNameEl.textContent = profile.full_name || profile.email.split('@')[0];
  if (userInitialsEl) {
    const name = profile.full_name || profile.email;
    userInitialsEl.textContent = name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  }
}

async function handleProfileUpdate(event) {
  event.preventDefault();
  
  const api = window.ScamShieldAPI;
  const form = event.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalText = submitBtn.innerHTML;
  
  const data = {
    full_name: document.getElementById('settingsName')?.value,
    phone: document.getElementById('settingsPhone')?.value || null,
  };
  
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> Saving...';
  
  try {
    const updated = await api.updateProfile(data);
    settingsState.user = updated;
    api.setUser(updated);
    
    showToast('Profile updated successfully', 'success');
    populateProfileForm(updated);
  } catch (error) {
    showToast(error.message || 'Failed to update profile', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
  }
}

// ============================================
// PREFERENCES FORM
// ============================================
function setupPreferencesForm() {
  const form = document.getElementById('preferencesForm');
  if (!form) return;
  
  form.addEventListener('submit', handlePreferencesUpdate);
}

function populateSettingsForm(settings) {
  // Auto-block toggle
  const autoBlockToggle = document.getElementById('autoBlockToggle');
  if (autoBlockToggle) autoBlockToggle.checked = settings.auto_block;
  
  // Sensitivity selector
  const sensitivitySelect = document.getElementById('sensitivitySelect');
  if (sensitivitySelect) sensitivitySelect.value = settings.sensitivity || 'medium';
  
  // Language
  const languageSelect = document.getElementById('languageSelect');
  if (languageSelect) languageSelect.value = settings.language || 'en';
  
  // Timezone
  const timezoneSelect = document.getElementById('timezoneSelect');
  if (timezoneSelect) timezoneSelect.value = settings.timezone || 'UTC';
  
  // Populate notification settings
  populateNotificationSettings(settings);
}

async function handlePreferencesUpdate(event) {
  event.preventDefault();
  
  const api = window.ScamShieldAPI;
  const form = event.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalText = submitBtn.innerHTML;
  
  const data = {
    auto_block: document.getElementById('autoBlockToggle')?.checked,
    sensitivity: document.getElementById('sensitivitySelect')?.value,
    language: document.getElementById('languageSelect')?.value,
    timezone: document.getElementById('timezoneSelect')?.value,
  };
  
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> Saving...';
  
  try {
    const updated = await api.updateSettings(data);
    settingsState.settings = updated;
    
    showToast('Preferences saved', 'success');
  } catch (error) {
    showToast(error.message || 'Failed to save preferences', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
  }
}

// ============================================
// NOTIFICATION SETTINGS
// ============================================
function setupNotificationForm() {
  const form = document.getElementById('notificationForm');
  if (!form) return;
  
  form.addEventListener('submit', handleNotificationUpdate);
}

function populateNotificationSettings(settings) {
  const emailAlerts = document.getElementById('emailAlerts');
  const smsAlerts = document.getElementById('smsAlerts');
  const pushNotifications = document.getElementById('pushNotifications');
  const weeklyReport = document.getElementById('weeklyReport');
  const instantAlerts = document.getElementById('instantAlerts');
  
  if (emailAlerts) emailAlerts.checked = settings.email_alerts;
  if (smsAlerts) smsAlerts.checked = settings.sms_alerts;
  if (pushNotifications) pushNotifications.checked = settings.push_notifications;
  if (weeklyReport) weeklyReport.checked = settings.weekly_report;
  if (instantAlerts) instantAlerts.checked = settings.instant_alerts;
}

async function handleNotificationUpdate(event) {
  event.preventDefault();
  
  const api = window.ScamShieldAPI;
  const form = event.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalText = submitBtn.innerHTML;
  
  const data = {
    email_alerts: document.getElementById('emailAlerts')?.checked,
    sms_alerts: document.getElementById('smsAlerts')?.checked,
    push_notifications: document.getElementById('pushNotifications')?.checked,
    weekly_report: document.getElementById('weeklyReport')?.checked,
    instant_alerts: document.getElementById('instantAlerts')?.checked,
  };
  
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> Saving...';
  
  try {
    const updated = await api.updateSettings(data);
    settingsState.settings = updated;
    
    showToast('Notification settings saved', 'success');
  } catch (error) {
    showToast(error.message || 'Failed to save notifications', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
  }
}

// ============================================
// SECURITY SETTINGS
// ============================================
function setupSecurityForm() {
  const form = document.getElementById('passwordForm');
  if (!form) return;
  
  form.addEventListener('submit', handlePasswordChange);
}

async function handlePasswordChange(event) {
  event.preventDefault();
  
  const api = window.ScamShieldAPI;
  const form = event.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalText = submitBtn.innerHTML;
  
  const currentPassword = document.getElementById('currentPassword')?.value;
  const newPassword = document.getElementById('newPassword')?.value;
  const confirmPassword = document.getElementById('confirmNewPassword')?.value;
  
  // Validation
  if (!currentPassword || !newPassword) {
    showToast('Please fill in all password fields', 'error');
    return;
  }
  
  if (newPassword.length < 8) {
    showToast('New password must be at least 8 characters', 'error');
    return;
  }
  
  if (newPassword !== confirmPassword) {
    showToast('New passwords do not match', 'error');
    return;
  }
  
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> Updating...';
  
  try {
    await api.changePassword(currentPassword, newPassword);
    
    showToast('Password changed successfully', 'success');
    form.reset();
  } catch (error) {
    showToast(error.message || 'Failed to change password', 'error');
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
  }
}

// ============================================
// SUBSCRIPTION DISPLAY
// ============================================
function displaySubscriptionInfo(subscription) {
  const container = document.getElementById('subscriptionInfo');
  if (!container) return;
  
  if (!subscription) {
    container.innerHTML = `
      <div class="subscription-card free">
        <div class="plan-header">
          <span class="plan-badge">FREE</span>
          <h3>Free Plan</h3>
        </div>
        <div class="plan-features">
          <p>✓ 10 scans per day</p>
          <p>✓ Basic threat detection</p>
          <p>✓ Email alerts</p>
        </div>
        <div class="plan-action">
          <button class="btn btn-primary" onclick="showUpgradeModal()">
            Upgrade to Pro
          </button>
        </div>
      </div>
    `;
    return;
  }
  
  container.innerHTML = `
    <div class="subscription-card ${subscription.plan_tier}">
      <div class="plan-header">
        <span class="plan-badge">${subscription.plan_tier.toUpperCase()}</span>
        <h3>${subscription.plan_name || subscription.plan_tier} Plan</h3>
      </div>
      <div class="plan-details">
        <div class="usage-stat">
          <span class="label">Status</span>
          <span class="value status-${subscription.status}">${subscription.status}</span>
        </div>
        <div class="usage-stat">
          <span class="label">Scans Today</span>
          <span class="value">${subscription.scans_today || 0} / ${subscription.daily_limit || '∞'}</span>
        </div>
        <div class="usage-stat">
          <span class="label">Scans This Month</span>
          <span class="value">${subscription.scans_this_month || 0}</span>
        </div>
        ${subscription.expires_at ? `
          <div class="usage-stat">
            <span class="label">Renews On</span>
            <span class="value">${formatDate(subscription.expires_at)}</span>
          </div>
        ` : ''}
      </div>
      ${subscription.plan_tier !== 'enterprise' ? `
        <div class="plan-action">
          <button class="btn btn-secondary" onclick="showUpgradeModal()">
            Upgrade Plan
          </button>
        </div>
      ` : ''}
    </div>
  `;
}

async function showUpgradeModal() {
  const api = window.ScamShieldAPI;
  
  try {
    const { plans } = await api.getPlans();
    
    const modal = document.getElementById('upgradeModal');
    const body = document.getElementById('upgradeModalBody');
    
    if (!modal || !body) return;
    
    body.innerHTML = `
      <div class="plans-grid">
        ${plans.filter(p => p.tier !== 'free').map(plan => `
          <div class="plan-option ${plan.tier}">
            <div class="plan-name">${plan.name}</div>
            <div class="plan-price">
              ₹${plan.price}<span>/month</span>
            </div>
            <ul class="plan-features-list">
              ${plan.features.map(f => `<li>✓ ${f}</li>`).join('')}
            </ul>
            <button class="btn btn-primary" onclick="subscribeToPlan('${plan.id}')">
              Select Plan
            </button>
          </div>
        `).join('')}
      </div>
    `;
    
    modal.classList.add('active');
  } catch (error) {
    showToast('Failed to load plans', 'error');
  }
}

async function subscribeToPlan(planId) {
  const api = window.ScamShieldAPI;
  
  try {
    const subscription = await api.subscribe(planId);
    settingsState.subscription = subscription;
    displaySubscriptionInfo(subscription);
    
    closeModal('upgradeModal');
    showToast('Successfully subscribed! Enjoy your new features.', 'success');
  } catch (error) {
    showToast(error.message || 'Subscription failed', 'error');
  }
}

// ============================================
// DANGER ZONE
// ============================================
function setupDangerZone() {
  const deleteBtn = document.getElementById('deleteAccountBtn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', showDeleteConfirmation);
  }
  
  const exportBtn = document.getElementById('exportDataBtn');
  if (exportBtn) {
    exportBtn.addEventListener('click', exportUserData);
  }
}

function showDeleteConfirmation() {
  const modal = document.getElementById('deleteConfirmModal');
  if (!modal) {
    if (confirm('Are you sure you want to delete your account? This cannot be undone.')) {
      deleteAccount();
    }
    return;
  }
  
  modal.classList.add('active');
}

async function deleteAccount() {
  const api = window.ScamShieldAPI;
  
  const confirmInput = document.getElementById('deleteConfirmInput');
  if (confirmInput && confirmInput.value !== 'DELETE') {
    showToast('Please type DELETE to confirm', 'error');
    return;
  }
  
  try {
    await api.delete('/users/me');
    
    // Logout and redirect
    api.clearTokens();
    showToast('Account deleted successfully', 'success');
    
    setTimeout(() => {
      window.location.href = './index.html';
    }, 1500);
  } catch (error) {
    showToast(error.message || 'Failed to delete account', 'error');
  }
}

async function exportUserData() {
  const api = window.ScamShieldAPI;
  
  showToast('Preparing your data export...', 'info');
  
  try {
    // Collect all user data
    const [profile, settings, scansResponse, stats] = await Promise.all([
      api.getProfile(),
      api.getSettings(),
      api.getScanHistory(1, 1000),
      api.getStats(),
    ]);
    
    const exportData = {
      exported_at: new Date().toISOString(),
      profile,
      settings,
      scan_history: scansResponse.scans || scansResponse.items || [],
      statistics: stats,
    };
    
    // Create download
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `scamshield_export_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    URL.revokeObjectURL(url);
    
    showToast('Data exported successfully!', 'success');
  } catch (error) {
    showToast('Failed to export data', 'error');
  }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================
function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
}

function showToast(message, type = 'info') {
  // Use existing showToast from dashboard or create new one
  if (typeof window.showToast === 'function') {
    window.showToast(message, type);
    return;
  }
  
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
window.Settings = {
  loadUserProfile,
  loadUserSettings,
  loadSubscription,
  showUpgradeModal,
  subscribeToPlan,
  exportUserData,
};
