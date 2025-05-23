// modules/ui/sidebar.js
// Intelligent Sidebar Component

export let intelligenceSidebar = null;

export function createIntelligenceSidebar() {
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
        closeSidebar();
    };

    document.body.appendChild(intelligenceSidebar);
    return content;
}

export function openSidebar() {
    if (intelligenceSidebar) {
        intelligenceSidebar.classList.add('open');
        document.body.style.marginRight = '420px';
        
        // Responsive handling
        if (window.innerWidth <= 768) {
            document.body.style.marginRight = '0';
        }
    }
}

export function closeSidebar() {
    if (intelligenceSidebar) {
        intelligenceSidebar.classList.remove('open');
        setTimeout(() => {
            if (intelligenceSidebar && !intelligenceSidebar.classList.contains('open')) {
                document.body.style.marginRight = '0';
            }
        }, 400);
    }
}

export function createInsightsOverview(data) {
    const overview = document.createElement('div');
    overview.className = 'insights-overview';
    
    const termsCount = data.terms ? data.terms.length : 0;
    const viewpointsCount = data.viewpoints ? data.viewpoints.split('•').length - 1 : 0;
    
    overview.innerHTML = `
        <h3 style="margin: 0 0 16px 0; font-size: 16px; font-weight: 600; color: #1e293b;">
            📊 Επισκόπηση Ανάλυσης
        </h3>
        <div class="overview-stats">
            <div class="stat-item">
                <div class="stat-number">${termsCount}</div>
                <div class="stat-label">Όροι</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">${viewpointsCount}</div>
                <div class="stat-label">Οπτικές</div>
            </div>
        </div>
    `;
    
    return overview;
}

export function createSectionHeader(icon, title) {
    const header = document.createElement('div');
    header.className = 'section-header';
    header.innerHTML = `
        <div class="section-icon">${icon}</div>
        <h2 class="section-title">${title}</h2>
    `;
    return header;
}

export function createIntelligenceSection(content) {
    const section = document.createElement('div');
    section.className = 'intelligence-section';
    section.appendChild(content);
    return section;
}