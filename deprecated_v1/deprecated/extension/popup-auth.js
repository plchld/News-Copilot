// extension/popup-auth.js
// Simplified authentication popup for News Copilot Chrome Extension

const SUPABASE_URL = 'https://zzweleyslkxemrwmlbri.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp6d2VsZXlzbGt4ZW1yd21sYnJpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwMTY5MzMsImV4cCI6MjA2MzU5MjkzM30.5-N5bCXYc_uBr-1EQsUajyp-UXxZW_s3BIXJm-GS1ek';
const BACKEND_URL = 'https://news-copilot.vercel.app';

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.currentProfile = null;
        this.initializeElements();
        this.setupEventListeners();
        this.checkAuthState();
    }

    initializeElements() {
        // Views
        this.loginView = document.getElementById('loginView');
        this.authenticatedView = document.getElementById('authenticatedView');
        this.loadingView = document.getElementById('loadingView');
        
        // Login elements
        this.emailInput = document.getElementById('emailInput');
        this.magicLinkButton = document.getElementById('magicLinkButton');
        this.apiKeyInput = document.getElementById('apiKeyInput');
        this.apiKeyButton = document.getElementById('apiKeyButton');
        this.authMessage = document.getElementById('authMessage');
        
        // Authenticated view elements
        this.userEmail = document.getElementById('userEmail');
        this.tierName = document.getElementById('tierName');
        this.logoutButton = document.getElementById('logoutButton');
        this.refreshButton = document.getElementById('refreshButton');
        
        // Usage elements
        this.basicUsage = document.getElementById('basicUsage');
        this.deepUsage = document.getElementById('deepUsage');
        this.basicUsageBar = document.getElementById('basicUsageBar');
        this.deepUsageBar = document.getElementById('deepUsageBar');
    }

    setupEventListeners() {
        this.magicLinkButton.addEventListener('click', () => this.sendMagicLink());
        this.apiKeyButton.addEventListener('click', () => this.authenticateWithApiKey());
        this.logoutButton.addEventListener('click', () => this.logout());
        
        // Add refresh button listener
        if (this.refreshButton) {
            this.refreshButton.addEventListener('click', () => this.refreshUsageStats());
        }
        
        this.emailInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMagicLink();
            }
        });
        
        this.apiKeyInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.authenticateWithApiKey();
            }
        });

        // Listen for auth state changes from background
        chrome.runtime.onMessage.addListener((message) => {
            if (message.type === 'AUTH_STATE_CHANGED') {
                this.handleAuthStateChange(message.authState);
            }
        });

        // Check auth state when popup gains focus
        window.addEventListener('focus', () => {
            this.checkAuthState();
        });
    }

    async checkAuthState() {
        this.showLoading();
        
        try {
            // Get auth state from background script
            const response = await chrome.runtime.sendMessage({ type: 'GET_AUTH_STATE' });
            
            if (response.authState && response.authState.token && response.authState.expiresAt > Date.now()) {
                // User is authenticated
                this.currentUser = response.authState.user;
                await this.loadUserProfile(response.authState.token);
                this.showAuthenticatedView();
            } else {
                // Not authenticated
                this.showLoginView();
            }
        } catch (error) {
            console.error('Error checking auth state:', error);
            this.showLoginView();
        }
    }

    handleAuthStateChange(authState) {
        if (authState.token && authState.expiresAt > Date.now()) {
            this.currentUser = authState.user;
            this.loadUserProfile(authState.token).then(() => {
                this.showAuthenticatedView();
            });
        } else {
            this.showLoginView();
        }
    }

    async sendMagicLink() {
        const email = this.emailInput.value.trim();
        
        if (!email || !this.isValidEmail(email)) {
            this.showMessage('Παρακαλώ εισάγετε έγκυρη διεύθυνση email', 'error');
            return;
        }

        this.setLoading(this.magicLinkButton, true);
        this.showMessage('Αποστολή magic link...', 'info');

        try {
            const response = await fetch(`${SUPABASE_URL}/auth/v1/otp`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'apikey': SUPABASE_ANON_KEY,
                    'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
                },
                body: JSON.stringify({
                    email: email,
                    options: {
                        emailRedirectTo: `${BACKEND_URL}/auth/callback`
                    }
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.msg || 'Failed to send magic link');
            }

            this.showMessage('📧 Magic link στάλθηκε! Ελέγξτε το email σας.', 'success');
            this.emailInput.value = '';
            
        } catch (error) {
            console.error('Error sending magic link:', error);
            this.showMessage(`Σφάλμα: ${error.message}`, 'error');
        } finally {
            this.setLoading(this.magicLinkButton, false);
        }
    }

    async authenticateWithApiKey() {
        const apiKey = this.apiKeyInput.value.trim();
        
        if (!apiKey) {
            this.showMessage('Παρακαλώ εισάγετε το API Key σας', 'error');
            return;
        }
        
        // Check for non-ASCII characters
        if (apiKey !== apiKey.replace(/[^\x00-\x7F]/g, "")) {
            this.showMessage('Το API Key περιέχει μη έγκυρους χαρακτήρες. Θα αφαιρεθούν αυτόματα.', 'warning');
        }
        
        this.setLoading(this.apiKeyButton, true);
        
        try {
            // Validate API key with backend
            // Ensure the API key only contains ASCII characters
            const cleanApiKey = apiKey.replace(/[^\x00-\x7F]/g, "");
            
            const response = await fetch(`${BACKEND_URL}/api/auth/validate-api-key`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${cleanApiKey}`
                },
                body: JSON.stringify({ api_key: cleanApiKey })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Invalid API key');
            }

            const data = await response.json();
            
            // Store auth state in background script
            const expiresAt = Date.now() + (24 * 60 * 60 * 1000); // 24 hours
            await chrome.runtime.sendMessage({
                type: 'SET_AUTH_STATE',
                token: cleanApiKey,
                user: { email: 'API Key User', is_api_key: true },
                expiresAt: expiresAt
            });
            
            this.showMessage('Επιτυχής σύνδεση με API Key!', 'success');
            
            // Clear the input
            this.apiKeyInput.value = '';
            
            // Load profile and show authenticated view
            this.currentUser = { email: 'API Key User', is_api_key: true };
            await this.loadUserProfile(cleanApiKey);
            this.showAuthenticatedView();
            
        } catch (error) {
            console.error('Error authenticating with API key:', error);
            this.showMessage(`Σφάλμα: ${error.message}`, 'error');
        } finally {
            this.setLoading(this.apiKeyButton, false);
        }
    }

    async loadUserProfile(token) {
        try {
            // Ensure token only contains ASCII characters
            const cleanToken = token.replace(/[^\x00-\x7F]/g, "");
            
            const response = await fetch(`${BACKEND_URL}/api/auth/profile`, {
                headers: {
                    'Authorization': `Bearer ${cleanToken}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load profile');
            }

            const data = await response.json();
            this.currentProfile = data;
            
        } catch (error) {
            console.error('Error loading profile:', error);
            // Continue anyway, profile is not critical
        }
    }

    async logout() {
        try {
            await chrome.runtime.sendMessage({ type: 'CLEAR_AUTH' });
            this.currentUser = null;
            this.currentProfile = null;
            this.showLoginView();
        } catch (error) {
            console.error('Error logging out:', error);
        }
    }

    showLoginView() {
        this.hideAllViews();
        this.loginView.classList.remove('hidden');
    }

    showAuthenticatedView() {
        this.hideAllViews();
        this.authenticatedView.classList.remove('hidden');
        
        // Update UI with user info
        if (this.currentUser) {
            if (this.currentUser.is_api_key) {
                this.userEmail.textContent = 'API Key Authentication';
                this.tierName.textContent = 'API Key';
                
                // Hide usage stats for API key users
                const usageSection = document.querySelector('.usage-section');
                if (usageSection) {
                    usageSection.style.display = 'none';
                }
            } else {
                this.userEmail.textContent = this.currentUser.email || 'User';
                
                // Show usage stats for regular users
                const usageSection = document.querySelector('.usage-section');
                if (usageSection) {
                    usageSection.style.display = 'block';
                }
                
                if (this.currentProfile) {
                    this.tierName.textContent = this.getTierDisplayName(this.currentProfile.tier);
                    
                    // Update usage based on the new API structure
                    const usage = this.currentProfile.usage_this_month || { basic_analysis: 0, deep_analysis: 0 };
                    const limits = this.currentProfile.usage_limits || { basic_analysis: 10, deep_analysis: 0 };
                    
                    // Calculate percentages
                    const basicPercent = limits.basic_analysis > 0 
                        ? (usage.basic_analysis / limits.basic_analysis) * 100 
                        : 0;
                    const deepPercent = limits.deep_analysis > 0 
                        ? (usage.deep_analysis / limits.deep_analysis) * 100 
                        : 0;
                    
                    // Format limits for display
                    const basicLimit = limits.basic_analysis >= 999999 ? '∞' : limits.basic_analysis;
                    const deepLimit = limits.deep_analysis >= 999999 ? '∞' : limits.deep_analysis;
                    
                    // Update text displays
                    this.basicUsage.textContent = `${usage.basic_analysis} / ${basicLimit}`;
                    this.deepUsage.textContent = `${usage.deep_analysis} / ${deepLimit}`;
                    
                    // Update progress bars
                    this.basicUsageBar.style.width = `${Math.min(basicPercent, 100)}%`;
                    this.deepUsageBar.style.width = `${Math.min(deepPercent, 100)}%`;
                    
                    // Change bar color if approaching limit using CSS classes
                    this.basicUsageBar.classList.remove('warning', 'danger');
                    if (basicPercent >= 90) {
                        this.basicUsageBar.classList.add('danger');
                    } else if (basicPercent >= 75) {
                        this.basicUsageBar.classList.add('warning');
                    }
                    
                    this.deepUsageBar.classList.remove('warning', 'danger');
                    if (deepPercent >= 90) {
                        this.deepUsageBar.classList.add('danger');
                    } else if (deepPercent >= 75) {
                        this.deepUsageBar.classList.add('warning');
                    }
                    
                    // Hide deep analysis section if user has no deep analysis allowance
                    const deepUsageItem = this.deepUsageBar.closest('.usage-item');
                    if (deepUsageItem) {
                        deepUsageItem.style.display = limits.deep_analysis > 0 ? 'block' : 'none';
                    }
                    
                    // Show tier-specific information
                    this.updateTierInfo(profile.tier, usage, limits);
                }
            }
        }
    }

    showLoading() {
        this.hideAllViews();
        this.loadingView.classList.remove('hidden');
    }

    hideAllViews() {
        this.loginView.classList.add('hidden');
        this.authenticatedView.classList.add('hidden');
        this.loadingView.classList.add('hidden');
    }

    showMessage(message, type = 'info') {
        this.authMessage.textContent = message;
        this.authMessage.className = `auth-message ${type}`;
        this.authMessage.classList.remove('hidden');
        
        if (type === 'success') {
            setTimeout(() => {
                this.authMessage.classList.add('hidden');
            }, 5000);
        }
    }

    setLoading(button, loading) {
        button.disabled = loading;
        if (loading) {
            button.textContent = 'Αποστολή...';
        } else {
            button.textContent = 'Αποστολή Magic Link';
        }
    }

    getTierDisplayName(tier) {
        const tierNames = {
            'free': 'Δωρεάν',
            'pro': 'Pro',
            'premium': 'Premium',
            'byok': 'BYOK'
        };
        return tierNames[tier] || tier;
    }

    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }
    
    updateTierInfo(tier, usage, limits) {
        const tierInfoElement = document.getElementById('tierInfo');
        if (!tierInfoElement) return;
        
        // Calculate remaining usage
        const basicRemaining = Math.max(0, limits.basic_analysis - usage.basic_analysis);
        const deepRemaining = Math.max(0, limits.deep_analysis - usage.deep_analysis);
        
        let infoHtml = '';
        
        // Check if user is running out of analyses
        if (tier === 'free') {
            if (basicRemaining <= 2 && basicRemaining > 0) {
                infoHtml = `⚠️ Απομένουν μόνο ${basicRemaining} βασικές αναλύσεις αυτόν τον μήνα.`;
            } else if (basicRemaining === 0) {
                infoHtml = `❌ Έχετε εξαντλήσει τις δωρεάν αναλύσεις σας. <a href="#" class="upgrade-link" onclick="window.open('${BACKEND_URL}/pricing', '_blank'); return false;">Αναβάθμιση σε Pro</a>`;
            }
        } else if (tier === 'pro' || tier === 'premium') {
            const totalRemaining = basicRemaining + deepRemaining;
            if (totalRemaining <= 5 && totalRemaining > 0) {
                infoHtml = `⚠️ Πλησιάζετε το μηνιαίο όριο αναλύσεων.`;
            } else if (totalRemaining === 0) {
                infoHtml = `❌ Έχετε εξαντλήσει όλες τις αναλύσεις σας αυτόν τον μήνα.`;
            }
        }
        
        // Show/hide tier info
        if (infoHtml) {
            tierInfoElement.innerHTML = infoHtml;
            tierInfoElement.classList.remove('hidden');
        } else {
            tierInfoElement.classList.add('hidden');
        }
    }
    
    async refreshUsageStats() {
        // Show loading state on refresh button
        if (this.refreshButton) {
            const originalText = this.refreshButton.textContent;
            this.refreshButton.textContent = '⟳';
            this.refreshButton.disabled = true;
            
            try {
                // Get current auth state
                const response = await chrome.runtime.sendMessage({ type: 'GET_AUTH_STATE' });
                
                if (response.authState && response.authState.token) {
                    // Reload user profile to get fresh usage stats
                    await this.loadUserProfile(response.authState.token);
                    
                    // Update the display
                    if (this.currentProfile) {
                        this.showAuthenticatedView();
                    }
                }
            } catch (error) {
                console.error('Error refreshing usage stats:', error);
            } finally {
                // Restore button state
                setTimeout(() => {
                    if (this.refreshButton) {
                        this.refreshButton.textContent = originalText;
                        this.refreshButton.disabled = false;
                    }
                }, 500);
            }
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AuthManager();
});