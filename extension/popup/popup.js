document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const analyzeBtn = document.getElementById('analyzeBtn');
    const historyBtn = document.getElementById('historyBtn');
    const resultContainer = document.getElementById('result');
    const resultContent = document.getElementById('resultContent');
    const historyContainer = document.getElementById('history');
    const historyContent = document.getElementById('historyContent');
    
    // Initial state - hide containers
    resultContainer.style.display = 'none';
    historyContainer.style.display = 'none';
    
    // Analyze button event
    analyzeBtn.addEventListener('click', analyzeSelectedText);
    
    // History button event
    historyBtn.addEventListener('click', toggleHistory);
    
    // Function to analyze selected text
    function analyzeSelectedText() {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, { action: "getSelectedText" }, (response) => {
                if (response && response.text) {
                    // Show loading state
                    resultContainer.style.display = 'block';
                    historyContainer.style.display = 'none';
                    resultContent.innerHTML = `
                        <div style="text-align:center; padding:20px;">
                            <div class="loading"></div>
                            <p>Analyzing selected text...</p>
                        </div>
                    `;
                    
                    // Send to API for analysis
                    analyzeText(response.text);
                } else {
                    // No text selected
                    resultContainer.style.display = 'block';
                    historyContainer.style.display = 'none';
                    resultContent.innerHTML = `
                        <div class="fade-in" style="text-align:center; padding:20px; color:#c62828;">
                            <p><strong>No text selected!</strong></p>
                            <p>Please select some text on the page before analyzing.</p>
                        </div>
                    `;
                }
            });
        });
    }
    
    // Function to analyze text with API
    function analyzeText(text) {
        // In a real implementation, this would call your API
        // For demo, we'll simulate API response
        setTimeout(() => {
            // Mock API response
            const mockResponse = {
                result: {
                    roberta_result: {
                        label: Math.random() > 0.5 ? "CG" : "Human",
                        confidence: Math.random()
                    },
                    ai_detector_result: {
                        label: Math.random() > 0.5 ? "AI" : "Human",
                        confidence: Math.random()
                    },
                    final_label: Math.random() > 0.7 ? "Human" : "CG"
                }
            };
            
            // Display results
            displayResult(mockResponse);
            
            // Add to history
            addToHistory(text, mockResponse);
        }, 1500);
    }
    
    // Function to display results
    function displayResult(data) {
        const finalLabel = data.result.final_label === "CG" || data.result.final_label === "AI" 
            ? '<span class="label ai-label">AI-generated</span>' 
            : '<span class="label human-label">Human-written</span>';
        
        const robertaLabel = data.result.roberta_result.label === "CG" || data.result.roberta_result.label === "AI" 
            ? '<span class="label ai-label">AI-generated</span>' 
            : '<span class="label human-label">Human-written</span>';
        
        const aiLabel = data.result.ai_detector_result.label === "CG" || data.result.ai_detector_result.label === "AI" 
            ? '<span class="label ai-label">AI-generated</span>' 
            : '<span class="label human-label">Human-written</span>';
        
        const robertaPercentage = Math.round(data.result.roberta_result.confidence * 100);
        const aiPercentage = Math.round(data.result.ai_detector_result.confidence * 100);
        
        resultContent.innerHTML = `
            <div class="fade-in">
                <p><strong>Final Assessment:</strong> ${finalLabel}</p>
                <div style="margin: 20px 0; padding: 15px; background: #f1f8ff; border-radius: 10px;">
                    <p><strong>RoBERTa Model Analysis</strong></p>
                    <p>Result: ${robertaLabel}</p>
                    <p>Confidence: ${robertaPercentage}%</p>
                    <div class="confidence-bar">
                        <div class="confidence-fill roberta" style="width: ${robertaPercentage}%"></div>
                    </div>
                </div>
                
                <div style="margin: 20px 0; padding: 15px; background: #fff8f1; border-radius: 10px;">
                    <p><strong>AI Detector Analysis</strong></p>
                    <p>Result: ${aiLabel}</p>
                    <p>Confidence: ${aiPercentage}%</p>
                    <div class="confidence-bar">
                        <div class="confidence-fill ai" style="width: ${aiPercentage}%"></div>
                    </div>
                </div>
                
                <div style="margin-top: 20px; padding: 10px; background: #e8f5e9; border-radius: 8px; text-align: center;">
                    <p><strong>Tip:</strong> ${finalLabel.includes('AI') ? 
                        'This text has a high probability of being AI-generated' : 
                        'This text appears to be human-written'}</p>
                </div>
            </div>
        `;
    }
    
    // Function to add to history
    function addToHistory(text, data) {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item fade-in';
        
        const finalLabel = data.result.final_label === "CG" || data.result.final_label === "AI" 
            ? '<span class="label ai-label"><span class="status-dot ai-dot"></span> AI-generated</span>' 
            : '<span class="label human-label"><span class="status-dot human-dot"></span> Human-written</span>';
        
        historyItem.innerHTML = `
            <div class="history-text">"${text.length > 100 ? text.substring(0, 100) + '...' : text}"</div>
            <div class="history-result">
                <p>Assessment: ${finalLabel}</p>
                <p>Models agree: ${data.result.roberta_result.label === data.result.ai_detector_result.label ? 'Yes' : 'No'}</p>
            </div>
        `;
        
        historyContent.insertBefore(historyItem, historyContent.firstChild);
        
        // Save to storage
        chrome.storage.local.get({ history: [] }, (result) => {
            const history = result.history;
            history.unshift({
                text: text,
                result: data.result
            });
            chrome.storage.local.set({ history: history.slice(0, 10) }); // Keep only 10 items
        });
    }
    
    // Function to toggle history visibility
    function toggleHistory() {
        if (historyContainer.style.display === 'block') {
            historyContainer.style.display = 'none';
            historyBtn.textContent = 'View History';
        } else {
            historyContainer.style.display = 'block';
            resultContainer.style.display = 'none';
            historyBtn.textContent = 'Hide History';
            displayHistory();
        }
    }
    
    // Function to display history
    function displayHistory() {
        historyContent.innerHTML = '';
        
        chrome.storage.local.get({ history: [] }, (result) => {
            const history = result.history;
            
            if (history.length === 0) {
                historyContent.innerHTML = `
                    <div class="no-history">
                        <p>No analysis history yet</p>
                        <p style="margin-top:10px;">Analyze some text to see results here</p>
                    </div>
                `;
                return;
            }
            
            history.forEach((item, index) => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item fade-in';
                
                const finalLabel = item.result.final_label === "CG" || item.result.final_label === "AI" 
                    ? '<span class="label ai-label"><span class="status-dot ai-dot"></span> AI-generated</span>' 
                    : '<span class="label human-label"><span class="status-dot human-dot"></span> Human-written</span>';
                
                historyItem.innerHTML = `
                    <div class="history-text">"${item.text.length > 100 ? item.text.substring(0, 100) + '...' : item.text}"</div>
                    <div class="history-result">
                        <p>Assessment: ${finalLabel}</p>
                        <p>Models agree: ${item.result.roberta_result.label === item.result.ai_detector_result.label ? 'Yes' : 'No'}</p>
                    </div>
                `;
                
                historyContent.appendChild(historyItem);
            });
        });
    }
});