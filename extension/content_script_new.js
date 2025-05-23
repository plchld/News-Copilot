// content_script.js
// Main Entry Point for News Copilot Extension

import { applyStyles } from './modules/styles/styles.js';
import { createAugmentButton, updateButtonState } from './modules/ui/button.js';
import { 
    createIntelligenceSidebar, 
    openSidebar, 
    closeSidebar,
    createInsightsOverview,
    createSectionHeader,
    createIntelligenceSection
} from './modules/ui/sidebar.js';
import { 
    showStatus, 
    updateStatus, 
    removeStatus, 
    showSuccessStatus, 
    showErrorStatus 
} from './modules/ui/status-display.js';
import { 
    sendAugmentRequest, 
    sendDeepAnalysisRequest, 
    createSearchParams 
} from './modules/api/communication.js';
import { 
    formatGreekText, 
    categorizeViewpoint, 
    findArticleElement,
    smoothScrollTo
} from './modules/utils/helpers.js';

console.log("News Copilot - Ελληνική έκδοση φορτώθηκε.");

// --- Global State ---
let highlightedTerms = [];
let currentData = null;

// --- Initialize Extension ---
function initializeExtension() {
    // Apply styles
    applyStyles();
    
    // Create floating button
    const augmentButton = createAugmentButton();
    
    // Add main click handler
    augmentButton.addEventListener("click", handleAugmentClick);
    
    // Setup keyboard shortcuts
    setupKeyboardShortcuts();
}

// --- Main Analysis Handler ---
function handleAugmentClick() {
    console.log("Κλικ στο κουμπί ανάλυσης άρθρου.");
    
    const augmentButton = document.getElementById("augment-article-button");
    updateButtonState(augmentButton, 'processing');
    showStatus("Σύνδεση με την υπηρεσία AI...");

    const articleUrl = window.location.href;
    window.currentArticleUrl = articleUrl;

    sendAugmentRequest(articleUrl, (response) => {
        updateButtonState(augmentButton, response.success ? 'complete' : 'error');
        removeStatus();

        if (response.success) {
            currentData = response.data;
            displayResults(response.data);
            showSuccessStatus("Ανάλυση ολοκληρώθηκε!");
        } else {
            console.error("Ανάλυση απέτυχε:", response.error);
            showErrorStatus(`Σφάλμα: ${response.error}`);
        }
    });
}

// --- Results Display ---
function displayResults(data) {
    const contentPanel = createIntelligenceSidebar();
    
    // Add insights overview
    const overview = createInsightsOverview(data);
    contentPanel.appendChild(overview);
    
    // Add sections based on available data
    if (data.jargon && data.jargon.terms) {
        const termsSection = createTermsSection(data.jargon);
        contentPanel.appendChild(termsSection);
    }
    
    if (data.viewpoints) {
        const viewpointsSection = createViewpointsSection(data.viewpoints);
        contentPanel.appendChild(viewpointsSection);
    }
    
    // Open sidebar
    openSidebar();
}

// --- Create Sections ---
function createTermsSection(jargonData) {
    const section = createIntelligenceSection();
    
    const header = createSectionHeader(
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#667eea" stroke-width="2"><path d="M12 2L2 7L12 12L22 7L12 2Z"/></svg>',
        '📚 Επεξήγηση Όρων'
    );
    section.appendChild(header);
    
    if (jargonData.terms && jargonData.terms.length > 0) {
        jargonData.terms.forEach(term => {
            const termCard = createTermCard(term);
            section.appendChild(termCard);
        });
    }
    
    return section;
}

function createViewpointsSection(viewpointsData) {
    const section = createIntelligenceSection();
    
    const header = createSectionHeader(
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8b5cf6" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
        '🔍 Εναλλακτικές Οπτικές'
    );
    section.appendChild(header);
    
    if (viewpointsData) {
        const viewpointCard = createViewpointCard(viewpointsData);
        section.appendChild(viewpointCard);
    }
    
    return section;
}

// --- Helper Functions ---
function createTermCard(term) {
    const card = document.createElement('div');
    card.className = 'term-card';
    
    card.innerHTML = `
        <div class="term-title">${term.term}</div>
        <div class="term-explanation">${formatGreekText(term.explanation)}</div>
    `;
    
    return card;
}

function createViewpointCard(viewpointsData) {
    const category = categorizeViewpoint(viewpointsData);
    
    const card = document.createElement('div');
    card.className = 'viewpoint-card';
    
    card.innerHTML = `
        <div class="viewpoint-type" style="color: ${category.color};">
            ${category.type}
        </div>
        <div class="viewpoint-content">${formatGreekText(viewpointsData)}</div>
    `;
    
    return card;
}

// --- Keyboard Shortcuts ---
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
            e.preventDefault();
            const sidebar = document.querySelector('.news-intelligence-sidebar');
            if (sidebar && sidebar.classList.contains('open')) {
                closeSidebar();
            } else if (sidebar) {
                openSidebar();
            } else {
                document.getElementById("augment-article-button").click();
            }
        }
        
        if (e.key === 'Escape') {
            const sidebar = document.querySelector('.news-intelligence-sidebar');
            if (sidebar && sidebar.classList.contains('open')) {
                closeSidebar();
            }
        }
    });
}

// --- Initialize when DOM is ready ---
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeExtension);
} else {
    initializeExtension();
}