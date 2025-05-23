// modules/ui/button.js
// Smart Floating Button Component

export function createAugmentButton() {
  const augmentButton = document.createElement("button");
  augmentButton.id = "augment-article-button";
  augmentButton.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
    </svg>
    <span>Ανάλυση Άρθρου</span>
  `;
  augmentButton.style.cssText = `
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
    backdrop-filter: blur(10px);
  `;
  
  document.body.appendChild(augmentButton);
  return augmentButton;
}

export function updateButtonState(button, state) {
  switch (state) {
    case 'processing':
      button.classList.add('processing');
      button.disabled = true;
      button.innerHTML = `
        <div class="status-spinner"></div>
        <span>Επεξεργασία...</span>
      `;
      break;
    case 'complete':
      button.classList.remove('processing');
      button.disabled = false;
      button.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M20 6L9 17l-5-5"/>
        </svg>
        <span>Ολοκληρώθηκε</span>
      `;
      setTimeout(() => resetButton(button), 2000);
      break;
    case 'error':
      button.classList.remove('processing');
      button.disabled = false;
      button.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <span>Σφάλμα</span>
      `;
      setTimeout(() => resetButton(button), 3000);
      break;
  }
}

function resetButton(button) {
  button.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
    </svg>
    <span>Ανάλυση Άρθρου</span>
  `;
}