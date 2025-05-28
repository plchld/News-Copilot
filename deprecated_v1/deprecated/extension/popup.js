// popup.js
// Extension popup for authentication and usage tracking

const API_BASE = 'https://news-copilot.vercel.app';

// UI Elements
const loginForm = document.getElementById('loginForm');
const authenticatedView = document.getElementById('authenticatedView');
const loadingView = document.getElementById('loadingView');
const emailInput = document.getElementById('emailInput');
const authButton = document.getElementById('authButton');
const authError = document.getElementById('authError');
const userEmail = document.getElementById('userEmail');
const basicUsage = document.getElementById('basicUsage');
const basicUsageBar = document.getElementById('basicUsageBar');
const deepUsage = document.getElementById('deepUsage');
const deepUsageBar = document.getElementById('deepUsageBar');
const tierName = document.getElementById('tierName');
const apiKeyInput = document.getElementById('apiKeyInput');
const apiKeyButton = document.getElementById('apiKeyButton');
const apiKeyStatus = document.getElementById('apiKeyStatus');
const logoutButton = document.getElementById('logoutButton');

// Load saved auth state
let authToken = null;
let userInfo = null;

async function loadAuthState() {
    try {
        const result = await chrome.storage.local.get(['authToken', 'userInfo']);
        if (result.authToken && result.userInfo) {
            authToken = result.authToken;
            userInfo = result.userInfo;
            await updateUsageStats();
            showAuthenticatedView();
        } else {
            showLoginForm();
        }
    } catch (error) {
        console.error('Error loading auth state:', error);
        showLoginForm();
    }
}

function showLoginForm() {
    loadingView.classList.add('hidden');
    loginForm.classList.remove('hidden');
    authenticatedView.classList.add('hidden');
}

function showAuthenticatedView() {
    loadingView.classList.add('hidden');
    loginForm.classList.add('hidden');
    authenticatedView.classList.remove('hidden');
    
    if (userInfo) {
        userEmail.textContent = userInfo.email;
        updateTierDisplay();
    }
}

function showLoading() {
    loadingView.classList.remove('hidden');
    loginForm.classList.add('hidden');
    authenticatedView.classList.add('hidden');
}

async function authenticate() {
    const email = emailInput.value.trim();
    if (!email) {
        showError('Παρακαλώ εισάγετε email');
        return;
    }
    
    showLoading();
    authError.classList.add('hidden');
    
    try {
        const response = await fetch(`${API_BASE}/api/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.token;
            userInfo = {
                email: email,
                tier: data.tier,
                usage: data.usage
            };
            
            // Save to storage
            await chrome.storage.local.set({
                authToken: authToken,
                userInfo: userInfo
            });
            
            // Send token to background script
            chrome.runtime.sendMessage({
                type: 'AUTH_UPDATE',
                token: authToken
            });
            
            showAuthenticatedView();
        } else {
            showError(data.error || 'Σφάλμα σύνδεσης');
            showLoginForm();
        }
    } catch (error) {
        console.error('Auth error:', error);
        showError('Σφάλμα δικτύου. Δοκιμάστε ξανά.');
        showLoginForm();
    }
}

async function updateUsageStats() {
    if (!userInfo || !userInfo.email) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/auth/usage?email=${userInfo.email}`, {
            headers: {
                'Authorization': `Bearer ${authToken.replace(/[^\x00-\x7F]/g, "")}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            userInfo.usage = data.usage;
            userInfo.limits = data.limits;
            userInfo.tier = data.tier;
            updateUsageDisplay();
        }
    } catch (error) {
        console.error('Error fetching usage:', error);
    }
}

function updateUsageDisplay() {
    if (!userInfo) return;
    
    const basicUsed = userInfo.usage?.basic_analysis || 0;
    const basicLimit = userInfo.limits?.basic_analysis || 10;
    const deepUsed = userInfo.usage?.deep_analysis || 0;
    const deepLimit = userInfo.limits?.deep_analysis || 0;
    
    basicUsage.textContent = `${basicUsed}/${basicLimit === Infinity ? '∞' : basicLimit}`;
    basicUsageBar.style.width = basicLimit === Infinity ? '0%' : `${(basicUsed / basicLimit) * 100}%`;
    
    deepUsage.textContent = `${deepUsed}/${deepLimit === Infinity ? '∞' : deepLimit}`;
    deepUsageBar.style.width = deepLimit === Infinity ? '0%' : `${(deepUsed / deepLimit) * 100}%`;
}

function updateTierDisplay() {
    if (!userInfo) return;
    
    const tierNames = {
        'free': 'Δωρεάν Πλάνο',
        'pro': 'Pro Πλάνο',
        'premium': 'Premium Πλάνο',
        'byok': 'Προσωπικό API Key'
    };
    
    tierName.textContent = tierNames[userInfo.tier] || 'Δωρεάν Πλάνο';
}

async function saveApiKey() {
    const apiKey = apiKeyInput.value.trim();
    if (!apiKey) {
        showApiKeyStatus('Παρακαλώ εισάγετε API key', 'error');
        return;
    }
    
    if (!apiKey.startsWith('xai-')) {
        showApiKeyStatus('Το API key πρέπει να ξεκινά με "xai-"', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/auth/set-api-key`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken.replace(/[^\x00-\x7F]/g, "")}`
            },
            body: JSON.stringify({
                email: userInfo.email,
                api_key: apiKey.replace(/[^\x00-\x7F]/g, "")
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.token;
            userInfo.tier = data.tier;
            
            await chrome.storage.local.set({
                authToken: authToken,
                userInfo: userInfo
            });
            
            chrome.runtime.sendMessage({
                type: 'AUTH_UPDATE',
                token: authToken
            });
            
            showApiKeyStatus('API key αποθηκεύτηκε επιτυχώς!', 'success');
            apiKeyInput.value = '';
            updateTierDisplay();
            await updateUsageStats();
        } else {
            showApiKeyStatus(data.error || 'Σφάλμα αποθήκευσης', 'error');
        }
    } catch (error) {
        console.error('API key error:', error);
        showApiKeyStatus('Σφάλμα δικτύου', 'error');
    }
}

function showApiKeyStatus(message, type) {
    apiKeyStatus.textContent = message;
    apiKeyStatus.className = type;
    apiKeyStatus.classList.remove('hidden');
    
    setTimeout(() => {
        apiKeyStatus.classList.add('hidden');
    }, 3000);
}

function showError(message) {
    authError.textContent = message;
    authError.classList.remove('hidden');
}

async function logout() {
    await chrome.storage.local.remove(['authToken', 'userInfo']);
    chrome.runtime.sendMessage({
        type: 'AUTH_UPDATE',
        token: null
    });
    authToken = null;
    userInfo = null;
    emailInput.value = '';
    showLoginForm();
}

// Event Listeners
authButton.addEventListener('click', authenticate);
emailInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') authenticate();
});
apiKeyButton.addEventListener('click', saveApiKey);
logoutButton.addEventListener('click', logout);

// Initialize
loadAuthState();