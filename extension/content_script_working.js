// Working content script without ES6 modules
console.log("News Copilot - Working version loaded!");
console.log("URL:", window.location.href);

// Create button function
function createAugmentButton() {
    const button = document.createElement("button");
    button.id = "augment-article-button";
    button.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
        <span>Ανάλυση Άρθρου</span>
    `;
    button.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        padding: 16px 24px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 50px;
        z-index: 9999;
        cursor: pointer;
        font-size: 15px;
        font-weight: 600;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    `;
    
    button.addEventListener('click', function() {
        console.log("Button clicked!");
        button.disabled = true;
        button.querySelector('span').textContent = "Αναλύεται...";
        
        // Send message to background script
        chrome.runtime.sendMessage({
            type: "AUGMENT_ARTICLE",
            url: window.location.href
        }, function(response) {
            button.disabled = false;
            button.querySelector('span').textContent = "Ανάλυση Άρθρου";
            
            if (response && response.success) {
                console.log("Analysis successful!", response.data);
                alert("Η ανάλυση ολοκληρώθηκε! (Check console for data)");
            } else if (response && response.needsAuth) {
                console.error("Authentication required");
                alert("Παρακαλώ συνδεθείτε πρώτα από το εικονίδιο της επέκτασης");
            } else if (response && response.rateLimit) {
                console.error("Rate limit exceeded");
                alert("Έχετε φτάσει το μηνιαίο όριο. Αναβαθμίστε το πλάνο σας.");
            } else {
                console.error("Analysis failed:", response?.error || "Unknown error");
                alert("Σφάλμα: " + (response?.error || "Unknown error"));
            }
        });
    });
    
    return button;
}

// Initialize when DOM is ready
function initialize() {
    console.log("Initializing News Copilot...");
    const button = createAugmentButton();
    document.body.appendChild(button);
    console.log("News Copilot button added to page!");
}

// Wait for DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}