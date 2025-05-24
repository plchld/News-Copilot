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

// --- CSS Styles loaded from separate file ---
// Styles are now in css/intelligence_panel.css to avoid duplication

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

// --- Article Text Highlighting --- (REMOVED FOR CHROME STORE COMPLIANCE)
function highlightTermsInArticle(terms) {
    // Content modification removed for Chrome Store compliance
    // Terms are still available in the sidebar for reference
    return;
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
                        
                    </div>
                    <div class="term-explanation">${formatGreekText(item.explanation)}</div>
                `;
                
                section.appendChild(termCard);
            }
        });
        
        // Highlight terms in article after rendering
        // Term highlighting removed for Chrome Store compliance
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
// Additional styles moved to external CSS file

// Additional styles moved to CSS file

// --- Reader Mode Implementation ---
let isReaderModeActive = false;
let originalPageState = null;

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