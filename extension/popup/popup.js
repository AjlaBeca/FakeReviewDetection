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
  toggleExplanationBtn.style.display = "none";

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
        toggleExplanationBtn.style.display = "inline-block";
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
        toggleExplanationBtn.style.display = "none";
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
    const fakeReview = result.fake_review_result; // NEW
    const finalLabel = result.final_label;

    const finalLabelDisplay = getFriendlyLabel(finalLabel);
    const robertaLabelDisplay = getFriendlyLabel(roberta.label);
    const aiLabelDisplay = getFriendlyLabel(aiDetector.label);
    const fakeLabelDisplay = fakeReview.label; // simple for now

    const robertaPercentage = Math.round(roberta.confidence * 100);
    const aiPercentage = Math.round(aiDetector.confidence * 100);
    const fakePercentage = Math.round(fakeReview.confidence * 100); // NEW

    resultContent.innerHTML = `
  <div class="fade-in">
    <p><strong>Final Assessment:</strong> <span class="label ${
      finalLabel === "CG" || finalLabel === "AI" ? "ai-label" : "human-label"
    }">${finalLabelDisplay}</span></p>

    <div style="margin: 20px 0; padding: 15px; background: #f1f8ff; border-radius: 10px;">
      <p><strong>RoBERTa Model Analysis</strong> 
        <span class="info-icon" data-id="roberta" title="This model detects AI-generated text by analyzing linguistic patterns and writing style.">ℹ️</span>
      </p>
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
      <p><strong>AI Detector Analysis</strong> 
        <span class="info-icon" data-id="aidetector" title="This model estimates the likelihood that the text was written by an AI using a specialized classifier.">ℹ️</span>
      </p>
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

    <div style="margin: 20px 0; padding: 15px; background: #e8f5e9; border-radius: 10px;">
      <p><strong>Fake Review Detector Analysis</strong> 
        <span class="info-icon" data-id="fake" title="This model predicts whether the review is genuine or fake based on review content and patterns.">ℹ️</span>
      </p>
      <p>Result: <span class="label ${
        fakeReview.label === "Fake" ? "ai-label" : "human-label"
      }">${fakeLabelDisplay}</span></p>
      <p>Confidence: ${fakePercentage}%</p>
      <div class="confidence-bar">
        <div class="confidence-fill fake" style="width: ${fakePercentage}%; background-color: #4caf50;"></div>
      </div>
    </div>

    <div style="margin-top: 20px; padding: 10px; background: #e0e0e0; border-radius: 8px; text-align: center;">
      <p><strong>Tip:</strong> ${
        ["CG", "AI", "Fake"].includes(finalLabel)
          ? "This text has a high probability of being AI-generated or fake"
          : "This text appears to be human-written and genuine"
      }</p>
    </div>
  </div>
`;
  }

  document.addEventListener("click", (event) => {
    const icon = event.target.closest(".info-icon");
    const existingTooltip = document.querySelector(".info-box");

    if (icon) {
      event.preventDefault();

      // If this icon already has its tooltip visible, remove it (toggle)
      if (
        existingTooltip &&
        existingTooltip.dataset.owner === icon.dataset.id
      ) {
        existingTooltip.remove();
        return;
      }

      // Remove any other tooltip
      document.querySelectorAll(".info-box").forEach((box) => box.remove());

      // Tooltip text mapping
      const tooltipTexts = {
        roberta:
          "This model detects AI-generated text by analyzing linguistic patterns and writing style.",
        aidetector:
          "This model estimates the likelihood that the text was written by an AI using a specialized classifier.",
        fake: "This model predicts whether the review is genuine or fake based on review content and patterns.",
      };

      const id = icon.dataset.id;
      const tooltipText = tooltipTexts[id];
      if (!tooltipText) return;

      // Create tooltip
      const tooltip = document.createElement("div");
      tooltip.className = "info-box";
      tooltip.textContent = tooltipText;
      tooltip.dataset.owner = id; // Mark the tooltip as belonging to this icon
      document.body.appendChild(tooltip);

      // Position it
      const rect = icon.getBoundingClientRect();
      const top = rect.bottom + window.scrollY + 8;
      const left = Math.min(
        window.innerWidth - 250,
        rect.left + window.scrollX
      );
      tooltip.style.top = `${top}px`;
      tooltip.style.left = `${left}px`;
    } else {
      // Clicked outside: remove any tooltip
      document.querySelectorAll(".info-box").forEach((box) => box.remove());
    }
  });

  function displayExplanation(data) {
    const result = data.result;
    const explanations = result.explanations?.roberta;

    if (Array.isArray(explanations)) {
      explanationSection.innerHTML =
        renderShapExplanationFromArray(explanations);
    } else if (
      explanations?.shap?.detailed_analysis?.evidence_summary?.key_indicators
    ) {
      explanationSection.innerHTML = renderShapExplanationFromArray(
        explanations.shap.detailed_analysis.evidence_summary.key_indicators
      );
    } else {
      explanationSection.innerHTML = `
            <div class="fade-in" style="text-align:center; padding:20px;">
                <p>${explanations?.error || "No explanation available"}</p>
            </div>`;
    }
  }
  function renderShapExplanationFromArray(shapArray) {
    if (!Array.isArray(shapArray)) {
      return "<p>No SHAP explanation available</p>";
    }

    const significantFeatures = shapArray
      .filter((item) => item && item.feature && typeof item.weight === "number")
      .map((item) => ({
        ...item,
        feature: item.feature
          .replace(/Ġ/g, " ")
          .replace(/âĢ/g, "'")
          .replace(/Ļ/g, "")
          .replace(/[^\w\s.,!?'"čćžšđČĆŽŠĐ-]/g, "") // ⚠️ now preserves Bosnian letters
          .trim(),
      }))
      .filter((item) => item.feature.length > 1);

    if (significantFeatures.length === 0) {
      return `
      <div class="fade-in" style="text-align:center; padding:20px;">
        <p>No significant features detected</p>
        <p class="threshold-note">Only phrases with meaningful impact are shown</p>
      </div>`;
    }

    significantFeatures.sort((a, b) => Math.abs(b.weight) - Math.abs(a.weight));

    let html = '<div class="fade-in">';
    html += "<h3>Key Phrases Influencing Prediction</h3>";
    html += '<div class="feature-impact">';

    for (const item of significantFeatures) {
      const isAI = item.weight > 0;
      const barWidth = Math.min(100, Math.abs(item.weight) * 1000);

      html += `
      <div class="feature-item ${isAI ? "ai-impact" : "human-impact"}">
        <span>"${item.feature}"</span>
        <div class="impact-bar">
          <div class="impact-fill ${isAI ? "ai-fill" : "human-fill"}"
            style="width: ${barWidth}%">
          </div>
        </div>
        <span>${isAI ? "AI" : "Human"}</span>
      </div>`;
    }

    html += "</div></div>";
    return html;
  }

  document.getElementById("pinBtn").addEventListener("click", () => {
    chrome.tabs.create({ url: chrome.runtime.getURL("popup/analyzer.html") });
  });

  function getFriendlyLabel(label) {
    if (label === "CG" || label === "AI") return "AI-generated";
    if (label === "OR" || label === "Human") return "Human-written";
    if (label === "Fake") return "Fake Review";
    if (label === "Genuine") return "Genuine Review";
    return label;
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
