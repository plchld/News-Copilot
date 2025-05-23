// modules/api/communication.js
// API Communication Module

export function sendAugmentRequest(articleUrl, callback) {
    chrome.runtime.sendMessage({ 
        type: "AUGMENT_ARTICLE", 
        url: articleUrl 
    }, (response) => {
        if (chrome.runtime.lastError) {
            console.error("Σφάλμα αποστολής μηνύματος:", chrome.runtime.lastError.message);
            callback({
                success: false,
                error: chrome.runtime.lastError.message
            });
            return;
        }
        
        callback(response || { success: false, error: "No response received" });
    });
}

export function sendDeepAnalysisRequest(analysisType, articleUrl, searchParams, callback) {
    console.log('Sending deep analysis request:', analysisType, articleUrl, searchParams);
    
    chrome.runtime.sendMessage({ 
        type: "DEEP_ANALYSIS",
        url: articleUrl,
        analysisType: analysisType,
        searchParams: searchParams
    }, (response) => {
        console.log('Deep analysis response for', analysisType, ':', response);
        
        if (chrome.runtime.lastError) {
            console.error('Chrome runtime error:', chrome.runtime.lastError);
            callback({
                success: false,
                error: 'Σφάλμα επικοινωνίας με την υπηρεσία'
            });
            return;
        }
        
        callback(response || { success: false, error: "No response received" });
    });
}

export function createSearchParams(analysisType) {
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
            searchParams.max_results = 10; // Limit results for quality
            break;
        default:
            searchParams.sources = [
                { type: "web" },
                { type: "x" },
                { type: "news" }
            ];
    }
    
    return searchParams;
}