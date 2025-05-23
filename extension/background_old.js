console.log("Article Augmentor background script loaded.");

// Store auth token
let authToken = null;

// Listen for auth updates from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "AUTH_UPDATE") {
    authToken = message.token;
    console.log("Auth token updated:", authToken ? "Present" : "Cleared");
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
    const flaskServerStreamUrl = `https://news-copilot.vercel.app/augment-stream?url=${encodeURIComponent(message.url)}`;

    // Use EventSource to connect to the SSE endpoint
    const eventSource = new EventSource(flaskServerStreamUrl);

    eventSource.onopen = () => {
      console.log("Background: SSE connection opened.");
      // Optionally send an initial progress update to content script
      if (sender.tab && sender.tab.id) {
        chrome.tabs.sendMessage(sender.tab.id, { type: "PROGRESS_UPDATE", status: "Σύνδεση με server..." });
      }
    };

    eventSource.addEventListener("progress", (event) => {
      const eventData = JSON.parse(event.data);
      console.log("Background: Received progress event:", eventData);
      // Forward progress to content script
      if (sender.tab && sender.tab.id) {
        chrome.tabs.sendMessage(sender.tab.id, { type: "PROGRESS_UPDATE", status: eventData.status });
      }
    });

    eventSource.addEventListener("final_result", (event) => {
      const eventData = JSON.parse(event.data);
      console.log("Background: Received final_result event:", eventData);
      sendResponse({ 
        success: true, 
        jargon: eventData.jargon, 
        viewpoints: eventData.viewpoints, 
        jargon_citations: eventData.jargon_citations, 
        viewpoints_citations: eventData.viewpoints_citations 
      });
      eventSource.close(); // Close connection after receiving final result
    });

    eventSource.addEventListener("error", (event) => {
      let errorMessage = "An unknown error occurred with the SSE stream.";
      if (event.data) {
        try {
            const eventData = JSON.parse(event.data);
            errorMessage = eventData.message || "Error from server (no message)";
        } catch (e) {
            errorMessage = "Malformed error event from server.";
        }
      } else if (event.target && event.target.readyState === EventSource.CLOSED) {
        errorMessage = "SSE connection closed by server unexpectedly or failed to connect.";
      } 
      console.error("Background: SSE error event:", event, "Message:", errorMessage);
      sendResponse({ success: false, error: errorMessage });
      eventSource.close(); // Close connection on error
    });
    
    // Keep the message channel open for the asynchronous response from sendResponse
    return true; 
  } else if (message.type === "DEEP_ANALYSIS") {
    console.log("Background: Received DEEP_ANALYSIS message:", message);
    
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
      },
      body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
      console.log("Background: Deep analysis response:", data);
      if (data.success) {
        sendResponse({ 
          success: true, 
          data: data.data.analysis,
          citations: data.data.citations || []
        });
      } else {
        sendResponse({ 
          success: false, 
          error: data.error || "Unknown error during deep analysis" 
        });
      }
    })
    .catch(error => {
      console.error("Background: Deep analysis fetch error:", error);
      sendResponse({ 
        success: false, 
        error: "Failed to connect to analysis service" 
      });
    });
    
    return true; // Keep channel open for async response
  }
}); 