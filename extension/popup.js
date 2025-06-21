    document.getElementById("analyzeBtn").addEventListener("click", () => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            chrome.tabs.sendMessage(tabs[0].id, { action: "getSelectedText" }, (response) => {
                if (response && response.text) {
                    analyzeText(response.text);
                } else {
                    document.getElementById("result").textContent = "No text selected.";
                }
            });
        });
    });

    document.getElementById("historyBtn").addEventListener("click", () => {
        displayHistory();
    });

    function getFriendlyLabel(label) {
        return label === "CG" || label === "AI" ? "AI-generated" : "Human-written";
    }

    function analyzeText(text) {
  fetch("http://127.0.0.1:8000/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: text })
  })
  .then(response => response.json())
  .then(data => {
    console.log("API returned:", data);

    const result  = data.result;
    const roberta = result.roberta_result;
    const ai      = result.ai_detector_result;
    const finalL  = result.final_label;

    document.getElementById("result").innerHTML = `
      <strong>Final Label:</strong> ${getFriendlyLabel(finalL)}<br>
      <strong>RoBERTa:</strong> ${styledLabel(roberta.label, roberta.confidence)}<br>
      <strong>AI Detector:</strong> ${styledLabel(ai.label, ai.confidence)}`;

    // Save to history
    chrome.storage.local.get({ history: [] }, (res) => {
      const h = res.history;
      h.unshift({ text, result });
      chrome.storage.local.set({ history: h });
    });
  })
  .catch(err => {
    console.error("Popup error:", err);
    document.getElementById("result").textContent = "Error contacting API.";
  });
}

function styledLabel(label) {
  const isAI = label === "CG" || label === "AI";
  const className = isAI ? "fake" : "real";
  const text = isAI ? "AI-generated" : "Human-written";
  return `<span class="${className} label">${text}</span>`;
}

function displayHistory() {
  chrome.storage.local.get({ history: [] }, (result) => {
    const historyDiv = document.getElementById("history");
    historyDiv.innerHTML = `<div class="history-title">Analysis History</div>`;

    if (result.history.length === 0) {
      historyDiv.innerHTML += "<p>No history yet.</p>";
      return;
    }

    result.history.slice(0, 10).forEach((entry, index) => {

      if (!entry.result || !entry.result.roberta_result) {
        historyDiv.innerHTML += `
          <div class="history-item">
            <strong>#${index + 1}</strong><br>
            <em>${entry.text}</em><br>
            <div>Error: Invalid history data</div>
          </div>`;
        return;
      }

      const finalLabel = styledLabel(entry.result.final_label);

      const robertaLabel = styledLabel(entry.result.roberta_result.label);
      const robertaBar = createConfidenceBar(entry.result.roberta_result.confidence, "roberta");

      const aiLabel = styledLabel(entry.result.ai_detector_result.label);
      const aiBar = createConfidenceBar(entry.result.ai_detector_result.confidence, "ai");

      historyDiv.innerHTML += `
        <div class="history-item">
          <strong>#${index + 1}</strong><br>
          <em>${entry.text}</em><br>
          <div><strong>Final:</strong> ${finalLabel}</div>
          <div class="roberta">
            <strong>RoBERTa:</strong> ${robertaLabel}
            ${robertaBar}
          </div>
          <div class="ai">
            <strong>AI Detector:</strong> ${aiLabel}
            ${aiBar}
          </div>
        </div>
      `;
    });
  });
}

function createConfidenceBar(confidence, modelClass) {
  const percentage = (confidence * 100).toFixed(2);
  return `
    <div class="confidence-bar ${modelClass}">
      <div class="confidence-fill" style="width: ${percentage}%;"></div>
    </div>
    <div class="confidence-label">${percentage}% confidence</div>
  `;
}

function displayResult(data) {
    if (!data || !data.roberta_result || !data.ai_detector_result) {
    console.error("Invalid data structure:", data);
    return `<div>Error: Received invalid data from API. Please try again.</div>`;
  }
  const finalLabel = styledLabel(data.final_label);

  const robertaLabel = styledLabel(data.roberta_result.label);
  const robertaBar = createConfidenceBar(data.roberta_result.confidence, "roberta");

  const aiLabel = styledLabel(data.ai_detector_result.label);
  const aiBar = createConfidenceBar(data.ai_detector_result.confidence, "ai");

  return `
    <div>
      <strong>Final Label:</strong> ${finalLabel}
    </div>
    <div class="roberta">
      <strong>RoBERTa:</strong> ${robertaLabel}
      ${robertaBar}
    </div>
    <div class="ai">
      <strong>AI Detector:</strong> ${aiLabel}
      ${aiBar}
    </div>
  `;
}
