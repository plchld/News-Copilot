console.log("News Copilot background script loaded.");

// Auth state management
let authState = {
  token: null,
  user: null,
  expiresAt: null
};

// Initialize auth state from storage
chrome.storage.local.get(['auth_token', 'auth_user', 'auth_expires_at'], (result) => {
  if (result.auth_token && result.auth_expires_at > Date.now()) {
    authState = {
      token: result.auth_token,
      user: result.auth_user,
      expiresAt: result.auth_expires_at
    };
    console.log("Auth state loaded from storage");
  }
});

// Handle auth state updates
async function updateAuthState(token, user, expiresAt) {
  authState = { token, user, expiresAt };
  
  // Store in chrome.storage
  await chrome.storage.local.set({
    auth_token: token,
    auth_user: user,
    auth_expires_at: expiresAt
  });
  
  // Notify all tabs and popup
  chrome.runtime.sendMessage({ type: 'AUTH_STATE_CHANGED', authState });
  
  // Notify all content scripts
  const tabs = await chrome.tabs.query({});
  tabs.forEach(tab => {
    chrome.tabs.sendMessage(tab.id, { type: 'AUTH_STATE_CHANGED', authState }).catch(() => {});
  });
}

// Clear auth state
async function clearAuthState() {
  authState = { token: null, user: null, expiresAt: null };
  await chrome.storage.local.remove(['auth_token', 'auth_user', 'auth_expires_at']);
  
  // Notify all
  chrome.runtime.sendMessage({ type: 'AUTH_STATE_CHANGED', authState });
  const tabs = await chrome.tabs.query({});
  tabs.forEach(tab => {
    chrome.tabs.sendMessage(tab.id, { type: 'AUTH_STATE_CHANGED', authState }).catch(() => {});
  });
}

// Listen for messages
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Auth state queries
  if (message.type === "GET_AUTH_STATE") {
    sendResponse({ authState });
    return false;
  }
  
  // Auth state updates
  if (message.type === "SET_AUTH_STATE") {
    updateAuthState(message.token, message.user, message.expiresAt);
    sendResponse({ success: true });
    return false;
  }
  
  // Clear auth
  if (message.type === "CLEAR_AUTH") {
    clearAuthState();
    sendResponse({ success: true });
    return false;
  }
  
  // Handle auth callback from web page
  if (message.type === "AUTH_CALLBACK") {
    const { access_token, refresh_token, expires_in, user_email } = message.data;
    const expiresAt = Date.now() + (expires_in * 1000);
    
    updateAuthState(access_token, { email: user_email, refresh_token }, expiresAt);
    sendResponse({ success: true });
    return false;
  }

  // Legacy auth update support
  if (message.type === "AUTH_UPDATE") {
    const expiresAt = Date.now() + (3600 * 1000); // Default 1 hour
    updateAuthState(message.token, null, expiresAt);
    sendResponse({ success: true });
    return false;
  }

  // Article augmentation
  if (message.type === "AUGMENT_ARTICLE") {
    console.log("Background: Received AUGMENT_ARTICLE message with URL:", message.url);
    
    // Check if user is authenticated
    if (!authState.token || authState.expiresAt < Date.now()) {
      sendResponse({
        success: false,
        error: "Παρακαλώ συνδεθείτε πρώτα από το εικονίδιο της επέκτασης",
        needsAuth: true
      });
      return true;
    }

    // Since EventSource doesn't support headers, we'll use fetch with streaming
    const flaskServerUrl = `https://news-copilot.vercel.app/augment-stream?url=${encodeURIComponent(message.url)}`;
    
    console.log("Background: Making API call to:", flaskServerUrl);
    console.log("Background: Auth token present:", !!authState.token);
    
    fetch(flaskServerUrl, {
      headers: {
        'Authorization': `Bearer ${authState.token}`
      }
    })
    .then(response => {
      console.log("Background: Response status:", response.status);
      console.log("Background: Response headers:", response.headers);
      
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('AUTH_REQUIRED');
        } else if (response.status === 429) {
          throw new Error('RATE_LIMIT');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      function processStream() {
        reader.read().then(({ done, value }) => {
          if (done) {
            console.log("Stream complete");
            return;
          }

          buffer += decoder.decode(value, { stream: true });
          const messages = buffer.split('\n\n');
          buffer = messages.pop() || '';

          for (const message of messages) {
            if (!message.trim()) continue;
            
            const lines = message.split('\n');
            let eventType = null;
            let eventData = null;
            
            for (const line of lines) {
              if (line.startsWith('event:')) {
                eventType = line.substring(6).trim();
              } else if (line.startsWith('data:')) {
                try {
                  eventData = JSON.parse(line.substring(5).trim());
                } catch (e) {
                  console.error("Failed to parse SSE data:", line);
                }
              }
            }
            
            if (eventType && eventData) {
              console.log(`Background: Processing event '${eventType}'`);
              
              if (eventType === 'progress' && sender.tab && sender.tab.id) {
                chrome.tabs.sendMessage(sender.tab.id, { 
                  type: "PROGRESS_UPDATE", 
                  status: eventData.status 
                }).catch(() => {}); // Ignore if tab is closed
              } else if (eventType === 'final_result') {
                console.log("Background: Received final result:", eventData);
                sendResponse({ success: true, data: eventData });
                reader.cancel(); // Stop reading after final result
                return;
              } else if (eventType === 'error') {
                console.error("Background: Received error event:", eventData);
                sendResponse({ success: false, error: eventData.message || "API error" });
                reader.cancel();
                return;
              }
            }
          }

          processStream();
        }).catch(error => {
          console.error("Stream reading error:", error);
          if (error.name === 'AbortError') {
            sendResponse({ success: false, error: "Η ανάλυση διακόπηκε" });
          } else {
            sendResponse({ success: false, error: `Σφάλμα ανάγνωσης: ${error.message}` });
          }
        });
      }

      processStream();
    })
    .catch(error => {
      console.error("Fetch error:", error);
      console.error("Error type:", error.name);
      console.error("Error message:", error.message);
      
      if (error.message === 'AUTH_REQUIRED') {
        clearAuthState(); // Clear invalid auth
        sendResponse({
          success: false,
          error: "Παρακαλώ συνδεθείτε ξανά",
          needsAuth: true
        });
      } else if (error.message === 'RATE_LIMIT') {
        sendResponse({
          success: false,
          error: "Έχετε φτάσει το μηνιαίο όριο. Αναβαθμίστε το πλάνο σας.",
          rateLimit: true
        });
      } else {
        sendResponse({ success: false, error: error.message });
      }
    });

    return true; // Will respond asynchronously
  }
  
  // Deep analysis
  if (message.type === "DEEP_ANALYSIS") {
    console.log("Background: Received DEEP_ANALYSIS message:", message);
    
    if (!authState.token || authState.expiresAt < Date.now()) {
      sendResponse({
        success: false,
        error: "Παρακαλώ συνδεθείτε πρώτα",
        needsAuth: true
      });
      return true;
    }
    
    // Call the Python Flask server for deep analysis
    const flaskDeepAnalysisUrl = 'https://news-copilot.vercel.app/deep-analysis';
    
    const requestData = {
      url: message.url,
      analysis_type: message.analysisType,
      search_params: message.searchParams || {}
    };
    
    fetch(flaskDeepAnalysisUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authState.token}`
      },
      body: JSON.stringify(requestData)
    })
    .then(response => {
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('AUTH_REQUIRED');
        } else if (response.status === 429) {
          throw new Error('RATE_LIMIT');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log("Background: Deep analysis response received:", data);
      sendResponse({ success: true, data: data.result, citations: data.citations });
    })
    .catch(error => {
      console.error("Background: Deep analysis error:", error);
      if (error.message === 'AUTH_REQUIRED') {
        clearAuthState(); // Clear invalid auth
        sendResponse({
          success: false,
          error: "Παρακαλώ συνδεθείτε ξανά",
          needsAuth: true
        });
      } else if (error.message === 'RATE_LIMIT') {
        sendResponse({
          success: false,
          error: "Έχετε φτάσει το μηνιαίο όριο εξειδικευμένων αναλύσεων",
          rateLimit: true
        });
      } else {
        sendResponse({ success: false, error: error.message });
      }
    });
    
    return true; // Will respond asynchronously
  }
});

// Listen for auth callback URLs
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url && changeInfo.url.includes('news-copilot.vercel.app/#access_token=')) {
    // Parse the auth tokens from the URL
    const url = new URL(changeInfo.url);
    const hash = url.hash.substring(1);
    const params = new URLSearchParams(hash);
    
    const access_token = params.get('access_token');
    const refresh_token = params.get('refresh_token');
    const expires_in = parseInt(params.get('expires_in') || '3600');
    
    if (access_token) {
      // Update auth state
      const expiresAt = Date.now() + (expires_in * 1000);
      updateAuthState(access_token, { refresh_token }, expiresAt);
      
      // Show success message
      chrome.tabs.sendMessage(tabId, {
        type: 'SHOW_AUTH_SUCCESS',
        message: 'Επιτυχής σύνδεση! Μπορείτε τώρα να κλείσετε αυτήν την καρτέλα.'
      });
      
      // Close the tab after a delay
      setTimeout(() => {
        chrome.tabs.remove(tabId);
      }, 3000);
    }
  }
});