// extension/popup-supabase.js
// Popup script for Supabase authentication - Chrome Extension compatible

// Configuration - Your actual Supabase credentials
const SUPABASE_URL = 'https://zzweleyslkxemrwmlbri.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp6d2VsZXlzbGt4ZW1yd21sYnJpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwMTY5MzMsImV4cCI6MjA2MzU5MjkzM30.5-N5bCXYc_uBr-1EQsUajyp-UXxZW_s3BIXJm-GS1ek'
const BACKEND_URL = 'https://news-copilot.vercel.app'

// Simple Supabase client replacement for Chrome extension
class SimpleSupabaseClient {
    constructor(url, key) {
        this.url = url;
        this.key = key;
    }

    async signInWithOtp(options) {
        try {
            const response = await fetch(`${this.url}/auth/v1/otp`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'apikey': this.key,
                    'Authorization': `Bearer ${this.key}`
                },
                body: JSON.stringify({
                    email: options.email,
                    options: options.options || {}
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.msg || `HTTP ${response.status}`);
            }

            const data = await response.json();
            return { data, error: null };
        } catch (error) {
            return { data: null, error };
        }
    }

    async getSession() {
        try {
            // For now, just return empty session since we're using magic links
            return { data: { session: null }, error: null };
        } catch (error) {
            return { data: { session: null }, error };
        }
    }

    // Auth state change listener (simplified)
    onAuthStateChange(callback) {
        // For now, we'll implement this as needed
        return { data: { subscription: null } };
    }

    get auth() {
        return {
            signInWithOtp: this.signInWithOtp.bind(this),
            getSession: this.getSession.bind(this),
            onAuthStateChange: this.onAuthStateChange.bind(this),
            signOut: async () => ({ error: null })
        };
    }
}

// Initialize Supabase client
const supabase = new SimpleSupabaseClient(SUPABASE_URL, SUPABASE_ANON_KEY);

class NewscopilotAuth {
    constructor() {
        this.currentUser = null;
        this.currentSession = null;
        
        this.initializeUI();
        this.setupEventListeners();
        this.checkAuthState();
    }
    
    initializeUI() {
        // Get DOM elements
        this.loadingView = document.getElementById('loadingView');
        this.loginForm = document.getElementById('loginForm');
        this.emailSentView = document.getElementById('emailSentView');
        this.authenticatedView = document.getElementById('authenticatedView');
        
        this.emailInput = document.getElementById('emailInput');
        this.magicLinkButton = document.getElementById('magicLinkButton');
        this.resendButton = document.getElementById('resendButton');
        this.backToLoginButton = document.getElementById('backToLoginButton');
        this.logoutButton = document.getElementById('logoutButton');
        this.apiKeyInput = document.getElementById('apiKeyInput');
        this.apiKeyButton = document.getElementById('apiKeyButton');
        
        this.authMessage = document.getElementById('authMessage');
        this.apiKeyMessage = document.getElementById('apiKeyMessage');
        this.userEmail = document.getElementById('userEmail');
        this.tierName = document.getElementById('tierName');
        this.basicUsage = document.getElementById('basicUsage');
        this.deepUsage = document.getElementById('deepUsage');
        this.basicUsageBar = document.getElementById('basicUsageBar');
        this.deepUsageBar = document.getElementById('deepUsageBar');
    }
    
    setupEventListeners() {
        this.magicLinkButton.addEventListener('click', () => this.sendMagicLink());
        this.resendButton.addEventListener('click', () => this.sendMagicLink());
        this.backToLoginButton.addEventListener('click', () => this.showLoginForm());
        this.logoutButton.addEventListener('click', () => this.signOut());
        this.apiKeyButton.addEventListener('click', () => this.updateApiKey());
        
        // Listen for Enter key in email input
        this.emailInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMagicLink();
            }
        });
    }
    
    async checkAuthState() {
        try {
            const { data: { session }, error } = await supabase.auth.getSession();
            
            if (error) {
                console.error('Error checking session:', error);
                this.showLoginForm();
                return;
            }
            
            this.currentSession = session;
            this.currentUser = session?.user || null;
            
            if (session && this.currentUser) {
                await this.loadUserProfile();
                this.showAuthenticatedView();
            } else {
                this.showLoginForm();
            }
        } catch (error) {
            console.error('Error checking auth state:', error);
            this.showLoginForm();
        }
    }
    
    async sendMagicLink() {
        const email = this.emailInput.value.trim();
        
        if (!email) {
            this.showMessage('Παρακαλώ εισάγετε το email σας', 'error');
            return;
        }
        
        if (!this.isValidEmail(email)) {
            this.showMessage('Παρακαλώ εισάγετε έγκυρη διεύθυνση email', 'error');
            return;
        }
        
        this.setLoading(this.magicLinkButton, true);
        
        try {
            const { data, error } = await supabase.auth.signInWithOtp({
                email: email,
                options: {
                    emailRedirectTo: `${BACKEND_URL}/auth/callback`
                }
            });
            
            if (error) throw error;
            
            this.showMessage('Magic link στάλθηκε στο email σας!', 'success');
            this.showEmailSentView();
            
        } catch (error) {
            console.error('Error sending magic link:', error);
            this.showMessage(`Σφάλμα δικτύου: ${error.message}`, 'error');
        } finally {
            this.setLoading(this.magicLinkButton, false);
        }
    }
    
    async signOut() {
        this.setLoading(this.logoutButton, true);
        
        try {
            const { error } = await supabase.auth.signOut();
            if (error) throw error;
            
            this.currentSession = null;
            this.currentUser = null;
            this.showLoginForm();
            
        } catch (error) {
            console.error('Error signing out:', error);
            this.showMessage(`Σφάλμα αποσύνδεσης: ${error.message}`, 'error');
        } finally {
            this.setLoading(this.logoutButton, false);
        }
    }
    
    async loadUserProfile() {
        if (!this.currentSession) return;
        
        try {
            const response = await fetch(`${BACKEND_URL}/api/auth/profile`, {
                headers: {
                    'Authorization': `Bearer ${this.currentSession.access_token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const profile = await response.json();
            this.updateProfileUI(profile);
            
        } catch (error) {
            console.error('Error loading profile:', error);
            this.showMessage('Σφάλμα φόρτωσης προφίλ', 'error');
        }
    }
    
    async updateApiKey() {
        const apiKey = this.apiKeyInput.value.trim();
        
        if (!this.currentSession) {
            this.showApiKeyMessage('Δεν είστε συνδεδεμένος', 'error');
            return;
        }
        
        this.setLoading(this.apiKeyButton, true);
        
        try {
            const response = await fetch(`${BACKEND_URL}/api/auth/update-api-key`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.currentSession.access_token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ api_key: apiKey })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (apiKey) {
                this.showApiKeyMessage('API Key αποθηκεύτηκε! Τώρα έχετε απεριόριστη χρήση.', 'success');
            } else {
                this.showApiKeyMessage('API Key αφαιρέθηκε. Επιστροφή στο δωρεάν πλάνο.', 'info');
            }
            
            // Reload profile to update usage limits
            await this.loadUserProfile();
            
        } catch (error) {
            console.error('Error updating API key:', error);
            this.showApiKeyMessage(`Σφάλμα: ${error.message}`, 'error');
        } finally {
            this.setLoading(this.apiKeyButton, false);
        }
    }
    
    updateProfileUI(profile) {
        this.userEmail.textContent = profile.email;
        
        // Update tier display
        const tierNames = {
            'free': 'Free Plan',
            'pro': 'Pro Plan (€8.99/μήνα)',
            'premium': 'Premium Plan (€24.99/μήνα)',
            'byok': 'Προσωπικό API Key',
            'admin': 'Admin'
        };
        this.tierName.textContent = tierNames[profile.tier] || profile.tier;
        
        // Update usage stats
        const usage = profile.usage_this_month;
        const limits = profile.usage_limits;
        
        this.basicUsage.textContent = `${usage.basic_analysis}/${limits.basic_analysis === Infinity ? '∞' : limits.basic_analysis}`;
        this.deepUsage.textContent = `${usage.deep_analysis}/${limits.deep_analysis === Infinity ? '∞' : limits.deep_analysis}`;
        
        // Update usage bars
        const basicPercent = limits.basic_analysis === Infinity ? 0 : (usage.basic_analysis / limits.basic_analysis) * 100;
        const deepPercent = limits.deep_analysis === Infinity ? 0 : (usage.deep_analysis / limits.deep_analysis) * 100;
        
        this.basicUsageBar.style.width = `${Math.min(basicPercent, 100)}%`;
        this.deepUsageBar.style.width = `${Math.min(deepPercent, 100)}%`;
        
        // Update API key input if user has one
        if (profile.has_api_key) {
            this.apiKeyInput.placeholder = 'API Key αποθηκευμένο';
        }
    }
    
    onSignIn(session) {
        console.log('User signed in:', session.user);
        this.loadUserProfile();
        this.showAuthenticatedView();
    }
    
    onSignOut() {
        console.log('User signed out');
        this.showLoginForm();
    }
    
    // UI Helper Methods
    
    showLoginForm() {
        this.hideAllViews();
        this.loginForm.classList.remove('hidden');
    }
    
    showEmailSentView() {
        this.hideAllViews();
        this.emailSentView.classList.remove('hidden');
    }
    
    showAuthenticatedView() {
        this.hideAllViews();
        this.authenticatedView.classList.remove('hidden');
    }
    
    hideAllViews() {
        this.loadingView.classList.add('hidden');
        this.loginForm.classList.add('hidden');
        this.emailSentView.classList.add('hidden');
        this.authenticatedView.classList.add('hidden');
    }
    
    showMessage(message, type = 'info') {
        this.authMessage.textContent = message;
        this.authMessage.className = `message ${type}`;
        this.authMessage.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.authMessage.classList.add('hidden');
        }, 5000);
    }
    
    showApiKeyMessage(message, type = 'info') {
        this.apiKeyMessage.textContent = message;
        this.apiKeyMessage.className = `message ${type}`;
        this.apiKeyMessage.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.apiKeyMessage.classList.add('hidden');
        }, 5000);
    }
    
    setLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            button.textContent = 'Φόρτωση...';
        } else {
            button.disabled = false;
            // Restore original text based on button ID
            if (button === this.magicLinkButton) {
                button.textContent = 'Αποστολή Magic Link';
            } else if (button === this.resendButton) {
                button.textContent = 'Επαναποστολή';
            } else if (button === this.logoutButton) {
                button.textContent = 'Αποσύνδεση';
            } else if (button === this.apiKeyButton) {
                button.textContent = 'Αποθήκευση API Key';
            }
        }
    }
    
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new NewscopilotAuth();
});