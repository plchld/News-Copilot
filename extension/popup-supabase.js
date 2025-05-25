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

    async setSession(session) {
        // Store the session
        this.currentSession = session;
        localStorage.setItem('supabase_session', JSON.stringify(session));
        return { data: { session }, error: null };
    }

    get auth() {
        return {
            signInWithOtp: this.signInWithOtp.bind(this),
            getSession: this.getSession.bind(this),
            onAuthStateChange: this.onAuthStateChange.bind(this),
            signOut: async () => ({ error: null }),
            signInWithOAuth: this.signInWithOAuth.bind(this),
            setSession: this.setSession.bind(this)
        };
    }

    async signInWithOAuth(options) {
        const { provider, options: { redirectTo } } = options;
        const authUrl = `${this.url}/auth/v1/authorize?provider=${provider}&redirect_to=${redirectTo}`;
        
        // For extensions, we need to open this in a new tab
        // The Supabase library would normally handle the redirect.
        try {
            if (chrome && chrome.tabs) {
                chrome.tabs.create({ url: authUrl });
            } else {
                // Fallback for non-extension environments (testing, etc.)
                window.open(authUrl, '_blank');
            }
            // This method itself doesn't return user/session in this flow,
            // the redirect and subsequent session handling does.
            return { data: { provider, url: authUrl }, error: null };
        } catch (error) {
            console.error('Error in signInWithOAuth:', error);
            return { data: null, error };
        }
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
        this.googleSignInButton = document.getElementById('googleSignInButton');
    }
    
    setupEventListeners() {
        this.magicLinkButton.addEventListener('click', () => this.sendMagicLink());
        if (this.googleSignInButton) { // Ensure button exists
            this.googleSignInButton.addEventListener('click', () => this.handleGoogleSignIn());
        }
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

    async handleGoogleSignIn() {
        this.setLoading(this.googleSignInButton, true);
        this.showMessage('Ανακατεύθυνση στην Google για σύνδεση...', 'info');

        try {
            const { data, error } = await supabase.auth.signInWithOAuth({
                provider: 'google',
                options: {
                    redirectTo: `${BACKEND_URL}/auth/callback` // Ensure this matches your Supabase redirect settings
                }
            });

            if (error) {
                throw error;
            }
            
            // For OAuth in extensions, the user is redirected.
            // The onAuthStateChange listener (if fully implemented and listened to)
            // or a manual check after the redirect would handle the user session.
            // We might not get an immediate session here. The tab will open, user signs in,
            // and then Supabase redirects to /auth/callback, which should then notify the extension.
            // For now, popup might close or refresh. User should be signed in when they reopen.
            // We can't directly confirm sign-in here without a more complex flow.

        } catch (error) {
            console.error('Error during Google Sign-In:', error);
            this.showMessage(`Σφάλμα σύνδεσης Google: ${error.message}`, 'error');
        } finally {
            // The button's loading state might need to be reset if the popup remains open
            // and the redirect doesn't happen or fails before redirect.
            // However, typically the redirect will cause the popup to lose context or close.
            // If the popup is re-opened, checkAuthState should reflect the new state.
            this.setLoading(this.googleSignInButton, false); 
        }
    }
    
    async checkAuthState() {
        try {
            // First check localStorage for auth data (set by the callback page)
            const storedAuth = localStorage.getItem('news_copilot_auth');
            if (storedAuth) {
                try {
                    const authData = JSON.parse(storedAuth);
                    // Check if token is not expired
                    if (authData.expires_at > Date.now()) {
                        // Update Supabase client with the stored token
                        supabase.auth.setSession({
                            access_token: authData.access_token,
                            refresh_token: authData.refresh_token
                        });
                        // Clear the stored auth to prevent reuse
                        localStorage.removeItem('news_copilot_auth');
                    }
                } catch (e) {
                    console.error('Error parsing stored auth:', e);
                }
            }
            
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
                    'Authorization': `Bearer ${this.currentSession.access_token.replace(/[^\x00-\x7F]/g, "")}`,
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
                    'Authorization': `Bearer ${this.currentSession.access_token.replace(/[^\x00-\x7F]/g, "")}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ api_key: apiKey.replace(/[^\x00-\x7F]/g, "") })
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
            } else if (button === this.googleSignInButton) {
                button.textContent = 'Σύνδεση με Google';
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
    const auth = new NewscopilotAuth();
    
    // Check auth state when popup window gains focus (e.g., after returning from magic link)
    window.addEventListener('focus', () => {
        auth.checkAuthState();
    });
    
    // Also listen for storage events (though they don't fire in the same window)
    window.addEventListener('storage', (e) => {
        if (e.key === 'news_copilot_auth') {
            auth.checkAuthState();
        }
    });
});