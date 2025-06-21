chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getSelectedText") {
    const selectedText = window.getSelection().toString();
    sendResponse({ text: selectedText });
  } else if (request.action === "analyzeSelection") {
    fetch("http://127.0.0.1:8000/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: request.text })
    })
    .then(res => res.json())
    .then(data => {
      alert(`AI Detection:
Final Label: ${data.final_label}
RoBERTa: ${data.roberta_result.label} (${(data.roberta_result.confidence * 100).toFixed(2)}%)
AI Detector: ${data.ai_detector_result.label} (${(data.ai_detector_result.confidence * 100).toFixed(2)}%)`);
    })
    .catch(err => {
      console.error("Fetch error:", err);
      alert("Error contacting API.");
    });

    return true; 
  }
});
