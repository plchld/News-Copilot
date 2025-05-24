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
        
        this.setLoading(this.apiKeyButton, true);
        
        try {
            // Validate API key with backend
            const response = await fetch(`${BACKEND_URL}/api/auth/validate-api-key`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({ api_key: apiKey })
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
                token: apiKey,
                user: { email: 'API Key User', is_api_key: true },
                expiresAt: expiresAt
            });
            
            this.showMessage('Επιτυχής σύνδεση με API Key!', 'success');
            
            // Clear the input
            this.apiKeyInput.value = '';
            
            // Load profile and show authenticated view
            this.currentUser = { email: 'API Key User', is_api_key: true };
            await this.loadUserProfile(apiKey);
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
            const response = await fetch(`${BACKEND_URL}/api/auth/profile`, {
                headers: {
                    'Authorization': `Bearer ${token}`
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
                    
                    // Update usage
                    const basicPercent = (this.currentProfile.basic_analysis_count / this.currentProfile.basic_analysis_limit) * 100;
                    const deepPercent = (this.currentProfile.deep_analysis_count / this.currentProfile.deep_analysis_limit) * 100;
                    
                    this.basicUsage.textContent = `${this.currentProfile.basic_analysis_count} / ${this.currentProfile.basic_analysis_limit}`;
                    this.deepUsage.textContent = `${this.currentProfile.deep_analysis_count} / ${this.currentProfile.deep_analysis_limit}`;
                    
                    this.basicUsageBar.style.width = `${Math.min(basicPercent, 100)}%`;
                    this.deepUsageBar.style.width = `${Math.min(deepPercent, 100)}%`;
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
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AuthManager();
});