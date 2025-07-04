document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const analyzeBtn = document.getElementById("analyzeBtn");
  const historyBtn = document.getElementById("historyBtn");
  const resultContainer = document.getElementById("result");
  const resultContent = document.getElementById("resultContent");
  const historyContainer = document.getElementById("history");
  const historyContent = document.getElementById("historyContent");
  const toggleExplanationBtn = document.getElementById("toggleExplanation");
  const explanationSection = document.getElementById("explanationSection");

  // Initial state - hide containers
  resultContainer.style.display = "none";
  historyContainer.style.display = "none";
  explanationSection.style.display = "none";

  // Store current analysis data
  let currentAnalysis = null;

  // Analyze button event
  analyzeBtn.addEventListener("click", () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.tabs.sendMessage(
        tabs[0].id,
        { action: "getSelectedText" },
        (response) => {
          if (response && response.text) {
            analyzeText(response.text);
          } else {
            resultContainer.style.display = "block";
            historyContainer.style.display = "none";
            resultContent.innerHTML = `
                        <div class="fade-in" style="text-align:center; padding:20px; color:#c62828;">
                            <p><strong>No text selected!</strong></p>
                            <p>Please select some text on the page before analyzing.</p>
                        </div>
                    `;
          }
        }
      );
    });
  });

  // Toggle explanation button
  toggleExplanationBtn.addEventListener("click", () => {
    if (explanationSection.style.display === "none") {
      explanationSection.style.display = "block";
      toggleExplanationBtn.innerHTML = "<i>🔍</i> Hide Explanation";

      // Only load explanation if we have analysis data and haven't loaded it yet
      if (currentAnalysis && !currentAnalysis.explanationLoaded) {
        loadExplanation();
      }
    } else {
      explanationSection.style.display = "none";
      toggleExplanationBtn.innerHTML = "<i>🔍</i> Show Explanation";
    }
  });

  // History button
  historyBtn.addEventListener("click", toggleHistory);

  function analyzeText(text) {
    // Reset explanation state
    explanationSection.style.display = "none";
    toggleExplanationBtn.innerHTML = "<i>🔍</i> Show Explanation";
    currentAnalysis = {
      text: text,
      explanationLoaded: false,
    };

    resultContainer.style.display = "block";
    historyContainer.style.display = "none";
    resultContent.innerHTML = `
            <div style="text-align:center; padding:20px;">
                <div class="loading"></div>
                <p>Analyzing selected text...</p>
            </div>
        `;

    // Request without explanation initially
    fetch("http://127.0.0.1:8000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text, explain: false }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("API returned:", data);
        displayResult(data);
        addToHistory(text, data);

        // Store analysis data
        currentAnalysis.data = data;
      })
      .catch((err) => {
        console.error("Popup error:", err);
        resultContent.innerHTML = `
                <div class="fade-in" style="text-align:center; padding:20px; color:#c62828;">
                    <p><strong>Error contacting API</strong></p>
                    <p>Please ensure the detection service is running</p>
                </div>
            `;
      });
  }

  function loadExplanation() {
    if (!currentAnalysis || !currentAnalysis.text) return;

    // Show loading in explanation section
    explanationSection.innerHTML = `
            <div style="text-align:center; padding:20px;">
                <div class="loading"></div>
                <p>Generating explanation...</p>
                <p class="note">This may take a moment</p>
            </div>
        `;

    // Request explanation
    fetch("http://127.0.0.1:8000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: currentAnalysis.text, explain: true }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Explanation API returned:", data);
        displayExplanation(data);
        currentAnalysis.explanationLoaded = true;
        currentAnalysis.explanationData = data;
      })
      .catch((err) => {
        console.error("Explanation error:", err);
        explanationSection.innerHTML = `
                <div class="fade-in" style="text-align:center; padding:20px; color:#c62828;">
                    <p><strong>Error generating explanation</strong></p>
                    <p>${err.message || "Please try again"}</p>
                </div>
            `;
      });
  }

  function displayResult(data) {
    const result = data.result;
    const roberta = result.roberta_result;
    const aiDetector = result.ai_detector_result;
    const finalLabel = result.final_label;

    const finalLabelDisplay = getFriendlyLabel(finalLabel);
    const robertaLabelDisplay = getFriendlyLabel(roberta.label);
    const aiLabelDisplay = getFriendlyLabel(aiDetector.label);

    const robertaPercentage = Math.round(roberta.confidence * 100);
    const aiPercentage = Math.round(aiDetector.confidence * 100);

    resultContent.innerHTML = `
            <div class="fade-in">
                <p><strong>Final Assessment:</strong> <span class="label ${
                  finalLabel === "CG" || finalLabel === "AI"
                    ? "ai-label"
                    : "human-label"
                }">${finalLabelDisplay}</span></p>
                
                <div style="margin: 20px 0; padding: 15px; background: #f1f8ff; border-radius: 10px;">
                    <p><strong>RoBERTa Model Analysis</strong></p>
                    <p>Result: <span class="label ${
                      roberta.label === "CG" || roberta.label === "AI"
                        ? "ai-label"
                        : "human-label"
                    }">${robertaLabelDisplay}</span></p>
                    <p>Confidence: ${robertaPercentage}%</p>
                    <div class="confidence-bar">
                        <div class="confidence-fill roberta" style="width: ${robertaPercentage}%"></div>
                    </div>
                </div>
                
                <div style="margin: 20px 0; padding: 15px; background: #fff8f1; border-radius: 10px;">
                    <p><strong>AI Detector Analysis</strong></p>
                    <p>Result: <span class="label ${
                      aiDetector.label === "CG" || aiDetector.label === "AI"
                        ? "ai-label"
                        : "human-label"
                    }">${aiLabelDisplay}</span></p>
                    <p>Confidence: ${aiPercentage}%</p>
                    <div class="confidence-bar">
                        <div class="confidence-fill ai" style="width: ${aiPercentage}%"></div>
                    </div>
                </div>
                
                <div style="margin-top: 20px; padding: 10px; background: #e8f5e9; border-radius: 8px; text-align: center;">
                    <p><strong>Tip:</strong> ${
                      finalLabel === "CG" || finalLabel === "AI"
                        ? "This text has a high probability of being AI-generated"
                        : "This text appears to be human-written"
                    }</p>
                </div>
            </div>
        `;
  }

  function displayExplanation(data) {
    const result = data.result;

    if (
      result.explanations &&
      result.explanations.roberta &&
      result.explanations.roberta.lime
    ) {
      explanationSection.innerHTML = renderLimeExplanation(
        result.explanations.roberta.lime
      );
    } else {
      explanationSection.innerHTML = `
                <div class="fade-in" style="text-align:center; padding:20px;">
                    <p>No explanation available</p>
                </div>
            `;
    }
  }

  function renderLimeExplanation(limeData) {
    if (!limeData || limeData.error || !Array.isArray(limeData)) {
      return "<p>No explanation available</p>";
    }

    // Filter out features with insignificant impact
    const significantFeatures = limeData.filter(
      (item) => Math.abs(item.weight) > 0.01
    );

    if (significantFeatures.length === 0) {
      return `
                <div class="fade-in" style="text-align:center; padding:20px;">
                    <p>No significant features detected</p>
                    <p class="threshold-note">Features with impact less than 0.01 are not shown</p>
                </div>
            `;
    }

    // Sort by absolute weight (most significant first)
    significantFeatures.sort((a, b) => Math.abs(b.weight) - Math.abs(a.weight));

    let html = '<div class="fade-in">';
    html += "<h3>Key Features Influencing Prediction</h3>";
    html +=
      '<p class="threshold-note">Showing features with significant impact (|weight| > 0.01)</p>';
    html += '<div class="feature-impact">';

    significantFeatures.forEach((item) => {
      const isAI = item.weight > 0;
      const absWeight = Math.abs(item.weight);
      const barWidth = Math.min(100, absWeight * 1000); // Scale for visualization

      html += `
                <div class="feature-item ${
                  isAI ? "ai-impact" : "human-impact"
                }">
                    <span>${item.feature}</span>
                    <div class="impact-bar">
                        <div class="impact-fill ${
                          isAI ? "ai-fill" : "human-fill"
                        }" style="width: ${barWidth}%"></div>
                    </div>
                    <span>${isAI ? "AI" : "Human"}</span>
                </div>
            `;
    });

    html += "</div></div>";
    return html;
  }

  document.getElementById("pinBtn").addEventListener("click", () => {
    chrome.tabs.create({ url: chrome.runtime.getURL("popup/analyzer.html") });
  });

  function getFriendlyLabel(label) {
    return label === "CG" || label === "AI" ? "AI-generated" : "Human-written";
  }

  function normalizeLabel(label) {
    if (label === "CG" || label === "AI") return "AI";
    if (label === "OR" || label === "Human") return "Human";
    return label;
  }

  // Function to add to history
  function addToHistory(text, data) {
    const historyItem = document.createElement("div");
    historyItem.className = "history-item fade-in";

    const finalLabel =
      data.result.final_label === "CG" || data.result.final_label === "AI"
        ? '<span class="label ai-label"><span class="status-dot ai-dot"></span> AI-generated</span>'
        : '<span class="label human-label"><span class="status-dot human-dot"></span> Human-written</span>';

    historyItem.innerHTML = `
            <div class="history-text">"${
              text.length > 100 ? text.substring(0, 100) + "..." : text
            }"</div>
            <div class="history-result">
                <p>Assessment: ${finalLabel}</p>
                <p>Models agree: ${
                  normalizeLabel(data.result.roberta_result.label) ===
                  normalizeLabel(data.result.ai_detector_result.label)
                    ? "Yes"
                    : "No"
                }</p>
            </div>
        `;

    historyContent.insertBefore(historyItem, historyContent.firstChild);

    // Save to storage
    chrome.storage.local.get({ history: [] }, (result) => {
      const history = result.history;
      history.unshift({
        text: text,
        result: data.result,
      });
      chrome.storage.local.set({ history: history.slice(0, 10) }); // Keep only 10 items
    });
  }

  // Function to toggle history visibility
  function toggleHistory() {
    if (historyContainer.style.display === "block") {
      historyContainer.style.display = "none";
      historyBtn.textContent = "View History";
    } else {
      historyContainer.style.display = "block";
      resultContainer.style.display = "none";
      historyBtn.textContent = "Hide History";
      displayHistory();
    }
  }

  // Function to display history
  function displayHistory() {
    historyContent.innerHTML = "";

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

      history.forEach((item) => {
        const historyItem = document.createElement("div");
        historyItem.className = "history-item fade-in";

        const finalLabel =
          item.result.final_label === "CG" || item.result.final_label === "AI"
            ? '<span class="label ai-label"><span class="status-dot ai-dot"></span> AI-generated</span>'
            : '<span class="label human-label"><span class="status-dot human-dot"></span> Human-written</span>';

        historyItem.innerHTML = `
                    <div class="history-text">"${
                      item.text.length > 100
                        ? item.text.substring(0, 100) + "..."
                        : item.text
                    }"</div>
                    <div class="history-result">
                        <p>Assessment: ${finalLabel}</p>
                        <p>Models agree: ${
                          normalizeLabel(item.result.roberta_result.label) ===
                          normalizeLabel(item.result.ai_detector_result.label)
                            ? "Yes"
                            : "No"
                        }</p>
                    </div>
                `;
        historyContent.appendChild(historyItem);
      });
    });
  }
});

function displayExplanations(explanations) {
  if (!explanations || explanations.error) {
    return `<div class="explanation-section">
            <h3><i>⚠️</i> Explanation Error</h3>
            <p>${explanations?.error || "No explanations available"}</p>
        </div>`;
  }

  // Handle SHAP errors
  if (explanations.roberta?.shap?.error) {
    return `<div class="explanation-section">
            <h3><i>🔍</i> Explanation (LIME)</h3>
            ${renderLimeExplanation(explanations.roberta.lime)}
            <div class="error">
                SHAP Error: ${explanations.roberta.shap.error}
            </div>
        </div>`;
  }

  if (!explanations || !explanations.roberta) {
    return '<div class="explanation-section">No explanations available</div>';
  }

  const roberta = explanations.roberta;

  // SHAP visualization
  let shapHTML = '<div class="shap-explanation">';
  roberta.shap.tokens.forEach((token, i) => {
    const value = roberta.shap.values[i];
    const intensity = Math.min(1, Math.abs(value) * 5);
    const color =
      value > 0
        ? `rgb(255, ${Math.round(200 * (1 - intensity))}, ${Math.round(
            200 * (1 - intensity)
          )})`
        : `rgb(${Math.round(200 * (1 - intensity))}, ${Math.round(
            200 * (1 - intensity)
          )}, 255)`;

    shapHTML += `<span class="shap-token" style="background-color:${color}">${token}</span>`;
  });
  shapHTML += "</div>";

  // LIME visualization
  let limeHTML = '<div class="lime-explanation"><table>';
  roberta.lime.forEach((item) => {
    const colorClass = item.weight > 0 ? "ai-feature" : "human-feature";
    limeHTML += `
            <tr>
                <td>${item.feature}</td>
                <td class="${colorClass}">${
      item.weight > 0 ? "+" : ""
    }${item.weight.toFixed(4)}</td>
                <td>${item.indicates}</td>
            </tr>
        `;
  });
  limeHTML += "</table></div>";

  return `
        <div class="explanation-section">
            <h3><i>🔍</i> Explanation</h3>
            <div class="tabs">
                <button class="tab-btn active" data-tab="shap">SHAP</button>
                <button class="tab-btn" data-tab="lime">LIME</button>
            </div>
            <div id="shapExplanation" class="tab-content active">
                ${shapHTML}
                <div class="legend">
                    <div><span class="color-box ai-color"></span> Indicates CG/AI</div>
                    <div><span class="color-box human-color"></span> Indicates OR/Human</div>
                </div>
            </div>
            <div id="limeExplanation" class="tab-content">
                ${limeHTML}
            </div>
        </div>
    `;
}

function renderShapExplanation(shapData) {
  if (!shapData || !shapData.tokens || !shapData.values) {
    return "<p>No SHAP explanation available</p>";
  }

  let html = '<div class="shap-text">';

  shapData.tokens.forEach((token, i) => {
    const value = shapData.values[i];
    // Normalize SHAP value for color intensity (0-1)
    const intensity = Math.min(1, Math.abs(value) * 5);
    const color =
      value > 0
        ? `rgb(255, ${Math.round(200 * (1 - intensity))}, ${Math.round(
            200 * (1 - intensity)
          )})`
        : `rgb(${Math.round(200 * (1 - intensity))}, ${Math.round(
            200 * (1 - intensity)
          )}, 255)`;

    html += `<span class="shap-token" style="background-color:${color}">${token}</span>`;
  });

  html += "</div>";
  html += `<div class="shap-legend">
        <div><span class="color-box ai-color"></span> Indicates CG/AI</div>
        <div><span class="color-box human-color"></span> Indicates OR/Human</div>
    </div>`;

  return html;
}

function renderLimeExplanation(limeData) {
  if (!limeData || limeData.error || !Array.isArray(limeData)) {
    return "<p>No LIME explanation available</p>";
  }

  let html = '<div class="lime-features">';
  html += "<h4>Top Features Influencing Prediction:</h4>";
  html += "<table>";
  html += "<tr><th>Feature</th><th>Weight</th><th>Indicates</th></tr>";

  limeData.forEach((item) => {
    const colorClass = item.weight > 0 ? "ai-feature" : "human-feature";

    html += `
            <tr>
                <td>${item.feature}</td>
                <td class="${colorClass}">${
      item.weight > 0 ? "+" : ""
    }${item.weight.toFixed(4)}</td>
                <td>${item.indicates}</td>
            </tr>
        `;
  });

  html += "</table></div>";
  return html;
}
