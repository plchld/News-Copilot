console.log("News Copilot - Ελληνική έκδοση φορτώθηκε.");

// --- UI Elements & State ---
let intelligenceSidebar = null;
let statusDisplay = null;
let highlightedTerms = [];
let currentData = null;

// --- Create Smart Floating Button ---
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

// --- Create Clean Website Button ---
const cleanWebsiteButton = document.createElement("button");
cleanWebsiteButton.id = "clean-website-button";
cleanWebsiteButton.innerHTML = `
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
    <circle cx="12" cy="12" r="3"></circle>
  </svg>
  <span>Καθαρή Προβολή</span>
`;
cleanWebsiteButton.style.cssText = `
  position: fixed;
  bottom: 30px;
  right: 200px; /* To the left of augmentButton */
  padding: 12px 18px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 50px;
  z-index: 9999;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3);
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
`;
document.body.appendChild(cleanWebsiteButton);

// Event listener for the new button
cleanWebsiteButton.addEventListener('click', () => {
    toggleReaderMode();
});
cleanWebsiteButton.setAttribute('data-listener-attached', 'true');


// --- Advanced CSS Styles ---
const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans:wght@400;500;600;700&display=swap');
  
  /* Button Interactions */
  #augment-article-button:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
    background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
  }

  #clean-website-button:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 10px 30px rgba(16, 185, 129, 0.4);
    background: linear-gradient(135deg, #059669 0%, #047857 100%);
  }
  
  #augment-article-button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
    transform: none;
  }
  
  #augment-article-button.processing {
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0%, 100% { box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3); }
    50% { box-shadow: 0 8px 32px rgba(102, 126, 234, 0.6); }
  }
  
  /* Intelligent Sidebar */
  .news-intelligence-sidebar {
    position: fixed;
    top: 0;
    right: 0;
    width: 420px;
    height: 100vh;
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border-left: 1px solid rgba(0, 0, 0, 0.08);
    box-shadow: -10px 0 50px rgba(0, 0, 0, 0.1);
    z-index: 10000;
    font-family: 'Noto Sans', 'Inter', system-ui, sans-serif;
    transform: translateX(100%);
    transition: transform 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
    backdrop-filter: blur(20px);
    overflow: hidden;
  }
  
  .news-intelligence-sidebar.open {
    transform: translateX(0);
  }
  
  .sidebar-header {
    padding: 24px 28px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    position: relative;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .sidebar-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.05"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.05"/><circle cx="50" cy="10" r="1" fill="white" opacity="0.03"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
    pointer-events: none;
  }
  
  .sidebar-title {
    font-size: 20px;
    font-weight: 700;
    margin: 0 0 4px 0;
    position: relative;
    z-index: 1;
  }
  
  .sidebar-subtitle {
    font-size: 14px;
    opacity: 0.9;
    margin: 0;
    position: relative;
    z-index: 1;
  }
  
  .sidebar-close {
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(255, 255, 255, 0.2);
    border: none;
    border-radius: 8px;
    width: 36px;
    height: 36px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
    z-index: 2;
  }
  
  .sidebar-close:hover {
    background: rgba(255, 255, 255, 0.3);
    transform: rotate(90deg);
  }
  
  .sidebar-content {
    height: calc(100vh - 80px);
    overflow-y: auto;
    padding: 0;
    scroll-behavior: smooth;
  }
  
  .sidebar-content::-webkit-scrollbar {
    width: 8px;
  }
  
  .sidebar-content::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.03);
  }
  
  .sidebar-content::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
  }
  
  /* Insights Overview Card */
  .insights-overview {
    margin: 20px;
    padding: 20px;
    background: white;
    border-radius: 16px;
    border: 1px solid rgba(0, 0, 0, 0.06);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  }
  
  .overview-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 16px;
  }
  
  .stat-item {
    text-align: center;
    padding: 12px;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    border-radius: 12px;
  }
  
  .stat-number {
    font-size: 24px;
    font-weight: 700;
    color: #667eea;
    margin-bottom: 4px;
  }
  
  .stat-label {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
  }
  
  /* Section Styles */
  .intelligence-section {
    margin: 20px;
    animation: slideInFromRight 0.6s ease-out forwards;
    opacity: 0;
  }
  
  .intelligence-section:nth-child(2) { animation-delay: 0.1s; }
  .intelligence-section:nth-child(3) { animation-delay: 0.2s; }
  .intelligence-section:nth-child(4) { animation-delay: 0.3s; }
  
  @keyframes slideInFromRight {
    from {
      opacity: 0;
      transform: translateX(30px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }
  
  .section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    padding: 12px 16px;
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
    border-radius: 12px;
    border-left: 4px solid #667eea;
  }
  
  .section-icon {
    width: 32px;
    height: 32px;
    background: white;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: #1e293b;
    margin: 0;
  }
  
  /* Term Cards with Enhanced Design */
  .term-card {
    background: white;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    transition: all 0.3s ease;
    cursor: pointer;
    position: relative;
    overflow: hidden;
  }
  
  .term-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    border-color: #667eea;
  }
  
  .term-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 3px;
    height: 100%;
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .term-card:hover::before {
    opacity: 1;
  }
  
  .term-title {
    font-size: 15px;
    font-weight: 600;
    color: #667eea;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .term-highlight-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: background 0.2s ease;
    margin-left: auto;
  }
  
  .term-highlight-btn:hover {
    background: rgba(102, 126, 234, 0.1);
  }
  
  .term-explanation {
    font-size: 13px;
    line-height: 1.6;
    color: #475569;
  }
  
  /* Viewpoints with Better Formatting */
  .viewpoint-card {
    background: linear-gradient(135deg, #fef7ff 0%, #faf5ff 100%);
    border: 1px solid rgba(139, 92, 246, 0.15);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    position: relative;
  }
  
  .viewpoint-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 3px;
    height: 100%;
    background: linear-gradient(180deg, #8b5cf6 0%, #a855f7 100%);
  }
  
  .viewpoint-type {
    display: inline-block;
    padding: 4px 12px;
    background: rgba(139, 92, 246, 0.1);
    color: #7c3aed;
    font-size: 11px;
    font-weight: 600;
    border-radius: 20px;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .viewpoint-content {
    font-size: 14px;
    line-height: 1.7;
    color: #374151;
  }
  
  .viewpoint-content strong {
    color: #7c3aed;
    font-weight: 600;
  }
  
  .viewpoint-content ul, .viewpoint-content ol {
    margin: 12px 0;
    padding-left: 20px;
  }
  
  .viewpoint-content li {
    margin-bottom: 8px;
  }
  
  /* Citations Redesign */
  .citations-section {
    background: #f8fafc;
    border-radius: 12px;
    padding: 16px;
    margin-top: 16px;
  }
  
  .citations-toggle {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-weight: 600;
    font-size: 13px;
    color: #475569;
    padding: 8px 0;
    user-select: none;
  }
  
  .citations-toggle svg {
    transition: transform 0.2s ease;
  }
  
  .citations-toggle.expanded svg {
    transform: rotate(90deg);
  }
  
  .citations-grid {
    display: none;
    grid-template-columns: 1fr;
    gap: 8px;
    margin-top: 12px;
  }
  
  .citations-grid.expanded {
    display: grid;
  }
  
  .citation-link {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    background: white;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 8px;
    text-decoration: none;
    color: #374151;
    font-size: 12px;
    transition: all 0.2s ease;
  }
  
  .citation-link:hover {
    background: #f1f5f9;
    transform: translateX(4px);
  }
  
  .citation-favicon {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    background: #e2e8f0;
    flex-shrink: 0;
  }
  
  .citation-domain {
    font-weight: 500;
    color: #1e293b;
    flex: 1;
  }
  
  /* Article Highlighting */
  .highlighted-term {
    background: linear-gradient(120deg, rgba(102, 126, 234, 0.2) 0%, rgba(102, 126, 234, 0.1) 100%);
    padding: 2px 4px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
  }
  
  .highlighted-term:hover {
    background: rgba(102, 126, 234, 0.3);
  }
  
  /* Tooltip for highlighted terms */
  .term-tooltip {
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    background: #1e293b;
    color: white;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 500;
    white-space: nowrap;
    z-index: 10001;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease;
  }
  
  .term-tooltip::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 4px solid transparent;
    border-top-color: #1e293b;
  }
  
  .highlighted-term:hover .term-tooltip {
    opacity: 1;
  }
  
  /* Status Display */
  .intelligence-status {
    position: fixed;
    bottom: 100px;
    right: 30px;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(12px);
    color: white;
    padding: 12px 20px;
    border-radius: 50px;
    font-size: 13px;
    font-weight: 500;
    z-index: 9998;
    display: flex;
    align-items: center;
    gap: 12px;
    animation: slideUp 0.3s ease-out;
    font-family: 'Inter', system-ui, sans-serif;
  }
  
  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .status-spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  
  /* Empty States */
  .empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #64748b;
  }
  
  .empty-state svg {
    width: 48px;
    height: 48px;
    stroke: #cbd5e1;
    margin-bottom: 16px;
  }
  
  .empty-state h3 {
    font-size: 16px;
    font-weight: 600;
    color: #475569;
    margin: 0 0 8px 0;
  }
  
  .empty-state p {
    font-size: 14px;
    margin: 0;
    line-height: 1.5;
  }
  
  /* Responsive Design */
  @media (max-width: 1200px) {
    .news-intelligence-sidebar {
      width: 360px;
    }
  }
  
  @media (max-width: 768px) {
    .news-intelligence-sidebar {
      width: 100vw;
      left: 0;
      transform: translateY(100%);
    }
    
    .news-intelligence-sidebar.open {
      transform: translateY(0);
    }
    
    #augment-article-button {
      bottom: 20px;
      right: 20px;
      padding: 14px 20px;
      font-size: 14px;
    }
  }
`;

const styleSheet = document.createElement("style");
styleSheet.type = "text/css";
styleSheet.innerText = styles;
document.head.appendChild(styleSheet);

// --- Helper Functions ---
function createStyledElement(tag, styles = {}, textContent = "") {
    const el = document.createElement(tag);
    Object.assign(el.style, styles);
    if (textContent) el.textContent = textContent;
    return el;
}

// --- Create Intelligent Sidebar ---
function createIntelligenceSidebar() {
    if (intelligenceSidebar) intelligenceSidebar.remove();

    intelligenceSidebar = document.createElement("div");
    intelligenceSidebar.className = "news-intelligence-sidebar";

    // Header
    const header = document.createElement("div");
    header.className = "sidebar-header";
    header.innerHTML = `
        <div class="sidebar-title">Ανάλυση Άρθρου</div>
        <div class="sidebar-subtitle">Εμπλουτισμένη κατανόηση με AI</div>
        <button class="sidebar-close">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
        </button>
    `;

    // Content
    const content = document.createElement("div");
    content.className = "sidebar-content";

    intelligenceSidebar.appendChild(header);
    intelligenceSidebar.appendChild(content);

    // Close functionality
    header.querySelector('.sidebar-close').onclick = () => {
        intelligenceSidebar.classList.remove('open');
        setTimeout(() => {
            if (intelligenceSidebar && !intelligenceSidebar.classList.contains('open')) {
                document.body.style.marginRight = '0';
            }
        }, 400);
    };

    document.body.appendChild(intelligenceSidebar);
    return content;
}

// --- Enhanced Text Formatting ---
function formatGreekText(text) {
    if (!text) return '';
    
    // Enhanced Greek text processing with X post linking
    let formatted = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code style="background: rgba(102, 126, 234, 0.1); padding: 2px 4px; border-radius: 4px; font-size: 0.9em;">$1</code>')
        .replace(/^\s*[-•*]\s+(.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ul style="margin: 12px 0; padding-left: 20px;">$1</ul>')
        .replace(/^\s*\d+\.\s+(.+)$/gm, '<li>$1</li>')
        .replace(/(<li>.*<\/li>)/s, '<ol style="margin: 12px 0; padding-left: 20px;">$1</ol>');
    
    // Add X post linking
    return linkifyXPosts(formatted);
}

// --- Enhanced Viewpoint Categorization ---
function categorizeViewpoint(text) {
    const supportingKeywords = ['υποστηρίζει', 'συμφωνεί', 'επιβεβαιώνει', 'θετικά'];
    const opposingKeywords = ['αντιτίθεται', 'διαφωνεί', 'επικρίνει', 'αρνητικά', 'αμφισβητεί'];
    const neutralKeywords = ['αναλύει', 'εξετάζει', 'παρουσιάζει', 'σημειώνει'];
    
    const lowerText = text.toLowerCase();
    
    if (supportingKeywords.some(keyword => lowerText.includes(keyword))) {
        return { type: 'υποστηρικτική', color: '#10b981' };
    } else if (opposingKeywords.some(keyword => lowerText.includes(keyword))) {
        return { type: 'αντίθετη', color: '#f59e0b' };
    } else if (neutralKeywords.some(keyword => lowerText.includes(keyword))) {
        return { type: 'ουδέτερη', color: '#6366f1' };
    }
    
    return { type: 'πρόσθετη', color: '#8b5cf6' };
}

// --- Article Text Highlighting ---
function highlightTermsInArticle(terms) {
    if (!terms || terms.length === 0) return;
    
    const articleSelectors = [
        'article', '[role="main"]', '.article-content', '.post-content', 
        '.entry-content', 'main', '.content', '#content'
    ];
    
    let articleElement = null;
    for (const selector of articleSelectors) {
        articleElement = document.querySelector(selector);
        if (articleElement) break;
    }
    
    if (!articleElement) {
        // Fallback: find largest text container
        const textElements = Array.from(document.querySelectorAll('div, section, article'))
            .filter(el => el.textContent.length > 500)
            .sort((a, b) => b.textContent.length - a.textContent.length);
        articleElement = textElements[0];
    }
    
    if (!articleElement) return;
    
    terms.forEach(termData => {
        const term = termData.term;
        const explanation = termData.explanation;
        
        const walker = document.createTreeWalker(
            articleElement,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        const textNodes = [];
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.toLowerCase().includes(term.toLowerCase())) {
                textNodes.push(node);
            }
        }
        
        textNodes.forEach(textNode => {
            const parent = textNode.parentNode;
            if (parent.tagName === 'SCRIPT' || parent.tagName === 'STYLE') return;
            if (parent.closest('.highlighted-term')) return; // Avoid double highlighting
            
            const regex = new RegExp(`(${term})`, 'gi');
            const html = textNode.textContent.replace(regex, 
                `<span class="highlighted-term" data-term="${term}" data-explanation="${explanation}">
                    $1
                    <div class="term-tooltip">${term}</div>
                </span>`
            );
            
            if (html !== textNode.textContent) {
                const wrapper = document.createElement('span');
                wrapper.innerHTML = html;
                parent.replaceChild(wrapper, textNode);
            }
        });
    });
    
    // Add click handlers for highlighted terms
    document.querySelectorAll('.highlighted-term').forEach(element => {
        element.addEventListener('click', (e) => {
            e.preventDefault();
            const term = element.dataset.term;
            const termCard = document.querySelector(`[data-term-card="${term}"]`);
            if (termCard) {
                termCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                termCard.style.background = 'rgba(102, 126, 234, 0.1)';
                setTimeout(() => {
                    termCard.style.background = '';
                }, 2000);
            }
        });
    });
}

// --- Render Functions ---
function renderOverview(jargonData, viewpointsData, panel) {
    const overview = document.createElement('div');
    overview.className = 'insights-overview';
    
    let termsCount = 0;
    if (jargonData?.terms) termsCount = jargonData.terms.length;
    else if (Array.isArray(jargonData)) termsCount = jargonData.length;
    
    const hasContext = viewpointsData && viewpointsData.trim() !== "";
    
    overview.innerHTML = `
        <h3 style="margin: 0 0 16px 0; font-size: 16px; font-weight: 600; color: #1e293b;">
            📊 Επισκόπηση Ανάλυσης
        </h3>
        <div class="overview-stats">
            <div class="stat-item">
                <div class="stat-number">${termsCount}</div>
                <div class="stat-label">Βασικοί Όροι</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">${hasContext ? '✓' : '—'}</div>
                <div class="stat-label">Πλαίσιο & Ανάλυση</div>
            </div>
        </div>
        <p style="margin: 16px 0 0 0; font-size: 13px; color: #64748b; line-height: 1.5;">
            Εντοπίστηκαν ${termsCount} σημαντικοί όροι${hasContext ? ' και πρόσθετο πλαίσιο για βαθύτερη κατανόηση' : ''}.
        </p>
    `;
    
    panel.appendChild(overview);
    
    // Add progressive analysis options
    const progressiveOptions = document.createElement('div');
    progressiveOptions.style.cssText = `
        margin: 20px;
        padding: 16px;
        background: linear-gradient(135deg, #f0f4ff 0%, #e8efff 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
    `;
    
    progressiveOptions.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <div style="width: 32px; height: 32px; background: white; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                🚀
            </div>
            <div>
                <h4 style="margin: 0; font-size: 14px; font-weight: 600; color: #1e293b;">Εμβάθυνση Ανάλυσης</h4>
                <p style="margin: 2px 0 0 0; font-size: 12px; color: #64748b;">Επιλέξτε πρόσθετες αναλύσεις για περισσότερες πληροφορίες</p>
            </div>
        </div>
        <!-- Reader Mode Toggle (Prominent) -->
        <button class="reader-mode-toggle" id="reader-mode-toggle" style="width: 100%; padding: 12px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 8px; cursor: pointer; transition: all 0.2s; font-size: 13px; font-weight: 600; margin-bottom: 12px; display: flex; align-items: center; justify-content: center; gap: 8px;">
            <span style="font-size: 18px;">📖</span>
            <span>Καθαρή Προβολή - Χωρίς Διαφημίσεις</span>
        </button>
        
        <div class="analysis-options" style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <button class="analysis-option" data-analysis="fact-check" style="padding: 10px; background: white; border: 1px solid #e5e7eb; border-radius: 8px; cursor: pointer; transition: all 0.2s; font-size: 12px; text-align: left;">
                <span style="font-size: 16px; margin-right: 4px;">✔️</span>
                <strong>Έλεγχος Γεγονότων</strong>
                <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Επαλήθευση ισχυρισμών</div>
            </button>
            <button class="analysis-option" data-analysis="bias" style="padding: 10px; background: white; border: 1px solid #e5e7eb; border-radius: 8px; cursor: pointer; transition: all 0.2s; font-size: 12px; text-align: left;">
                <span style="font-size: 16px; margin-right: 4px;">⚖️</span>
                <strong>Ανάλυση Μεροληψίας</strong>
                <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Πολιτική κλίση & τόνος</div>
            </button>
            <button class="analysis-option" data-analysis="timeline" style="padding: 10px; background: white; border: 1px solid #e5e7eb; border-radius: 8px; cursor: pointer; transition: all 0.2s; font-size: 12px; text-align: left;">
                <span style="font-size: 16px; margin-right: 4px;">📅</span>
                <strong>Χρονολόγιο</strong>
                <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Εξέλιξη της ιστορίας</div>
            </button>
            <button class="analysis-option" data-analysis="expert" style="padding: 10px; background: white; border: 1px solid #e5e7eb; border-radius: 8px; cursor: pointer; transition: all 0.2s; font-size: 12px; text-align: left;">
                <span style="font-size: 16px; margin-right: 4px;">🎓</span>
                <strong>Απόψεις Ειδικών</strong>
                <div style="font-size: 11px; color: #6b7280; margin-top: 2px;">Από X & ειδήσεις</div>
            </button>
        </div>
    `;
    
    panel.appendChild(progressiveOptions);
    
    // Add event listeners for progressive analysis
    progressiveOptions.querySelectorAll('.analysis-option').forEach(button => {
        button.addEventListener('mouseenter', () => {
            button.style.transform = 'translateY(-2px)';
            button.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
        });
        button.addEventListener('mouseleave', () => {
            button.style.transform = 'translateY(0)';
            button.style.boxShadow = 'none';
        });
        button.addEventListener('click', () => {
            handleProgressiveAnalysis(button.dataset.analysis);
        });
    });
    
    // Add reader mode toggle functionality
    const readerModeToggle = progressiveOptions.querySelector('#reader-mode-toggle');
    readerModeToggle.addEventListener('click', () => {
        toggleReaderMode();
    });
    readerModeToggle.addEventListener('mouseenter', () => {
        readerModeToggle.style.transform = 'translateY(-2px)';
        readerModeToggle.style.boxShadow = '0 6px 20px rgba(16, 185, 129, 0.4)';
    });
    readerModeToggle.addEventListener('mouseleave', () => {
        readerModeToggle.style.transform = 'translateY(0)';
        readerModeToggle.style.boxShadow = 'none';
    });
}

function renderTerms(jargonData, citationsData, panel) {
    const section = document.createElement('div');
    section.className = 'intelligence-section';
    
    const sectionHeader = document.createElement('div');
    sectionHeader.className = 'section-header';
    sectionHeader.innerHTML = `
        <div class="section-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#667eea" stroke-width="2">
                <path d="M12 2L2 7L12 12L22 7L12 2Z"/>
                <path d="M2 17L12 22L22 17"/>
                <path d="M2 12L12 17L22 12"/>
            </svg>
        </div>
        <h3 class="section-title">📚 Επεξήγηση Όρων</h3>
    `;
    
    section.appendChild(sectionHeader);
    
    let termsArray = [];
    if (jargonData?.terms && Array.isArray(jargonData.terms)) {
        termsArray = jargonData.terms;
    } else if (Array.isArray(jargonData)) {
        termsArray = jargonData;
    } else if (typeof jargonData === 'object' && jargonData?.term) {
        termsArray = [jargonData];
    }
    
    if (termsArray.length > 0) {
        termsArray.forEach((item, index) => {
            if (item.term && item.explanation) {
                const termCard = document.createElement('div');
                termCard.className = 'term-card';
                termCard.setAttribute('data-term-card', item.term);
                
                termCard.innerHTML = `
                    <div class="term-title">
                        <span>${item.term}</span>
                        <button class="term-highlight-btn" title="Επισήμανση στο άρθρο">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#667eea" stroke-width="2">
                                <path d="M15 3L21 9L9 21L3 21L3 15L15 3Z"/>
                            </svg>
                        </button>
                    </div>
                    <div class="term-explanation">${formatGreekText(item.explanation)}</div>
                `;
                
                section.appendChild(termCard);
            }
        });
        
        // Highlight terms in article after rendering
        setTimeout(() => highlightTermsInArticle(termsArray), 500);
    } else {
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M9 11H15M9 15H15M12 2L2 7V17L12 22L22 17V7L12 2Z"/>
            </svg>
            <h3>Δεν βρέθηκαν όροι</h3>
            <p>Δεν εντοπίστηκαν συγκεκριμένοι όροι που χρειάζονται επεξήγηση σε αυτό το άρθρο.</p>
        `;
        section.appendChild(emptyState);
    }
    
    if (citationsData && citationsData.length > 0) {
        renderCitations(citationsData, section, "Πηγές επεξηγήσεων");
    }
    
    panel.appendChild(section);
}

function renderViewpoints(viewpointsData, citationsData, panel) {
    const section = document.createElement('div');
    section.className = 'intelligence-section';
    
    const sectionHeader = document.createElement('div');
    sectionHeader.className = 'section-header';
    sectionHeader.innerHTML = `
        <div class="section-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2">
                <path d="M3 3h18v18H3V3z"/>
                <path d="M3 9h18"/>
                <path d="M9 3v18"/>
            </svg>
        </div>
        <h3 class="section-title">🌐 Πλαίσιο & Ανάλυση</h3>
    `;
    
    section.appendChild(sectionHeader);
    
    if (viewpointsData && viewpointsData.trim() !== "") {
        const contextIntro = document.createElement('p');
        contextIntro.style.cssText = 'margin: 0 0 16px 0; font-size: 13px; color: #64748b; line-height: 1.5;';
        contextIntro.textContent = 'Πρόσθετες πληροφορίες και ανάλυση για καλύτερη κατανόηση του θέματος:';
        section.appendChild(contextIntro);
        
        const formattedViewpoints = formatEnhancedViewpoints(viewpointsData);
        section.insertAdjacentHTML('beforeend', formattedViewpoints);
    } else {
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M21 16V8C20.9996 7.64927 20.9071 7.30481 20.7315 7.00116C20.556 6.69751 20.3037 6.44536 20 6.27V6C20 5.46957 19.7893 4.96086 19.4142 4.58579C19.0391 4.21071 18.5304 4 18 4H6C5.46957 4 4.96086 4.21071 4.58579 4.58579C4.21071 4.96086 4 5.46957 4 6V6.27C3.69625 6.44536 3.44397 6.69751 3.26846 7.00116C3.09294 7.30481 3.00036 7.64927 3 8V16C3 16.7956 3.31607 17.5587 3.87868 18.1213C4.44129 18.6839 5.20435 19 6 19H18C18.7956 19 19.5587 18.6839 20.1213 18.1213C20.6839 17.5587 21 16.7956 21 16Z"/>
            </svg>
            <h3>Δεν βρέθηκε πρόσθετο πλαίσιο</h3>
            <p>Δεν εντοπίστηκαν πρόσθετες πληροφορίες για αυτό το θέμα.</p>
        `;
        section.appendChild(emptyState);
    }
    
    if (citationsData && citationsData.length > 0) {
        renderCitations(citationsData, section, "Πηγές πληροφοριών");
    }
    
    panel.appendChild(section);
}

// --- Enhanced Viewpoint Formatting ---
function formatEnhancedViewpoints(text) {
    const lines = text.split('\n').filter(line => line.trim());
    let html = '';
    let currentViewpoint = null;
    
    lines.forEach((line, index) => {
        const trimmedLine = line.trim();
        const isHeader = /^(\d+[\.\)]\s*|[-•*]\s*|.*:$)/.test(trimmedLine);
        const isBulletPoint = /^[-•*]\s+/.test(trimmedLine);
        
        if (isHeader && !isBulletPoint) {
            if (currentViewpoint) {
                html += '</div></div>';
            }
            
            const category = categorizeViewpoint(trimmedLine);
            let headerText = trimmedLine.replace(/^(\d+[\.\)]\s*|[-•*]\s*)/, '').replace(/:$/, '');
            
            html += `<div class="viewpoint-card">
                        <div class="viewpoint-type" style="background: ${category.color}20; color: ${category.color};">
                            ${category.type.toUpperCase()}
                        </div>
                        <div class="viewpoint-content">
                            <strong>${headerText}</strong>`;
            currentViewpoint = true;
        } else if (isBulletPoint) {
            const bulletText = trimmedLine.replace(/^[-•*]\s+/, '');
            html += `<ul><li>${formatGreekText(bulletText)}</li></ul>`;
        } else {
            if (!currentViewpoint) {
                const category = categorizeViewpoint(trimmedLine);
                html += `<div class="viewpoint-card">
                            <div class="viewpoint-type" style="background: ${category.color}20; color: ${category.color};">
                                ${category.type.toUpperCase()}
                            </div>
                            <div class="viewpoint-content">`;
                currentViewpoint = true;
            }
            html += `<p style="margin: 8px 0;">${formatGreekText(trimmedLine)}</p>`;
        }
    });
    
    if (currentViewpoint) {
        html += '</div></div>';
    }
    
    if (!html) {
        const category = categorizeViewpoint(text);
        html = `<div class="viewpoint-card">
                    <div class="viewpoint-type" style="background: ${category.color}20; color: ${category.color};">
                        ${category.type.toUpperCase()}
                    </div>
                    <div class="viewpoint-content">${formatGreekText(text)}</div>
                </div>`;
    }
    
    return html;
}

function renderCitations(citationsArray, parentElement, titleText) {
    if (!citationsArray || citationsArray.length === 0) return;
    
    const citationsSection = document.createElement('div');
    citationsSection.className = 'citations-section';
    
    const citationsToggle = document.createElement('div');
    citationsToggle.className = 'citations-toggle';
    citationsToggle.innerHTML = `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 18L15 12L9 6"/>
        </svg>
        ${titleText} (${citationsArray.length})
    `;
    
    const citationsGrid = document.createElement('div');
    citationsGrid.className = 'citations-grid';
    
    citationsArray.forEach((citation, index) => {
            if (typeof citation === 'string') {
            const citationLink = document.createElement('a');
            citationLink.className = 'citation-link';
            citationLink.href = citation;
            citationLink.target = '_blank';
            citationLink.rel = 'noopener noreferrer';
            
            let domainText = citation;
                try {
                    const url = new URL(citation);
                domainText = url.hostname.replace('www.', '');
                } catch (e) {
                domainText = citation.length > 30 ? citation.substring(0, 27) + '...' : citation;
            }
            
            citationLink.innerHTML = `
                <div class="citation-favicon"></div>
                <div class="citation-domain">${domainText}</div>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6m4-3h6v6m-11 5L21 3"/>
                </svg>
            `;
            
            citationsGrid.appendChild(citationLink);
        }
    });
    
    citationsToggle.onclick = () => {
        citationsToggle.classList.toggle('expanded');
        citationsGrid.classList.toggle('expanded');
    };
    
    citationsSection.appendChild(citationsToggle);
    citationsSection.appendChild(citationsGrid);
    parentElement.appendChild(citationsSection);
}

// --- Status Display Function ---
function updateStatusDisplay(message) {
    if (!statusDisplay) {
        statusDisplay = document.createElement('div');
        statusDisplay.className = 'intelligence-status';
        document.body.appendChild(statusDisplay);
    }
    if (message) {
        statusDisplay.innerHTML = `<div class="status-spinner"></div><span>${message}</span>`;
        statusDisplay.style.display = 'flex';
    } else {
        statusDisplay.style.display = 'none';
    }
}

// --- Main Event Listener ---
augmentButton.addEventListener("click", () => {
    console.log("Κλικ στο κουμπί ανάλυσης άρθρου.");
    augmentButton.querySelector("span").textContent = "Αναλύεται...";
    augmentButton.classList.add('processing');
    augmentButton.disabled = true;
    updateStatusDisplay("Σύνδεση με την υπηρεσία AI...");

    const articleUrl = window.location.href;
    window.currentArticleUrl = articleUrl; // Store for progressive analysis

    chrome.runtime.sendMessage({ type: "AUGMENT_ARTICLE", url: articleUrl }, (response) => {
        augmentButton.querySelector("span").textContent = "Ανάλυση Άρθρου";
        augmentButton.classList.remove('processing');
        augmentButton.disabled = false;
        updateStatusDisplay(null);

        if (chrome.runtime.lastError) {
            console.error("Σφάλμα αποστολής μηνύματος:", chrome.runtime.lastError.message);
            updateStatusDisplay(`Σφάλμα: ${chrome.runtime.lastError.message}`);
            
            const contentPanel = createIntelligenceSidebar();
            const errorState = document.createElement('div');
            errorState.className = 'empty-state';
            errorState.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
                <h3>Σφάλμα επικοινωνίας</h3>
                <p>Δεν ήταν δυνατή η σύνδεση με την υπηρεσία. Παρακαλώ ελέγξτε τη σύνδεσή σας και δοκιμάστε ξανά.</p>
            `;
            contentPanel.appendChild(errorState);
            intelligenceSidebar.classList.add('open');
            document.body.style.marginRight = '420px';
            return;
        }
        
        console.log("Απάντηση από το background script:", response);

        const contentPanel = createIntelligenceSidebar();
        if (response && response.success) {
            updateStatusDisplay("Επεξεργασία insights...");
            currentData = response;
            
            renderOverview(response.jargon, response.viewpoints, contentPanel);
            renderTerms(response.jargon, response.jargon_citations, contentPanel);
            renderViewpoints(response.viewpoints, response.viewpoints_citations, contentPanel);
            
            intelligenceSidebar.classList.add('open');
            document.body.style.marginRight = '420px';
            updateStatusDisplay(null);
        } else {
            const errorMsg = response ? response.error : "Άγνωστο σφάλμα από το background script";
            updateStatusDisplay(`Αποτυχία: ${errorMsg}`);
            
            const errorState = document.createElement('div');
            errorState.className = 'empty-state';
            errorState.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
                <h3>Αποτυχία ανάλυσης άρθρου</h3>
                <p>${errorMsg}</p>
            `;
            contentPanel.appendChild(errorState);
            intelligenceSidebar.classList.add('open');
            document.body.style.marginRight = '420px';
        }
    });
});

// --- Progress Updates ---
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "PROGRESS_UPDATE") {
        console.log("Ενημέρωση προόδου από background:", message.status);
        updateStatusDisplay(message.status);
    }
});

// --- Keyboard Shortcuts ---
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Shift + A: Toggle sidebar
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
        e.preventDefault();
        if (intelligenceSidebar && intelligenceSidebar.classList.contains('open')) {
            intelligenceSidebar.classList.remove('open');
            document.body.style.marginRight = '0';
        } else if (intelligenceSidebar) {
            intelligenceSidebar.classList.add('open');
            document.body.style.marginRight = '420px';
        } else {
            augmentButton.click();
        }
    }
    
    // Escape: Close sidebar
    if (e.key === 'Escape' && intelligenceSidebar && intelligenceSidebar.classList.contains('open')) {
        intelligenceSidebar.classList.remove('open');
        document.body.style.marginRight = '0';
    }
});

// --- Page Visibility Handling ---
document.addEventListener('visibilitychange', () => {
    if (document.hidden && intelligenceSidebar) {
        // Pause any animations when page is hidden
        intelligenceSidebar.style.animationPlayState = 'paused';
    } else if (intelligenceSidebar) {
        intelligenceSidebar.style.animationPlayState = 'running';
    }
});

// --- Responsive Handling ---
function handleResize() {
    if (window.innerWidth <= 768 && intelligenceSidebar && intelligenceSidebar.classList.contains('open')) {
        document.body.style.marginRight = '0';
    } else if (window.innerWidth > 768 && intelligenceSidebar && intelligenceSidebar.classList.contains('open')) {
        document.body.style.marginRight = '420px';
    }
}

window.addEventListener('resize', handleResize);

// New function to handle progressive analysis
function handleProgressiveAnalysis(analysisType) {
    console.log('handleProgressiveAnalysis called with:', analysisType);
    
    if (!currentData || !window.currentArticleUrl) {
        console.error('Missing currentData or currentArticleUrl');
        return;
    }
    
    const analysisButton = document.querySelector(`[data-analysis="${analysisType}"]`);
    if (!analysisButton) {
        console.error('Analysis button not found for type:', analysisType);
        return;
    }
    
    const originalContent = analysisButton.innerHTML;
    analysisButton.innerHTML = '<div style="text-align: center;">⏳ Αναλύεται...</div>';
    analysisButton.disabled = true;
    
    // Create analysis request with specific sources based on type
    const searchParams = {
        mode: "on",
        return_citations: true,
        sources: []
    };
    
    switch(analysisType) {
        case 'fact-check':
            searchParams.sources = [
                { type: "web" },
                { type: "news" }
            ];
            break;
        case 'expert':
            searchParams.sources = [
                { type: "x" },
                { type: "news" }
            ];
            // Add more specific search parameters for experts
            searchParams.max_results = 10; // Limit results for quality
            break;
        default:
            searchParams.sources = [
                { type: "web" },
                { type: "x" },
                { type: "news" }
            ];
    }
    
    // Send request for deeper analysis
    chrome.runtime.sendMessage({ 
        type: "DEEP_ANALYSIS",
        url: window.currentArticleUrl,
        analysisType: analysisType,
        searchParams: searchParams
    }, (response) => {
        console.log('Deep analysis response for', analysisType, ':', response);
        
        analysisButton.innerHTML = originalContent;
        analysisButton.disabled = false;
        
        if (chrome.runtime.lastError) {
            console.error('Chrome runtime error:', chrome.runtime.lastError);
            showAnalysisError(analysisType, 'Σφάλμα επικοινωνίας με την υπηρεσία');
            return;
        }
        
        if (response && response.success) {
            console.log('Calling displayDeepAnalysis with:', analysisType, response.data, response.citations);
            displayDeepAnalysis(analysisType, response.data, response.citations);
        } else {
            const errorMsg = response ? response.error : 'Unknown error';
            console.error('Analysis failed:', errorMsg);
            showAnalysisError(analysisType, errorMsg);
        }
    });
}

// Function to display deep analysis results
function displayDeepAnalysis(analysisType, data, citations = []) {
    console.log('displayDeepAnalysis called with:', analysisType, data, citations);
    
    const sidebar = document.querySelector('.sidebar-content');
    if (!sidebar) {
        console.error('Sidebar not found');
        return;
    }
    
    // Remove any existing deep analysis sections first
    const existingAnalysis = sidebar.querySelectorAll('.deep-analysis');
    existingAnalysis.forEach(section => section.remove());
    
    const analysisSection = document.createElement('div');
    analysisSection.className = 'intelligence-section deep-analysis';
    analysisSection.style.cssText = 'animation: slideInFromRight 0.4s ease-out; opacity: 1;';
    
    let icon, title, content;
    
            try {
            switch(analysisType) {
                case 'fact-check':
                    icon = '✔️';
                    title = 'Έλεγχος Γεγονότων';
                    content = formatFactCheckResults(data);
                    break;
                case 'bias':
                    icon = '⚖️';
                    title = 'Ανάλυση Μεροληψίας';
                    content = formatBiasAnalysis(data);
                    break;
                case 'timeline':
                    icon = '📅';
                    title = 'Χρονολόγιο Εξελίξεων';
                    content = formatTimeline(data);
                    break;
                case 'expert':
                    icon = '🎓';
                    title = 'Απόψεις Ειδικών';
                    content = formatExpertOpinions(data);
                    break;
                default:
                    throw new Error(`Unknown analysis type: ${analysisType}`);
            }
        
        console.log('Generated content for', analysisType, ':', content.substring(0, 200) + '...');
        
    } catch (error) {
        console.error('Error generating content for', analysisType, ':', error);
        content = `<div style="padding: 20px; text-align: center; color: #dc2626;">
            <h4>Σφάλμα εμφάνισης</h4>
            <p>Υπήρξε πρόβλημα με την εμφάνιση των αποτελεσμάτων.</p>
            <p style="font-size: 12px; color: #6b7280;">Error: ${error.message}</p>
        </div>`;
    }
    
    // Build the section safely
    const headerHTML = `
        <div class="section-header" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-left-color: #f59e0b;">
            <div class="section-icon" style="background: white;">
                <span style="font-size: 18px;">${icon}</span>
            </div>
            <h3 class="section-title">${title}</h3>
            <button class="close-analysis" style="margin-left: auto; background: none; border: none; cursor: pointer; padding: 4px; border-radius: 4px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#92400e" stroke-width="2">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </button>
        </div>
    `;
    
    const contentHTML = `
        <div class="analysis-content" style="padding: 16px 20px;">
            ${content}
        </div>
    `;
    
    try {
        analysisSection.innerHTML = headerHTML + contentHTML;
    } catch (error) {
        console.error('Error setting innerHTML:', error);
        analysisSection.innerHTML = headerHTML + `<div style="padding: 20px; color: #dc2626;">Error rendering content: ${error.message}</div>`;
    }
    
    // Find insertion point more safely
    let insertionPoint = null;
    const insightsOverview = sidebar.querySelector('.insights-overview');
    if (insightsOverview && insightsOverview.nextElementSibling) {
        insertionPoint = insightsOverview.nextElementSibling;
    } else {
        // Fallback: find last .intelligence-section or append to sidebar
        const sections = sidebar.querySelectorAll('.intelligence-section');
        insertionPoint = sections.length > 0 ? sections[sections.length - 1] : null;
    }
    
    try {
        if (insertionPoint) {
            console.log('Inserting after element:', insertionPoint);
            insertionPoint.insertAdjacentElement('afterend', analysisSection);
        } else {
            console.log('Appending to sidebar');
            sidebar.appendChild(analysisSection);
        }
        console.log('Analysis section inserted successfully. Element:', analysisSection);
        console.log('Element has innerHTML length:', analysisSection.innerHTML.length);
        console.log('Element style:', analysisSection.style.cssText);
        
        // Force a reflow
        analysisSection.offsetHeight;
        
        // Double-check it's in the DOM
        setTimeout(() => {
            const stillInDOM = document.contains(analysisSection);
            console.log('Section still in DOM after 500ms:', stillInDOM);
            if (stillInDOM) {
                console.log('Section computed style:', window.getComputedStyle(analysisSection).display);
                console.log('Section visibility:', window.getComputedStyle(analysisSection).visibility);
                console.log('Section opacity:', window.getComputedStyle(analysisSection).opacity);
            }
        }, 500);
        
    } catch (error) {
        console.error('Error inserting analysis section:', error);
        return;
    }
    
    // Add citations if available
    if (citations && citations.length > 0) {
        try {
            renderCitations(citations, analysisSection, `Πηγές ανάλυσης (${citations.length})`);
        } catch (error) {
            console.error('Error rendering citations:', error);
        }
    }
    
    // Add close functionality with error handling
    try {
        const closeButton = analysisSection.querySelector('.close-analysis');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                analysisSection.style.animation = 'slideOutToRight 0.3s ease-out';
                setTimeout(() => {
                    if (analysisSection.parentNode) {
                        analysisSection.remove();
                    }
                }, 300);
            });
            
            // Add hover effect
            closeButton.addEventListener('mouseenter', () => {
                closeButton.style.background = 'rgba(220, 38, 38, 0.1)';
            });
            closeButton.addEventListener('mouseleave', () => {
                closeButton.style.background = 'none';
            });
        }
    } catch (error) {
        console.error('Error setting up close button:', error);
    }
    
    // Scroll to the new section with delay to ensure it's rendered
    setTimeout(() => {
        try {
            analysisSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } catch (error) {
            console.error('Error scrolling to section:', error);
        }
    }, 100);
}

// Helper function to calculate expert opinion reliability
function calculateExpertReliability(expert) {
    let score = 0.5; // Base score
    
    // Has credentials +0.2
    if (expert.credentials && expert.credentials.trim() !== '') score += 0.2;
    
    // Has specific quote +0.2
    if (expert.quote && expert.quote.trim() !== '' && expert.quote !== expert.opinion) score += 0.2;
    
    // Has verified source URL +0.3
    if (expert.source_url && expert.source_url.trim() !== '' && expert.source_url.includes('http')) score += 0.3;
    
    // Trusted source types +0.1
    if (expert.source === 'news' || expert.source === 'x') score += 0.1;
    
    // Has clear stance +0.1
    if (expert.stance && expert.stance !== 'ουδέτερη') score += 0.1;
    
    return Math.min(score, 1.0); // Cap at 1.0
}

// Helper functions for formatting different analysis types
function formatFactCheckResults(data) {
    try {
        if (!data) {
            return '<div style="padding: 20px; text-align: center; color: #6b7280;">Δεν υπάρχουν δεδομένα για εμφάνιση</div>';
        }
        
        const credibilityColors = {
            'υψηλή': '#16a34a',
            'μέτρια': '#f59e0b', 
            'χαμηλή': '#dc2626'
        };
        
        const credibilityColor = credibilityColors[data.overall_credibility] || '#6b7280';
    
    return `
        <div class="fact-checks">
            <div style="padding: 12px; background: ${data.overall_credibility === 'υψηλή' ? '#f0fdf4' : data.overall_credibility === 'μέτρια' ? '#fffbeb' : '#fef2f2'}; border: 1px solid ${credibilityColor}30; border-radius: 8px; margin-bottom: 12px;">
                <strong style="color: ${credibilityColor};">📊 Συνολική Αξιοπιστία: ${data.overall_credibility || 'Άγνωστη'}</strong>
                ${data.missing_context ? `<p style="margin: 8px 0 0 0; font-size: 13px; color: #6b7280;">${data.missing_context}</p>` : ''}
            </div>
            
            ${data.claims && Array.isArray(data.claims) && data.claims.length > 0 ? data.claims.map(claim => `
                <div style="padding: 12px; background: white; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 8px;">
                    <div style="font-weight: 600; margin-bottom: 8px; font-size: 14px;">"${claim.statement}"</div>
                                            <div style="font-size: 13px; color: ${claim.verified ? '#16a34a' : '#dc2626'}; margin-bottom: 8px;">
                            ${claim.verified ? '✓ Επαληθευμένο' : '✗ Αμφισβητήσιμο'}: ${claim.explanation || 'Δεν υπάρχει εξήγηση'}
                        </div>
                    ${claim.sources && claim.sources.length > 0 ? `
                        <div style="font-size: 11px; color: #6b7280;">
                            <strong>Πηγές:</strong> ${claim.sources.slice(0, 2).join(', ')}${claim.sources.length > 2 ? ` (+${claim.sources.length - 2} ακόμη)` : ''}
                        </div>
                    ` : ''}
                </div>
            `).join('') : '<p style="color: #6b7280; text-align: center; padding: 20px;">Δεν βρέθηκαν συγκεκριμένοι ισχυρισμοί προς επαλήθευση</p>'}
            
            ${data.red_flags && Array.isArray(data.red_flags) && data.red_flags.length > 0 ? `
                <div style="padding: 12px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; margin-top: 12px;">
                    <strong style="color: #dc2626;">⚠️ Προσοχή:</strong>
                    <ul style="margin: 8px 0 0 0; padding-left: 20px;">
                        ${data.red_flags.map(flag => `<li style="font-size: 13px; margin-bottom: 4px;">${flag}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
    } catch (error) {
        console.error('Error in formatFactCheckResults:', error);
        return `<div style="padding: 20px; text-align: center; color: #dc2626;">
            <h4>Σφάλμα μορφοποίησης</h4>
            <p>Υπήρξε πρόβλημα με την εμφάνιση των αποτελεσμάτων.</p>
        </div>`;
    }
}

function formatBiasAnalysis(data) {
    try {
        console.log('formatBiasAnalysis called with:', data);
        
        if (!data) {
            return '<div style="padding: 20px; text-align: center; color: #6b7280;">Δεν υπάρχουν δεδομένα για εμφάνιση</div>';
        }
        
        const confidenceColors = {
            'υψηλή': '#16a34a',
            'μέτρια': '#f59e0b',
            'χαμηλή': '#dc2626'
        };
        
        const toneColors = {
            'θετικός': '#16a34a',
            'ουδέτερος': '#6b7280',
            'αρνητικός': '#dc2626',
            'ανάμεικτος': '#f59e0b'
        };
    
    return `
        <div class="bias-analysis">
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                <div style="text-align: center; padding: 12px; background: #f3f4f6; border-radius: 8px;">
                    <div style="font-size: 24px; margin-bottom: 4px;">🎯</div>
                    <div style="font-size: 12px; color: #6b7280;">Πολιτική Κλίση</div>
                    <div style="font-weight: 600; color: #1e293b; font-size: 13px;">${data.political_lean || 'Ουδέτερο'}</div>
                </div>
                <div style="text-align: center; padding: 12px; background: #f3f4f6; border-radius: 8px;">
                    <div style="font-size: 24px; margin-bottom: 4px;">🎭</div>
                    <div style="font-size: 12px; color: #6b7280;">Συναισθηματικός Τόνος</div>
                    <div style="font-weight: 600; color: ${toneColors[data.emotional_tone] || '#6b7280'}; font-size: 13px;">${data.emotional_tone || 'Ουδέτερος'}</div>
                </div>
                <div style="text-align: center; padding: 12px; background: #f3f4f6; border-radius: 8px;">
                    <div style="font-size: 24px; margin-bottom: 4px;">📊</div>
                    <div style="font-size: 12px; color: #6b7280;">Βεβαιότητα</div>
                    <div style="font-weight: 600; color: ${confidenceColors[data.confidence] || '#6b7280'}; font-size: 13px;">${data.confidence || 'Μέτρια'}</div>
                </div>
            </div>
            
            ${data.language_analysis ? `
                <div style="padding: 12px; background: white; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 12px;">
                    <strong style="color: #1e293b;">🔍 Ανάλυση Γλώσσας:</strong>
                    <div style="margin-top: 8px;">
                        ${data.language_analysis.framing ? `<p style="margin: 4px 0; font-size: 13px;"><strong>Πλαισίωση:</strong> ${data.language_analysis.framing}</p>` : ''}
                        ${data.language_analysis.loaded_words && data.language_analysis.loaded_words.length > 0 ? `
                            <p style="margin: 4px 0; font-size: 13px;">
                                <strong>Φορτισμένες λέξεις:</strong> ${data.language_analysis.loaded_words.slice(0, 5).map(word => `<span style="background: #fef3c7; padding: 2px 6px; border-radius: 4px; margin: 0 2px;">${word}</span>`).join('')}
                            </p>
                        ` : ''}
                        ${data.language_analysis.missing_perspectives ? `<p style="margin: 4px 0; font-size: 13px;"><strong>Απόψεις που λείπουν:</strong> ${data.language_analysis.missing_perspectives}</p>` : ''}
                    </div>
                </div>
            ` : ''}
            
            ${data.comparison ? `
                <div style="padding: 12px; background: #fefce8; border: 1px solid #fef08a; border-radius: 8px; margin-bottom: 12px;">
                    <strong style="color: #a16207;">📰 Σύγκριση με άλλες πηγές:</strong>
                    <p style="margin: 4px 0 0 0; font-size: 13px; line-height: 1.5;">${data.comparison}</p>
                </div>
            ` : ''}
            
            ${data.recommendations ? `
                <div style="padding: 12px; background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 8px;">
                    <strong style="color: #1e40af;">💡 Συστάσεις:</strong>
                    <p style="margin: 4px 0 0 0; font-size: 13px; line-height: 1.5;">${data.recommendations}</p>
                </div>
            ` : ''}
        </div>
    `;
    } catch (error) {
        console.error('Error in formatBiasAnalysis:', error);
        return `<div style="padding: 20px; text-align: center; color: #dc2626;">
            <h4>Σφάλμα μορφοποίησης</h4>
            <p>Υπήρξε πρόβλημα με την εμφάνιση των αποτελεσμάτων.</p>
        </div>`;
    }
}

function formatTimeline(data) {
    try {
        if (!data) {
            return '<div style="padding: 20px; text-align: center; color: #6b7280;">Δεν υπάρχουν δεδομένα για εμφάνιση</div>';
        }
        
        const importanceColors = {
            'υψηλή': '#dc2626',
            'μέτρια': '#f59e0b',
            'χαμηλή': '#6b7280'
        };
    
    return `
        <div class="timeline">
            ${data.story_title ? `
                <div style="padding: 12px; background: #f8fafc; border-radius: 8px; margin-bottom: 16px; text-align: center;">
                    <strong style="color: #1e293b; font-size: 15px;">📖 ${data.story_title}</strong>
                </div>
            ` : ''}
            
            ${data.events && Array.isArray(data.events) && data.events.length > 0 ? data.events.map((event, index) => {
                const importance = event.importance || 'μέτρια';
                const importanceColor = importanceColors[importance] || '#6b7280';
                const isLatest = index === data.events.length - 1;
                
                return `
                    <div style="display: flex; gap: 12px; margin-bottom: 16px; position: relative;">
                        ${!isLatest ? `<div style="position: absolute; left: 19px; top: 40px; width: 2px; height: calc(100% + 16px); background: #e5e7eb;"></div>` : ''}
                        <div style="width: 40px; height: 40px; background: ${isLatest ? '#667eea' : '#e5e7eb'}; border: 3px solid white; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; z-index: 1; position: relative;">
                            <span style="color: ${isLatest ? 'white' : '#6b7280'}; font-size: 12px; font-weight: 600;">${index + 1}</span>
                        </div>
                        <div style="flex: 1; padding-bottom: 8px;">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                                <span style="font-size: 11px; color: #6b7280; background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">${event.date}</span>
                                <span style="font-size: 10px; color: white; background: ${importanceColor}; padding: 2px 6px; border-radius: 4px; text-transform: uppercase;">${importance}</span>
                            </div>
                            <div style="font-weight: 600; margin-bottom: 6px; color: #1e293b; font-size: 14px;">${linkifyXPosts(event.title)}</div>
                            <div style="font-size: 13px; color: #475569; line-height: 1.5; margin-bottom: 4px;">${linkifyXPosts(event.description)}</div>
                            ${event.source ? `<div style="font-size: 11px; color: #6b7280;"><strong>Πηγή:</strong> ${linkifyXPosts(event.source)}</div>` : ''}
                        </div>
                    </div>
                `;
            }).join('') : '<p style="color: #6b7280; text-align: center; padding: 20px;">Δεν βρέθηκαν γεγονότα για χρονολόγιο</p>'}
            
            ${data.context ? `
                <div style="padding: 12px; background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 8px; margin-top: 16px;">
                    <strong style="color: #1e40af;">🔍 Ιστορικό Πλαίσιο:</strong>
                    <p style="margin: 4px 0 0 0; font-size: 13px; line-height: 1.5;">${linkifyXPosts(data.context)}</p>
                </div>
            ` : ''}
            
            ${data.future_implications ? `
                <div style="padding: 12px; background: #fefce8; border: 1px solid #fef08a; border-radius: 8px; margin-top: 8px;">
                    <strong style="color: #a16207;">🔮 Μελλοντικές Εξελίξεις:</strong>
                    <p style="margin: 4px 0 0 0; font-size: 13px; line-height: 1.5;">${linkifyXPosts(data.future_implications)}</p>
                </div>
            ` : ''}
        </div>
    `;
    } catch (error) {
        console.error('Error in formatTimeline:', error);
        return `<div style="padding: 20px; text-align: center; color: #dc2626;">
            <h4>Σφάλμα μορφοποίησης</h4>
            <p>Υπήρξε πρόβλημα με την εμφάνιση του χρονολογίου.</p>
        </div>`;
    }
}

function formatExpertOpinions(data) {
    try {
        if (!data) {
            return '<div style="padding: 20px; text-align: center; color: #6b7280;">Δεν υπάρχουν δεδομένα για εμφάνιση</div>';
        }
        
        const stanceColors = {
            'υποστηρικτική': '#16a34a',
            'αντίθετη': '#dc2626',
            'ουδέτερη': '#6b7280'
        };
        
        const sourceIcons = {
            'x': '𝕏',
            'news': '📰',
            'web': '🌐'
        };
    
    return `
        <div class="expert-opinions">
            ${data.topic_summary ? `
                <div style="padding: 12px; background: #f8fafc; border-radius: 8px; margin-bottom: 16px;">
                    <strong style="color: #1e293b;">📋 Σύνοψη Θέματος:</strong>
                    <p style="margin: 4px 0 0 0; font-size: 13px; line-height: 1.5;">${linkifyXPosts(data.topic_summary)}</p>
                </div>
            ` : ''}
            
            ${data.experts && Array.isArray(data.experts) && data.experts.length > 0 ? data.experts.map(expert => {
                // Add a reliability indicator based on source URL presence and completeness
                const reliabilityScore = calculateExpertReliability(expert);
                const reliabilityColor = reliabilityScore >= 0.8 ? '#16a34a' : reliabilityScore >= 0.6 ? '#f59e0b' : '#dc2626';
                const reliabilityText = reliabilityScore >= 0.8 ? 'Υψηλή' : reliabilityScore >= 0.6 ? 'Μέτρια' : 'Χαμηλή';
                
                return `
                <div style="padding: 12px; background: white; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 12px;">
                    <div style="display: flex; align-items: start; gap: 12px; margin-bottom: 10px;">
                        <div style="width: 40px; height: 40px; background: #e0e7ff; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                            <span style="font-size: 18px;">👤</span>
                        </div>
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 2px;">
                                <div style="font-weight: 600; color: #1e293b;">${expert.name}</div>
                                ${expert.stance ? `<span style="font-size: 10px; color: white; background: ${stanceColors[expert.stance] || '#6b7280'}; padding: 2px 6px; border-radius: 4px; text-transform: uppercase;">${expert.stance}</span>` : ''}
                                <span style="font-size: 9px; color: white; background: ${reliabilityColor}; padding: 2px 4px; border-radius: 4px;">📊 ${reliabilityText}</span>
                            </div>
                            <div style="font-size: 12px; color: #6b7280; margin-bottom: 4px;">${expert.credentials}</div>
                            <div style="display: flex; align-items: center; gap: 4px;">
                                <span style="font-size: 12px;">${sourceIcons[expert.source] || '🌐'}</span>
                                <span style="font-size: 11px; color: #6b7280;">${expert.source === 'x' ? 'X/Twitter' : expert.source === 'news' ? 'Ειδήσεις' : 'Web'}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div style="font-size: 13px; line-height: 1.5; color: #374151; margin-bottom: 8px;">
                        "${linkifyXPosts(expert.opinion)}"
                    </div>
                    
                    ${expert.quote && expert.quote !== expert.opinion ? `
                        <div style="padding: 8px 12px; background: #f3f4f6; border-left: 3px solid #6b7280; border-radius: 0 4px 4px 0; margin-top: 8px;">
                            <div style="font-size: 12px; font-style: italic; color: #475569;">"${linkifyXPosts(expert.quote)}"</div>
                        </div>
                    ` : ''}
                    
                    ${expert.source_url && expert.source_url.trim() !== '' ? (() => {
                        const enhancedUrl = enhanceXSourceUrl(expert.source_url);
                        const linkStyle = enhancedUrl.isXPost 
                            ? "font-size: 11px; color: #1d9bf0; text-decoration: none; background: #f0f9ff; padding: 4px 8px; border-radius: 6px; border: 1px solid #bfdbfe;"
                            : "font-size: 11px; color: #6366f1; text-decoration: none;";
                        const icon = enhancedUrl.isXPost ? "🐦" : "📎";
                        return `
                            <div style="margin-top: 8px;">
                                <a href="${enhancedUrl.url}" target="_blank" style="${linkStyle}">${icon} ${enhancedUrl.display}</a>
                                ${enhancedUrl.isXPost ? 
                                    `<span style="font-size: 10px; color: #1d9bf0; margin-left: 8px;">✓ Άμεσος σύνδεσμος X</span>` :
                                    `<span style="font-size: 10px; color: #9ca3af; margin-left: 8px;">⚠️ Επαληθεύστε ότι η πηγή περιέχει το απόσπασμα</span>`
                                }
                            </div>
                        `;
                    })() : `
                        <div style="margin-top: 8px;">
                            <span style="font-size: 10px; color: #9ca3af;">📄 Δεν διαθέσιμη άμεση πηγή για αυτή την άποψη</span>
                        </div>
                    `}
                </div>
            `;
            }).join('') : '<p style="color: #6b7280; text-align: center; padding: 20px;">Δεν βρέθηκαν απόψεις ειδικών</p>'}
            
            ${data.consensus ? `
                <div style="padding: 12px; background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 8px; margin-bottom: 8px;">
                    <strong style="color: #1e40af;">🤝 Συναίνεση Ειδικών:</strong>
                    <p style="margin: 4px 0 0 0; font-size: 13px; line-height: 1.5;">${linkifyXPosts(data.consensus)}</p>
                </div>
            ` : ''}
            
            ${data.key_debates ? `
                <div style="padding: 12px; background: #fefce8; border: 1px solid #fef08a; border-radius: 8px; margin-bottom: 12px;">
                    <strong style="color: #a16207;">⚡ Κύρια Σημεία Διαφωνίας:</strong>
                    <p style="margin: 4px 0 0 0; font-size: 13px; line-height: 1.5;">${linkifyXPosts(data.key_debates)}</p>
                </div>
            ` : ''}
            
            <!-- Source Verification Warning -->
            <div style="padding: 12px; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; margin-top: 12px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">ℹ️</span>
                    <strong style="color: #334155; font-size: 12px;">Σημείωση Επαλήθευσης</strong>
                </div>
                <p style="margin: 4px 0 0 0; font-size: 11px; line-height: 1.4; color: #64748b;">
                    Οι απόψεις ειδικών εντοπίζονται αυτόματα από τη Live Search. Παρακαλούμε επαληθεύστε τις πηγές πριν τις χρησιμοποιήσετε. 
                    Τα σκορ αξιοπιστίας βασίζονται στην πληρότητα των πληροφοριών και την παρουσία επαληθευμένων πηγών.
                </p>
            </div>
        </div>
    `;
    } catch (error) {
        console.error('Error in formatExpertOpinions:', error);
        return `<div style="padding: 20px; text-align: center; color: #dc2626;">
            <h4>Σφάλμα μορφοποίησης</h4>
            <p>Υπήρξε πρόβλημα με την εμφάνιση των απόψεων ειδικών.</p>
        </div>`;
    }
}

// Add error handling for analysis
function showAnalysisError(analysisType, errorMessage = 'Αποτυχία φόρτωσης ανάλυσης. Δοκιμάστε ξανά.') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        bottom: 120px;
        right: 30px;
        background: #fee2e2;
        border: 1px solid #fecaca;
        color: #991b1b;
        padding: 12px 20px;
        border-radius: 8px;
        font-size: 13px;
        animation: slideUp 0.3s ease-out;
        z-index: 10001;
        max-width: 300px;
        line-height: 1.4;
    `;
    
    const analysisNames = {
        'fact-check': 'Έλεγχος Γεγονότων',
        'bias': 'Ανάλυση Μεροληψίας', 
        'timeline': 'Χρονολόγιο',
        'expert': 'Απόψεις Ειδικών'
    };
    
    notification.innerHTML = `
        <strong>${analysisNames[analysisType] || 'Ανάλυση'}</strong><br>
        ${errorMessage}
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideDown 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Add necessary animations to CSS
const additionalStyles = `
    @keyframes slideOutToRight {
        to {
            opacity: 0;
            transform: translateX(30px);
        }
    }
    
    @keyframes slideDown {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(20px);
        }
    }
    
    .deep-analysis {
        background: linear-gradient(to bottom, #fffbeb, #fef3c7) !important;
        border: 1px solid rgba(251, 191, 36, 0.2) !important;
        border-radius: 12px !important;
        margin: 20px !important;
        overflow: visible !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        min-height: 100px !important;
    }
    
    .deep-analysis .analysis-content {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        min-height: 50px !important;
    }
    
    .analysis-option:hover {
        border-color: #6366f1 !important;
        background: #f5f3ff !important;
    }
    
    .analysis-option:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
    
    .reader-mode-toggle:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4) !important;
    }
`;

// Append additional styles
const existingStyleSheet = document.querySelector('style');
existingStyleSheet.innerText += additionalStyles;

// --- Reader Mode Implementation ---
let isReaderModeActive = false;
let originalPageState = null;

function toggleReaderMode() {
    if (isReaderModeActive) {
        exitReaderMode();
    } else {
        enterReaderMode();
    }
}

function enterReaderMode() {
    // Save original state
    originalPageState = {
        sidebarOpen: false, // Default to false
        bodyMarginRight: '',
        statusDisplayHTML: null,
        statusDisplayStyle: null,
        // bodyHTML, bodyClass, bodyStyle, htmlClass, title are saved later
    };

    // Save Sidebar State
    if (intelligenceSidebar) {
        if (intelligenceSidebar.classList.contains('open')) {
            originalPageState.sidebarOpen = true;
            originalPageState.bodyMarginRight = document.body.style.marginRight;
        }
        intelligenceSidebar.style.display = 'none'; // Hide before saving bodyHTML
    }

    // Save Status Display State
    if (statusDisplay && statusDisplay.style.display !== 'none') {
        originalPageState.statusDisplayHTML = statusDisplay.innerHTML;
        originalPageState.statusDisplayStyle = statusDisplay.style.display;
        statusDisplay.style.display = 'none'; // Hide before saving bodyHTML
    }

    originalPageState.bodyHTML = document.body.innerHTML;
        bodyClass: document.body.className,
        bodyStyle: document.body.getAttribute('style') || '',
        htmlClass: document.documentElement.className,
        title: document.title
    };
    
    // Extract clean content
    const cleanContent = extractCleanContent();
    if (!cleanContent) {
        showReaderModeError("Δεν ήταν δυνατή η εξαγωγή του περιεχομένου του άρθρου.");
        return;
    }
    
    // Apply reader mode
    applyReaderMode(cleanContent);
    isReaderModeActive = true;
    
    // Update toggle button
    updateReaderModeButton(true);
    // Hide the floating buttons when reader mode is active
    if (augmentButton) augmentButton.style.display = 'none';
    if (cleanWebsiteButton) cleanWebsiteButton.style.display = 'none';
    
    // Show success notification
    showReaderModeNotification("📖 Καθαρή προβολή ενεργοποιήθηκε");
}

function exitReaderMode() {
    if (!originalPageState) return;
    
    // Restore original state
    document.body.innerHTML = originalPageState.bodyHTML;
    document.body.className = originalPageState.bodyClass;
    if (originalPageState.bodyStyle) {
        document.body.setAttribute('style', originalPageState.bodyStyle);
    } else {
        document.body.removeAttribute('style');
    }
    document.documentElement.className = originalPageState.htmlClass;
    document.title = originalPageState.title;
    
    isReaderModeActive = false;
    
    // Re-inject our extension elements
    reinjectExtensionElements();
    
    // Show notification
    showReaderModeNotification("🌐 Κανονική προβολή αποκαταστάθηκε");
    // Restore floating buttons' display style
    if (augmentButton) augmentButton.style.display = 'flex';
    if (cleanWebsiteButton) cleanWebsiteButton.style.display = 'flex';
}

function extractCleanContent() {
    // Priority selectors for main content
    const contentSelectors = [
        'article',
        '[role="main"]',
        '.article-content',
        '.post-content',
        '.entry-content',
        '.content-body',
        '.article-body',
        '.story-body',
        'main',
        '.main-content',
        '#main-content',
        '.content',
        '#content'
    ];
    
    let mainContent = null;
    
    // Try to find main content using selectors
    for (const selector of contentSelectors) {
        const element = document.querySelector(selector);
        if (element && element.textContent.trim().length > 500) {
            mainContent = element;
            break;
        }
    }
    
    // Fallback: find largest text container
    if (!mainContent) {
        const textElements = Array.from(document.querySelectorAll('div, section, article'))
            .filter(el => {
                const text = el.textContent.trim();
                return text.length > 500 && !isUnwantedElement(el);
            })
            .sort((a, b) => b.textContent.length - a.textContent.length);
        
        mainContent = textElements[0];
    }
    
    if (!mainContent) return null;
    
    // Extract and clean content
    const cleanedContent = cleanContent(mainContent.cloneNode(true));
    
    // Extract metadata
    const metadata = extractMetadata();
    
    return {
        content: cleanedContent,
        metadata: metadata
    };
}

function cleanContent(contentElement) {
    // Remove unwanted elements
    const unwantedSelectors = [
        // Ads
        '.ad', '.ads', '.advertisement', '.adsystem', '.adsbygoogle', '.ad-container',
        '[class*="ad-"]', '[id*="ad-"]', '[class*="ads-"]', '[id*="ads-"]',
        '.dfp-ad', '.google-ads', '.amazon-ad', '.sponsored', '.promotion',
        
        // Navigation and UI
        'nav', '.navigation', '.nav', '.menu', '.sidebar', '.aside',
        '.header', '.footer', '.comments', '.comment', '.social-share',
        '.newsletter', '.subscription', '.popup', '.modal', '.overlay',
        
        // Tracking and analytics
        'script', 'noscript', '.analytics', '.tracking',
        
        // Related and recommended
        '.related', '.recommended', '.more-stories', '.trending',
        '.popular', '.most-read', '.you-might-like',
        
        // Social and sharing
        '.share', '.sharing', '.social', '.follow', '.subscribe',
        
        // Generic unwanted
        '.promo', '.banner', '.widget', '.plugin', '.embed:not(iframe)',
        '.alert', '.notice', '.warning'
    ];
    
    unwantedSelectors.forEach(selector => {
        contentElement.querySelectorAll(selector).forEach(el => el.remove());
    });
    
    // Clean attributes that might interfere
    contentElement.querySelectorAll('*').forEach(el => {
        // Remove problematic attributes
        ['onclick', 'onmouseover', 'onmouseout', 'style', 'class', 'id'].forEach(attr => {
            if (attr !== 'src' && attr !== 'href' && attr !== 'alt' && attr !== 'title') {
                el.removeAttribute(attr);
            }
        });
        
        // Keep only essential elements
        if (!isEssentialElement(el)) {
            // Check if element has meaningful content
            const textContent = el.textContent.trim();
            if (textContent.length < 20 && !el.querySelector('img, video, iframe')) {
                el.remove();
            }
        }
    });
    
    return contentElement;
}

function isEssentialElement(element) {
    const essentialTags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'img', 'video', 'iframe', 'blockquote', 'ul', 'ol', 'li', 'strong', 'em', 'a', 'br'];
    return essentialTags.includes(element.tagName.toLowerCase());
}

function isUnwantedElement(element) {
    const unwantedClasses = ['ad', 'advertisement', 'sidebar', 'header', 'footer', 'nav', 'menu', 'comments'];
    const classList = element.className.toLowerCase();
    return unwantedClasses.some(cls => classList.includes(cls));
}

function extractMetadata() {
    const metadata = {};
    
    // Title
    metadata.title = document.querySelector('h1')?.textContent?.trim() ||
                    document.querySelector('[property="og:title"]')?.content ||
                    document.title;
    
    // Author
    metadata.author = document.querySelector('[name="author"]')?.content ||
                     document.querySelector('[property="article:author"]')?.content ||
                     document.querySelector('.author')?.textContent?.trim() ||
                     document.querySelector('.byline')?.textContent?.trim();
    
    // Date
    const dateElement = document.querySelector('time') ||
                       document.querySelector('[property="article:published_time"]') ||
                       document.querySelector('.date') ||
                       document.querySelector('.published');
    
    metadata.date = dateElement?.getAttribute('datetime') ||
                   dateElement?.textContent?.trim();
    
    // Description
    metadata.description = document.querySelector('[name="description"]')?.content ||
                          document.querySelector('[property="og:description"]')?.content;
    
    // Image
    metadata.image = document.querySelector('[property="og:image"]')?.content ||
                    document.querySelector('meta[name="twitter:image"]')?.content;
    
    return metadata;
}

function applyReaderMode(cleanContent) {
    // Create reader mode HTML
    const readerHTML = `
        <div id="reader-mode-container" style="
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #ffffff;
            min-height: 100vh;
            font-family: 'Inter', 'Georgia', serif;
            line-height: 1.8;
            color: #1a1a1a;
        ">
            <!-- Reader Mode Header -->
            <div style="text-align: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid #e5e7eb;">
                <button id="exit-reader-mode" style="
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: rgba(0, 0, 0, 0.8);
                    color: white;
                    border: none;
                    border-radius: 50px;
                    padding: 12px 20px;
                    cursor: pointer;
                    font-size: 13px;
                    font-weight: 600;
                    z-index: 10000;
                    backdrop-filter: blur(10px);
                    transition: all 0.2s ease;
                ">
                    ✕ Έξοδος από Καθαρή Προβολή
                </button>
                
                ${cleanContent.metadata.title ? `
                    <h1 style="
                        font-size: 2.5rem;
                        font-weight: 700;
                        margin: 0 0 20px 0;
                        line-height: 1.2;
                        color: #1a1a1a;
                    ">${cleanContent.metadata.title}</h1>
                ` : ''}
                
                <div style="
                    display: flex;
                    justify-content: center;
                    gap: 20px;
                    flex-wrap: wrap;
                    font-size: 14px;
                    color: #6b7280;
                ">
                    ${cleanContent.metadata.author ? `
                        <span>📝 ${cleanContent.metadata.author}</span>
                    ` : ''}
                    ${cleanContent.metadata.date ? `
                        <span>📅 ${cleanContent.metadata.date}</span>
                    ` : ''}
                    <span>📖 News Copilot Reader</span>
                </div>
            </div>
            
            <!-- Article Content -->
            <div id="reader-content" style="
                font-size: 18px;
                line-height: 1.8;
                color: #2d3748;
            ">
                ${cleanContent.content.innerHTML}
            </div>
            
            <!-- Reader Mode Footer -->
            <div style="
                margin-top: 60px;
                padding-top: 30px;
                border-top: 1px solid #e5e7eb;
                text-align: center;
                color: #6b7280;
                font-size: 14px;
            ">
                <p>📖 Καθαρή προβολή από News Copilot</p>
                <button onclick="window.intelligenceSidebar?.classList.add('open'); document.body.style.marginRight = '420px';" style="
                    background: #667eea;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    cursor: pointer;
                    font-size: 13px;
                    margin-top: 10px;
                ">
                    🚀 Ανάλυση Άρθρου
                </button>
            </div>
        </div>
    `;
    
    // Apply reader mode styles to body
    document.body.innerHTML = readerHTML;
    document.body.style.cssText = `
        margin: 0;
        padding: 0;
        background: linear-gradient(to bottom, #f9fafb, #ffffff);
        font-family: 'Inter', 'Georgia', serif;
        overflow-x: hidden;
    `;
    
    // Style improvements for content elements
    styleReaderContent();
    
    // Add exit functionality
    document.getElementById('exit-reader-mode').addEventListener('click', exitReaderMode);
    
    // Add hover effect to exit button
    const exitButton = document.getElementById('exit-reader-mode');
    exitButton.addEventListener('mouseenter', () => {
        exitButton.style.background = 'rgba(220, 38, 38, 0.9)';
        exitButton.style.transform = 'scale(1.05)';
    });
    exitButton.addEventListener('mouseleave', () => {
        exitButton.style.background = 'rgba(0, 0, 0, 0.8)';
        exitButton.style.transform = 'scale(1)';
    });
}

function styleReaderContent() {
    const content = document.getElementById('reader-content');
    if (!content) return;
    
    // Style paragraphs
    content.querySelectorAll('p').forEach(p => {
        p.style.cssText = `
            margin-bottom: 1.5rem;
            line-height: 1.8;
            font-size: 18px;
        `;
    });
    
    // Style headings
    content.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(heading => {
        heading.style.cssText = `
            margin: 2rem 0 1rem 0;
            font-weight: 700;
            line-height: 1.3;
            color: #1a1a1a;
        `;
        
        if (heading.tagName === 'H2') heading.style.fontSize = '1.8rem';
        if (heading.tagName === 'H3') heading.style.fontSize = '1.5rem';
        if (heading.tagName === 'H4') heading.style.fontSize = '1.3rem';
    });
    
    // Style images
    content.querySelectorAll('img').forEach(img => {
        img.style.cssText = `
            max-width: 100%;
            height: auto;
            margin: 2rem auto;
            display: block;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        `;
    });
    
    // Style blockquotes
    content.querySelectorAll('blockquote').forEach(quote => {
        quote.style.cssText = `
            margin: 2rem 0;
            padding: 1rem 2rem;
            border-left: 4px solid #667eea;
            background: #f8fafc;
            font-style: italic;
            border-radius: 0 8px 8px 0;
        `;
    });
    
    // Style links
    content.querySelectorAll('a').forEach(link => {
        link.style.cssText = `
            color: #667eea;
            text-decoration: underline;
            transition: color 0.2s ease;
        `;
        link.addEventListener('mouseenter', () => link.style.color = '#4f46e5');
        link.addEventListener('mouseleave', () => link.style.color = '#667eea');
    });
    
    // Style lists
    content.querySelectorAll('ul, ol').forEach(list => {
        list.style.cssText = `
            margin: 1.5rem 0;
            padding-left: 2rem;
        `;
    });
    
    content.querySelectorAll('li').forEach(item => {
        item.style.cssText = `
            margin-bottom: 0.5rem;
            line-height: 1.7;
        `;
    });
}

function updateReaderModeButton(isActive) {
    const button = document.getElementById('reader-mode-toggle');
    if (!button) return;
    
    if (isActive) {
        button.innerHTML = `
            <span style="font-size: 18px;">🌐</span>
            <span>Επιστροφή στην Κανονική Προβολή</span>
        `;
        button.style.background = 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)';
    } else {
        button.innerHTML = `
            <span style="font-size: 18px;">📖</span>
            <span>Καθαρή Προβολή - Χωρίς Διαφημίσεις</span>
        `;
        button.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
    }
}

function reinjectExtensionElements() {
    // Re-add our extension elements after exiting reader mode
    setTimeout(() => {
        // --- 1. Re-inject Styles ---
        let styleTagInHead = document.head.querySelector('style[data-news-copilot="true"]');
        if (!styleTagInHead) {
            styleTagInHead = document.createElement("style");
            styleTagInHead.type = "text/css";
            styleTagInHead.setAttribute('data-news-copilot', 'true');
            // 'styles' and 'additionalStyles' are global constants with the CSS strings
            styleTagInHead.innerText = styles + additionalStyles; 
            document.head.appendChild(styleTagInHead);
        }

        // --- 2. Re-inject Floating Buttons & Their Listeners ---
        let currentAugmentButton = document.getElementById('augment-article-button');
        if (!currentAugmentButton) {
            document.body.appendChild(augmentButton); 
            currentAugmentButton = augmentButton; 
        }
        if (!currentAugmentButton.hasAttribute('data-listener-attached')) {
            currentAugmentButton.addEventListener("click", () => { 
                // Main click handler for augmentButton (Copied from original code)
                console.log("Κλικ στο κουμπί ανάλυσης άρθρου.");
                currentAugmentButton.querySelector("span").textContent = "Αναλύεται...";
                currentAugmentButton.classList.add('processing');
                currentAugmentButton.disabled = true;
                updateStatusDisplay("Σύνδεση με την υπηρεσία AI...");
                const articleUrl = window.location.href;
                window.currentArticleUrl = articleUrl;
                chrome.runtime.sendMessage({ type: "AUGMENT_ARTICLE", url: articleUrl }, (response) => {
                    currentAugmentButton.querySelector("span").textContent = "Ανάλυση Άρθρου";
                    currentAugmentButton.classList.remove('processing');
                    currentAugmentButton.disabled = false;
                    updateStatusDisplay(null);
                    if (chrome.runtime.lastError) {
                        console.error("Σφάλμα αποστολής μηνύματος:", chrome.runtime.lastError.message);
                        updateStatusDisplay(`Σφάλμα: ${chrome.runtime.lastError.message}`);
                        const contentPanel = createIntelligenceSidebar(); 
                        const errorState = document.createElement('div');
                        errorState.className = 'empty-state';
                        errorState.innerHTML = `<h3>Σφάλμα επικοινωνίας</h3><p>Δεν ήταν δυνατή η σύνδεση.</p>`;
                        contentPanel.appendChild(errorState);
                        if(intelligenceSidebar) intelligenceSidebar.classList.add('open');
                        if (window.innerWidth > 768 && intelligenceSidebar) document.body.style.marginRight = originalPageState.bodyMarginRight ||'420px';
                        return;
                    }
                    const contentPanel = createIntelligenceSidebar(); 
                    if (response && response.success) {
                        updateStatusDisplay("Επεξεργασία insights...");
                        currentData = response; // Update currentData
                        renderOverview(response.jargon, response.viewpoints, contentPanel);
                        renderTerms(response.jargon, response.jargon_citations, contentPanel);
                        renderViewpoints(response.viewpoints, response.viewpoints_citations, contentPanel);
                        if(intelligenceSidebar) intelligenceSidebar.classList.add('open');
                        if (window.innerWidth > 768 && intelligenceSidebar) document.body.style.marginRight = originalPageState.bodyMarginRight ||'420px';
                        updateStatusDisplay(null);
                    } else {
                        const errorMsg = response ? response.error : "Άγνωστο σφάλμα";
                        updateStatusDisplay(`Αποτυχία: ${errorMsg}`);
                        const errorState = document.createElement('div');
                        errorState.className = 'empty-state';
                        errorState.innerHTML = `<h3>Αποτυχία ανάλυσης</h3><p>${errorMsg}</p>`;
                        contentPanel.appendChild(errorState);
                        if(intelligenceSidebar) intelligenceSidebar.classList.add('open');
                        if (window.innerWidth > 768 && intelligenceSidebar) document.body.style.marginRight = originalPageState.bodyMarginRight ||'420px';
                    }
                });
            });
            currentAugmentButton.setAttribute('data-listener-attached', 'true');
        }
        currentAugmentButton.style.display = 'flex'; // Ensure visible

        let currentCleanButton = document.getElementById('clean-website-button');
        if (!currentCleanButton) {
            document.body.appendChild(cleanWebsiteButton); 
            currentCleanButton = cleanWebsiteButton; 
        }
        if (!currentCleanButton.hasAttribute('data-listener-attached')) {
             currentCleanButton.addEventListener('click', () => {
                toggleReaderMode();
            });
            currentCleanButton.setAttribute('data-listener-attached', 'true');
        }
        currentCleanButton.style.display = 'flex'; // Ensure visible

        // --- 3. Restore Intelligence Sidebar ---
        let restoredSidebar = document.querySelector('.news-intelligence-sidebar');
        if (originalPageState.sidebarOpen) {
            if (!restoredSidebar) {
                // If not found, create it (createIntelligenceSidebar appends to body and reassigns global intelligenceSidebar)
                createIntelligenceSidebar(); 
                // window.intelligenceSidebar is now the new sidebar
            } else {
                 window.intelligenceSidebar = restoredSidebar; // Point global var to the found one
            }

            // At this point, window.intelligenceSidebar should be the correct DOM element (either found or newly created)
            if (window.intelligenceSidebar) {
                window.intelligenceSidebar.style.display = ''; // Make sure it's not display:none
                window.intelligenceSidebar.classList.add('open');
                document.body.style.marginRight = originalPageState.bodyMarginRight || (window.innerWidth > 768 ? '420px' : '0px');
                
                const closeButton = window.intelligenceSidebar.querySelector('.sidebar-close');
                if (closeButton && !closeButton.hasAttribute('data-listener-attached')) {
                    closeButton.onclick = () => {
                        window.intelligenceSidebar.classList.remove('open'); // Use global var
                        setTimeout(() => {
                            if (window.intelligenceSidebar && !window.intelligenceSidebar.classList.contains('open')) {
                                document.body.style.marginRight = '0';
                            }
                        }, 400);
                    };
                    closeButton.setAttribute('data-listener-attached', 'true');
                }

                // Re-render sidebar content
                const contentPanel = window.intelligenceSidebar.querySelector('.sidebar-content');
                if (contentPanel) {
                    contentPanel.innerHTML = ''; // Clear previous content
                    if (currentData) { // currentData should be available globally
                        renderOverview(currentData.jargon, currentData.viewpoints, contentPanel);
                        renderTerms(currentData.jargon, currentData.jargon_citations, contentPanel);
                        renderViewpoints(currentData.viewpoints, currentData.viewpoints_citations, contentPanel);
                    } else {
                        // Handle case where currentData is null (e.g. show empty state or error)
                         const emptyState = document.createElement('div');
                         emptyState.className = 'empty-state';
                         emptyState.innerHTML = `<p>Δεδομένα ανάλυσης μη διαθέσιμα για την επαναφορά της πλευρικής στήλης.</p>`;
                         contentPanel.appendChild(emptyState);
                    }
                }
            }
        } else if (restoredSidebar) { // Sidebar was not open, but exists in DOM
             window.intelligenceSidebar = restoredSidebar; // Ensure global var is set
             restoredSidebar.style.display = ''; // Ensure visible if it was hidden
             restoredSidebar.classList.remove('open'); // Ensure it's closed
        } else {
            // Sidebar was not open and not in DOM, optionally recreate it in a hidden state
            // createIntelligenceSidebar(); // Creates and appends, global intelligenceSidebar is set
            // if (window.intelligenceSidebar) window.intelligenceSidebar.style.display = 'none'; // Keep it hidden
        }


        // --- 4. Restore Status Display ---
        if (originalPageState.statusDisplayHTML && originalPageState.statusDisplayStyle) {
            let restoredStatusDisplay = document.querySelector('.intelligence-status');
            if (!restoredStatusDisplay) {
                window.statusDisplay = document.createElement('div'); // Assign to global
                window.statusDisplay.className = 'intelligence-status';
                document.body.appendChild(window.statusDisplay);
            } else {
                window.statusDisplay = restoredStatusDisplay; // Assign found element to global
            }
            window.statusDisplay.innerHTML = originalPageState.statusDisplayHTML;
            window.statusDisplay.style.display = originalPageState.statusDisplayStyle;
        } else if (window.statusDisplay) { // if global var exists but wasn't saved (was hidden)
            window.statusDisplay.style.display = 'none';
        }
        
        // Call handleResize to ensure correct body margin if sidebar is open on mobile/desktop
        handleResize();

    }, 100);
}

function showReaderModeNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 12px 24px;
        border-radius: 50px;
        font-size: 14px;
        font-weight: 500;
        z-index: 10001;
        backdrop-filter: blur(10px);
        animation: slideDown 0.3s ease-out;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideUp 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

function showReaderModeError(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        bottom: 120px;
        right: 30px;
        background: #fee2e2;
        border: 1px solid #fecaca;
        color: #991b1b;
        padding: 12px 20px;
        border-radius: 8px;
        font-size: 13px;
        animation: slideUp 0.3s ease-out;
        z-index: 10001;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideDown 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Helper function to convert X/Twitter mentions to direct links
function linkifyXPosts(text) {
    if (!text || typeof text !== 'string') return text;
    
    // Patterns for different X post formats
    const patterns = [
        // Direct X.com URLs
        {
            regex: /(https?:\/\/)?(www\.)?(x\.com|twitter\.com)\/[a-zA-Z0-9_]+\/status\/([0-9]+)(\?[^\s]*)?/gi,
            replacement: (match, protocol, www, domain, tweetId, params) => {
                const url = `https://x.com/i/status/${tweetId}`;
                return `<a href="${url}" target="_blank" style="color: #1d9bf0; text-decoration: none; font-weight: 500; background: #f0f9ff; padding: 2px 6px; border-radius: 4px; border: 1px solid #bfdbfe;">
                    🐦 Δείτε το X post
                </a>`;
            }
        },
        // Tweet mentions like "@username said on X/Twitter"
        {
            regex: /@([a-zA-Z0-9_]+)\s+(said|posted|tweeted|wrote|commented|responded|stated)\s+(on\s+)?(X|Twitter|x\.com|twitter\.com)/gi,
            replacement: (match, username, verb, on, platform) => {
                const url = `https://x.com/${username}`;
                return `<a href="${url}" target="_blank" style="color: #1d9bf0; text-decoration: none; font-weight: 500; background: #f0f9ff; padding: 2px 6px; border-radius: 4px; border: 1px solid #bfdbfe;">
                    @${username} ${verb} στο X
                </a>`;
            }
        },
        // Greek Twitter/X mentions 
        {
            regex: /@([a-zA-Z0-9_]+)\s+(είπε|ανέφερε|έγραψε|σχολίασε|απάντησε|δήλωσε)\s+(στο\s+)?(X|Twitter|x\.com|twitter\.com)/gi,
            replacement: (match, username, verb, sto, platform) => {
                const url = `https://x.com/${username}`;
                return `<a href="${url}" target="_blank" style="color: #1d9bf0; text-decoration: none; font-weight: 500; background: #f0f9ff; padding: 2px 6px; border-radius: 4px; border: 1px solid #bfdbfe;">
                    @${username} ${verb} στο X
                </a>`;
            }
        },
        // Post ID mentions like "X post 1234567890"
        {
            regex: /(X|Twitter)\s+(post|tweet|δημοσίευση|tweet)\s+([0-9]{10,})/gi,
            replacement: (match, platform, postType, id) => {
                const url = `https://x.com/i/status/${id}`;
                return `<a href="${url}" target="_blank" style="color: #1d9bf0; text-decoration: none; font-weight: 500; background: #f0f9ff; padding: 2px 6px; border-radius: 4px; border: 1px solid #bfdbfe;">
                    🐦 X δημοσίευση ${id}
                </a>`;
            }
        },
        // Username-only mentions with context (be more conservative)
        {
            regex: /\s(@[a-zA-Z0-9_]+)(?=\s|$|[.,;!?])/g,
            replacement: (match, username) => {
                // Only convert if it's in a context that suggests it's a Twitter mention
                const url = `https://x.com/${username.substring(1)}`;
                return ` <a href="${url}" target="_blank" style="color: #1d9bf0; text-decoration: none; font-weight: 500;">
                    ${username}
                </a>`;
            }
        }
    ];
    
    let processedText = text;
    patterns.forEach(pattern => {
        if (pattern.replacement) {
            processedText = processedText.replace(pattern.regex, pattern.replacement);
        }
    });
    
    return processedText;
}

// Helper function to extract and enhance X URLs from source URLs
function enhanceXSourceUrl(sourceUrl) {
    if (!sourceUrl || typeof sourceUrl !== 'string') return sourceUrl;
    
    // Check if it's an X/Twitter URL
    const xUrlPattern = /(https?:\/\/)?(www\.)?(x\.com|twitter\.com)\/([a-zA-Z0-9_]+)(?:\/status\/([0-9]+))?/i;
    const match = sourceUrl.match(xUrlPattern);
    
    if (match) {
        const [, protocol, www, domain, username, tweetId] = match;
        if (tweetId) {
            // It's a specific tweet
            return {
                url: `https://x.com/${username}/status/${tweetId}`,
                display: `X post από @${username}`,
                isXPost: true,
                username: username,
                tweetId: tweetId
            };
        } else {
            // It's a profile
            return {
                url: `https://x.com/${username}`,
                display: `Προφίλ X: @${username}`,
                isXPost: false,
                username: username
            };
        }
    }
    
    return {
        url: sourceUrl,
        display: 'Δείτε την πηγή',
        isXPost: false
    };
}

console.log("🚀 News Copilot - Ελληνική έκδοση αρχικοποιήθηκε επιτυχώς!"); 