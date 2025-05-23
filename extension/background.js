console.log("Article Augmentor background script loaded.");

// Store auth token
let authToken = null;

// Listen for auth updates from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "AUTH_UPDATE") {
    authToken = message.token;
    console.log("Auth token updated:", authToken ? "Present" : "Cleared");
    sendResponse({ success: true });
    return false;
  }
});

// Load auth token on startup
chrome.storage.local.get(['authToken'], (result) => {
  if (result.authToken) {
    authToken = result.authToken;
    console.log("Auth token loaded from storage");
  }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "AUGMENT_ARTICLE") {
    console.log("Background: Received AUGMENT_ARTICLE message with URL:", message.url);
    
    // Check if user is authenticated
    if (!authToken) {
      sendResponse({
        success: false,
        error: "Παρακαλώ συνδεθείτε πρώτα από το εικονίδιο της επέκτασης",
        needsAuth: true
      });
      return true;
    }

    // Since EventSource doesn't support headers, we'll use fetch with streaming
    const flaskServerUrl = `https://news-copilot.vercel.app/augment-stream?url=${encodeURIComponent(message.url)}`;
    
    fetch(flaskServerUrl, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
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
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('event:')) {
              const eventType = line.substring(6).trim();
              
              // Get the data line
              const nextLine = lines[lines.indexOf(line) + 1];
              if (nextLine && nextLine.startsWith('data:')) {
                const data = JSON.parse(nextLine.substring(5).trim());
                
                if (eventType === 'progress' && sender.tab && sender.tab.id) {
                  chrome.tabs.sendMessage(sender.tab.id, { 
                    type: "PROGRESS_UPDATE", 
                    status: data.status 
                  });
                } else if (eventType === 'final_result') {
                  sendResponse({ success: true, data: data });
                } else if (eventType === 'error') {
                  sendResponse({ success: false, error: data.message });
                }
              }
            }
          }

          processStream();
        }).catch(error => {
          console.error("Stream reading error:", error);
          sendResponse({ success: false, error: error.message });
        });
      }

      processStream();
    })
    .catch(error => {
      console.error("Fetch error:", error);
      if (error.message === 'AUTH_REQUIRED') {
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
  } else if (message.type === "DEEP_ANALYSIS") {
    console.log("Background: Received DEEP_ANALYSIS message:", message);
    
    if (!authToken) {
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
        'Authorization': `Bearer ${authToken}`
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