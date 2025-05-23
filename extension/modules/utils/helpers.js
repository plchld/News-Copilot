// modules/utils/helpers.js
// Helper Functions and Utilities

// Enhanced Text Formatting
export function formatGreekText(text) {
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

// Enhanced Viewpoint Categorization
export function categorizeViewpoint(text) {
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

// X/Twitter Post Linking
export function linkifyXPosts(text) {
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

// Parse X post URLs and extract information
export function parseXPostUrl(sourceUrl) {
    const xPostPattern = /(https?:\/\/)?(www\.)?(x\.com|twitter\.com)\/([a-zA-Z0-9_]+)\/status\/([0-9]+)/;
    const match = sourceUrl.match(xPostPattern);
    
    if (match) {
        const [, protocol, www, domain, username, tweetId] = match;
        if (tweetId) {
            return {
                url: `https://x.com/${username}/status/${tweetId}`,
                display: `X post από @${username}`,
                isXPost: true,
                username: username,
                tweetId: tweetId
            };
        } else {
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

// Calculate expert opinion reliability
export function calculateExpertReliability(expert) {
    let score = 0.5; // Base score
    
    if (expert.credentials) {
        const credentials = expert.credentials.toLowerCase();
        if (credentials.includes('καθηγητής') || credentials.includes('professor')) score += 0.3;
        if (credentials.includes('δρ.') || credentials.includes('dr.')) score += 0.2;
        if (credentials.includes('ερευνητής') || credentials.includes('researcher')) score += 0.2;
        if (credentials.includes('πρώην') || credentials.includes('former')) score += 0.1;
    }
    
    if (expert.source === 'news') score += 0.2;
    if (expert.source_url && expert.source_url.length > 0) score += 0.1;
    
    return Math.min(score, 1.0);
}

// Article Text Detection
export function findArticleElement() {
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
    
    return articleElement;
}

// Create citation links with favicon support
export function createCitationLink(citation) {
    const link = document.createElement('a');
    link.className = 'citation-link';
    link.href = citation.url;
    link.target = '_blank';
    
    const favicon = document.createElement('div');
    favicon.className = 'citation-favicon';
    
    // Try to get favicon
    try {
        const url = new URL(citation.url);
        favicon.style.backgroundImage = `url(https://www.google.com/s2/favicons?domain=${url.hostname})`;
        favicon.style.backgroundSize = 'contain';
    } catch (e) {
        // Fallback to generic icon
    }
    
    const domain = document.createElement('span');
    domain.className = 'citation-domain';
    try {
        const url = new URL(citation.url);
        domain.textContent = url.hostname.replace('www.', '');
    } catch (e) {
        domain.textContent = 'Εξωτερική πηγή';
    }
    
    link.appendChild(favicon);
    link.appendChild(domain);
    
    return link;
}

// Debounce function for performance
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Smooth scroll to element
export function smoothScrollTo(element, options = {}) {
    const defaultOptions = {
        behavior: 'smooth',
        block: 'center',
        inline: 'nearest'
    };
    
    try {
        element.scrollIntoView({ ...defaultOptions, ...options });
    } catch (error) {
        console.error('Error scrolling to element:', error);
    }
}