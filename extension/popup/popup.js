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
    const fakeReview = result.fake_review_result;
    const finalLabel = result.final_label;

    const robertaPercentage = Math.round(roberta.confidence * 100);
    const aiPercentage = Math.round(aiDetector.confidence * 100);
    const fakePercentage = Math.round(fakeReview.confidence * 100);

    let tipMessage = "";
    if (finalLabel === "CG" || finalLabel === "AI") {
      tipMessage = "This text has a high probability of being AI-generated";
    } else if (finalLabel === "Fake") {
      tipMessage = "This review appears to be fake or inauthentic";
    } else {
      tipMessage = "This text appears to be human-written and genuine";
    }

    resultContent.innerHTML = `
  <div class="fade-in">
    <p><strong>Final Assessment:</strong> <span class="label ${getLabelClass(
      finalLabel
    )}">
        ${getLabelText(finalLabel)}
      </span> </p>

   <div style="margin: 20px 0; padding: 15px; background: #f1f8ff; border-radius: 10px;">
      <p><strong>RoBERTa Model Analysis</strong> 
        <span class="info-icon" data-id="roberta" title="This model detects AI-generated text by analyzing linguistic patterns and writing style.">ℹ️</span>
      </p>
      <p>Result: <span class="label ${getLabelClass(
        roberta.label
      )}">${getLabelText(roberta.label)}</span></p>
      <p>Confidence: ${robertaPercentage}%</p>
      <div class="confidence-bar">
        <div class="confidence-fill roberta" style="width: ${robertaPercentage}%"></div>
      </div>
    </div>

    <div style="margin: 20px 0; padding: 15px; background: #fff8f1; border-radius: 10px;">
      <p><strong>AI Detector Analysis</strong> 
        <span class="info-icon" data-id="aidetector" title="This model estimates the likelihood that the text was written by an AI using a specialized classifier.">ℹ️</span>
      </p>
      <p>Result: <span class="label ${getLabelClass(
        aiDetector.label
      )}">${getLabelText(aiDetector.label)}</span></p>
      <p>Confidence: ${aiPercentage}%</p>
      <div class="confidence-bar">
        <div class="confidence-fill ai" style="width: ${aiPercentage}%"></div>
      </div>
    </div>

   <div style="margin: 20px 0; padding: 15px; background: #e8f5e9; border-radius: 10px;">
      <p><strong>Fake Review Detector Analysis</strong> 
        <span class="info-icon" data-id="fake" title="This model predicts whether the review is genuine or fake based on review content and patterns.">ℹ️</span>
      </p>
      <p>Result: <span class="label ${getLabelClass(
        fakeReview.label
      )}">${getLabelText(fakeReview.label)}</span></p>
      <p>Confidence: ${fakePercentage}%</p>
      <div class="confidence-bar">
        <div class="confidence-fill fake" style="width: ${fakePercentage}%"></div>
      </div>
    </div>

   <div style="margin-top: 20px; padding: 10px; background: #e0e0e0; border-radius: 8px; text-align: center;">
      <p><strong>Tip:</strong> ${getTipMessage(finalLabel)}</p>
    </div>
  </div>
`;
  }

  document.addEventListener("click", (event) => {
    const icon = event.target.closest(".info-icon");
    const existingTooltip = document.querySelector(".info-box");

    if (icon) {
      event.preventDefault();

      if (
        existingTooltip &&
        existingTooltip.dataset.owner === icon.dataset.id
      ) {
        existingTooltip.remove();
        return;
      }

      document.querySelectorAll(".info-box").forEach((box) => box.remove());

      // tooltip text mapping
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

      // create tooltip
      const tooltip = document.createElement("div");
      tooltip.className = "info-box";
      tooltip.textContent = tooltipText;
      tooltip.dataset.owner = id;
      document.body.appendChild(tooltip);

      // positioning tooltip
      const rect = icon.getBoundingClientRect();
      const top = rect.bottom + window.scrollY + 8;
      const left = Math.min(
        window.innerWidth - 250,
        rect.left + window.scrollX
      );
      tooltip.style.top = `${top}px`;
      tooltip.style.left = `${left}px`;
    } else {
      // clicked outside: remove any tooltip
      document.querySelectorAll(".info-box").forEach((box) => box.remove());
    }
  });

  function displayExplanation(data) {
    try {
      const explanation = data?.result?.explanations?.roberta;

      if (!explanation) {
        explanationSection.innerHTML = `
      <div class="fade-in" style="text-align:center; padding:20px; color:#c62828;">
        <p><strong>No explanation available</strong></p>
        <p>Unable to find explanation data in API response</p>
      </div>`;
        return;
      }

      const insightItems = explanation.key_insights.map((insight) => ({
        text: insight.text,
        type: insight.type || "ambiguous",
        icon: insight.icon || "❓",
        stat: insight.text.match(/\(([^)]+)\)/)?.[1] || "",
      }));

      let html = `
    <div class="fade-in explanation-container">
      <div class="explanation-header">
        <div class="explanation-icon">🔍</div>
        <h3>Research-Based Analysis</h3>
      </div>
      
      <div class="conclusion">
        ${explanation.conclusion}
      </div>
      
      <div class="key-insights" style="margin-top: 20px;">
        <h4 style="margin-bottom: 10px;"> Key Linguistic Indicators</h4>
        <ul class="insight-list">`;

      insightItems.forEach((item) => {
        html += `
          <li class="insight-item ${item.type}">
            <div class="insight-icon">${item.icon}</div>
            <div>
              <div class="insight-text">${item.text.replace(
                /\(([^)]+)\)/,
                ""
              )}</div>
              <div class="insight-stats">${item.stat}</div>
            </div>
          </li>`;
      });

      html += `
        </ul>
      </div>
      
      <div class="research-basis">
        <em>${explanation.research_basis}</em>
      </div>
    </div>`;

      explanationSection.innerHTML = html;
    } catch (err) {
      console.error("Error rendering explanation:", err);
      explanationSection.innerHTML = `
    <div class="fade-in" style="text-align:center; padding:20px; color:#c62828;">
      <p><strong>Error rendering explanation</strong></p>
      <p>${err.message || "Please try again"}</p>
    </div>`;
    }
  }

  document.getElementById("pinBtn").addEventListener("click", () => {
    chrome.tabs.create({ url: chrome.runtime.getURL("popup/analyzer.html") });
  });

  function getLabelClass(label) {
    if (
      label === "CG" ||
      label === "AI" ||
      label === "AI-generated or Fake" ||
      label === "Fake"
    ) {
      return "ai-label";
    }
    return "human-label";
  }

  function getLabelText(label) {
    if (label === "CG" || label === "AI") return "AI-generated";
    if (label === "OR" || label === "Human") return "Human-written";
    if (label === "Fake") return "Fake Review";
    if (label === "Genuine") return "Genuine Review";
    if (label === "AI-generated or Fake") return "AI-generated or Fake";
    return label;
  }

  function getTipMessage(finalLabel) {
    if (
      finalLabel === "CG" ||
      finalLabel === "AI" ||
      finalLabel === "Fake" ||
      finalLabel === "AI-generated or Fake"
    ) {
      return "This text has a high probability of being AI-generated or fake";
    }
    return "This text appears to be human-written and genuine";
  }

  // add review to history
  function addToHistory(text, data) {
    const historyItem = document.createElement("div");
    historyItem.className = "history-item fade-in";

    const finalLabel = data.result.final_label;

    historyItem.innerHTML = `
      <div class="history-text">"${
        text.length > 100 ? text.substring(0, 100) + "..." : text
      }"</div>
      <div class="history-result">
        <p>Assessment: <span class="label ${getLabelClass(
          finalLabel
        )}">${getLabelText(finalLabel)}</span></p>
        <p>Models agree: ${
          getLabelClass(data.result.roberta_result.label) ===
          getLabelClass(data.result.ai_detector_result.label)
            ? "Yes"
            : "No"
        }</p>
      </div>
    `;

    historyContent.insertBefore(historyItem, historyContent.firstChild);

    // save to storage
    chrome.storage.local.get({ history: [] }, (result) => {
      const history = result.history;
      history.unshift({
        text: text,
        result: data.result,
      });
      chrome.storage.local.set({ history: history.slice(0, 10) });
    });
  }

  // toggle history visibility
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

  // function to display history
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

        const finalLabel = item.result.final_label;

        historyItem.innerHTML = `
        <div class="history-text">"${
          item.text.length > 100
            ? item.text.substring(0, 100) + "..."
            : item.text
        }"</div>
        <div class="history-result">
          <p>Assessment: <span class="label ${getLabelClass(
            finalLabel
          )}">${getLabelText(finalLabel)}</span></p>
          <p>Models agree: ${
            getLabelClass(item.result.roberta_result.label) ===
            getLabelClass(item.result.ai_detector_result.label)
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
