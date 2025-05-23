// extension/js/supabase-auth.js
// Supabase authentication for Chrome extension

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.38.0'

class SupabaseAuth {
    constructor() {
        // These will be set from environment or storage
        this.supabaseUrl = null;
        this.supabaseAnonKey = null;
        this.supabase = null;
        this.currentUser = null;
        this.currentSession = null;
        
        this.init();
    }
    
    async init() {
        // Get Supabase credentials from storage or config
        const config = await this.getConfig();
        
        if (config.supabaseUrl && config.supabaseAnonKey) {
            this.supabaseUrl = config.supabaseUrl;
            this.supabaseAnonKey = config.supabaseAnonKey;
            this.supabase = createClient(this.supabaseUrl, this.supabaseAnonKey);
            
            // Check for existing session
            await this.checkSession();
            
            // Listen for auth changes
            this.supabase.auth.onAuthStateChange((event, session) => {
                console.log('Auth state changed:', event, session);
                this.currentSession = session;
                this.currentUser = session?.user || null;
                
                if (event === 'SIGNED_IN') {
                    this.onSignIn(session);
                } else if (event === 'SIGNED_OUT') {
                    this.onSignOut();
                }
            });
        }
    }

    async signInWithGoogle() {
        if (!this.supabase) throw new Error('Supabase not initialized');

        try {
            const { data, error } = await this.supabase.auth.signInWithOAuth({
                provider: 'google',
                options: {
                    redirectTo: 'https://news-copilot.vercel.app/auth/callback'
                }
            });

            if (error) throw error;

            // signInWithOAuth typically redirects, so this part might not be reached
            // if the redirect happens immediately.
            // However, if it returns data (e.g., the URL to redirect to),
            // the caller (popup-supabase.js) will handle the redirect.
            return {
                success: true,
                data: data // This might contain the provider's URL
            };
        } catch (error) {
            console.error('Error signing in with Google:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    async getConfig() {
        // In production, these should come from your backend or be hardcoded
        return {
            supabaseUrl: 'https://your-project.supabase.co', // Replace with your Supabase URL
            supabaseAnonKey: 'your-anon-key' // Replace with your anon key
        };
    }
    
    async checkSession() {
        if (!this.supabase) return null;
        
        try {
            const { data: { session }, error } = await this.supabase.auth.getSession();
            if (error) throw error;
            
            this.currentSession = session;
            this.currentUser = session?.user || null;
            
            return session;
        } catch (error) {
            console.error('Error checking session:', error);
            return null;
        }
    }
    
    async signInWithMagicLink(email) {
        if (!this.supabase) throw new Error('Supabase not initialized');
        
        try {
            const { data, error } = await this.supabase.auth.signInWithOtp({
                email: email,
                options: {
                    emailRedirectTo: 'https://news-copilot.vercel.app/auth/callback'
                }
            });
            
            if (error) throw error;
            
            return {
                success: true,
                message: 'Magic link sent to your email'
            };
        } catch (error) {
            console.error('Error sending magic link:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    async signInWithPassword(email, password) {
        if (!this.supabase) throw new Error('Supabase not initialized');
        
        try {
            const { data, error } = await this.supabase.auth.signInWithPassword({
                email: email,
                password: password
            });
            
            if (error) throw error;
            
            return {
                success: true,
                user: data.user,
                session: data.session
            };
        } catch (error) {
            console.error('Error signing in:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    async signUp(email, password = null) {
        if (!this.supabase) throw new Error('Supabase not initialized');
        
        try {
            let result;
            
            if (password) {
                // Sign up with password
                result = await this.supabase.auth.signUp({
                    email: email,
                    password: password
                });
            } else {
                // Sign up with magic link
                result = await this.supabase.auth.signInWithOtp({
                    email: email,
                    options: {
                        emailRedirectTo: 'https://news-copilot.vercel.app/auth/callback'
                    }
                });
            }
            
            if (result.error) throw result.error;
            
            return {
                success: true,
                message: password ? 'Account created! Please check your email for verification.' : 'Magic link sent to your email'
            };
        } catch (error) {
            console.error('Error signing up:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }
    
    async signOut() {
        if (!this.supabase) return;
        
        try {
            const { error } = await this.supabase.auth.signOut();
            if (error) throw error;
            
            this.currentSession = null;
            this.currentUser = null;
            
            return { success: true };
        } catch (error) {
            console.error('Error signing out:', error);
            return { success: false, error: error.message };
        }
    }
    
    async getProfile() {
        if (!this.currentSession) return null;
        
        try {
            const response = await fetch(`${this.getBackendUrl()}/api/auth/profile`, {
                headers: {
                    'Authorization': `Bearer ${this.currentSession.access_token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error('Failed to get profile');
            
            return await response.json();
        } catch (error) {
            console.error('Error getting profile:', error);
            return null;
        }
    }
    
    async updateApiKey(apiKey) {
        if (!this.currentSession) throw new Error('Not authenticated');
        
        try {
            const response = await fetch(`${this.getBackendUrl()}/api/auth/update-api-key`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.currentSession.access_token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ api_key: apiKey })
            });
            
            if (!response.ok) throw new Error('Failed to update API key');
            
            return await response.json();
        } catch (error) {
            console.error('Error updating API key:', error);
            throw error;
        }
    }
    
    getBackendUrl() {
        // Return your backend URL
        return 'https://news-copilot.vercel.app'; // Replace with your actual backend URL
    }
    
    isAuthenticated() {
        return !!this.currentSession && !!this.currentUser;
    }
    
    getAccessToken() {
        return this.currentSession?.access_token || null;
    }
    
    onSignIn(session) {
        console.log('User signed in:', session.user);
        // Emit custom event for UI updates
        window.dispatchEvent(new CustomEvent('authStateChanged', {
            detail: { event: 'SIGNED_IN', session: session }
        }));
    }
    
    onSignOut() {
        console.log('User signed out');
        // Emit custom event for UI updates
        window.dispatchEvent(new CustomEvent('authStateChanged', {
            detail: { event: 'SIGNED_OUT', session: null }
        }));
    }
}

// Create global instance
window.supabaseAuth = new SupabaseAuth();

export default SupabaseAuth;