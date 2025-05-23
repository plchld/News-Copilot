// modules/ui/status-display.js
// Status Display Component

export let statusDisplay = null;

export function showStatus(message) {
    removeStatus();
    
    statusDisplay = document.createElement("div");
    statusDisplay.className = "intelligence-status";
    statusDisplay.innerHTML = `
        <div class="status-spinner"></div>
        <span>${message}</span>
    `;
    
    document.body.appendChild(statusDisplay);
}

export function updateStatus(message) {
    if (statusDisplay) {
        const span = statusDisplay.querySelector('span');
        if (span) {
            span.textContent = message;
        }
    }
}

export function removeStatus() {
    if (statusDisplay) {
        statusDisplay.remove();
        statusDisplay = null;
    }
}

export function showSuccessStatus(message, duration = 2000) {
    removeStatus();
    
    statusDisplay = document.createElement("div");
    statusDisplay.className = "intelligence-status";
    statusDisplay.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 6L9 17l-5-5"/>
        </svg>
        <span>${message}</span>
    `;
    
    document.body.appendChild(statusDisplay);
    
    setTimeout(() => {
        removeStatus();
    }, duration);
}

export function showErrorStatus(message, duration = 3000) {
    removeStatus();
    
    statusDisplay = document.createElement("div");
    statusDisplay.className = "intelligence-status";
    statusDisplay.style.background = "rgba(220, 38, 38, 0.9)";
    statusDisplay.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span>${message}</span>
    `;
    
    document.body.appendChild(statusDisplay);
    
    setTimeout(() => {
        removeStatus();
    }, duration);
}