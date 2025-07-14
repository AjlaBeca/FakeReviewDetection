from ai_detector import predict_ai_generated
from fake_review import predict_fake_review
from prediction import analyze_text
import logging

logger = logging.getLogger(__name__)


def ensemble_predict(text, include_explanations=False):
    roberta_result = analyze_text(text, explain=False)["prediction"]
    ai_result = predict_ai_generated(text)
    fake_result = predict_fake_review(text)

    # can change weights
    combined_score = (
        roberta_result["class_probabilities"]["AI"] * 0.4
        + ai_result["class_probabilities"]["AI"] * 0.3
        + fake_result["class_probabilities"]["Fake"] * 0.3
    )

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
