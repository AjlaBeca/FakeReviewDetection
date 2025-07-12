from openai import predict_ai_generated
from bert import predict_fake_review
from prediction import analyze_text  # Import our new analyze_text function
import logging

logger = logging.getLogger(__name__)


def ensemble_predict(text, include_explanations=False):
    # Get predictions from all models
    roberta_result = analyze_text(text, explain=False)["prediction"]
    ai_result = predict_ai_generated(text)
    fake_result = predict_fake_review(text)

    # Weights can be tuned
    combined_score = (
        roberta_result["class_probabilities"]["AI"] * 0.4
        + ai_result["class_probabilities"]["AI"] * 0.3
        + fake_result["class_probabilities"]["Fake"] * 0.3
    )

    # Determine final label based on combined score
    if combined_score > 0.6:
        final_label = "AI-generated or Fake"
    elif combined_score > 0.4:
        final_label = "Suspicious Content"
    else:
        final_label = "Human Genuine"

    result = {
        "final_label": final_label,
        "roberta_result": roberta_result,
        "ai_detector_result": ai_result,
        "fake_review_result": fake_result,
        "combined_score": combined_score,
    }

    if include_explanations:
        try:
            # Get research-based explanation
            analysis = analyze_text(text, explain=True)

            if "explanation" in analysis:
                result["explanations"] = {"roberta": analysis["explanation"]}
            else:
                result["explanations"] = {
                    "roberta": {"error": "Explanation not available"}
                }

        except Exception as e:
            logger.error(f"Error generating explanation: {e}", exc_info=True)
            result["explanations"] = {
                "roberta": {"error": f"Failed to generate explanation: {str(e)}"}
            }

    return result
