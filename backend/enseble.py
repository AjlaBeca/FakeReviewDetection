from openai import predict_ai_generated
from bert import predict_fake_review
import logging
from prediction import predict_roberta, explain_roberta
from XAIAnalyzer import explain_with_xai

logger = logging.getLogger(__name__)


def ensemble_predict(text, include_explanations=False):
    roberta_result = predict_roberta(text)
    ai_result = predict_ai_generated(text)
    fake_result = predict_fake_review(text)

    # Weights can be tuned
    combined_score = (
        roberta_result["class_probabilities"]["CG"] * 0.4
        + ai_result["class_probabilities"]["AI"] * 0.3
        + fake_result["class_probabilities"]["Fake"] * 0.3
    )

    final_label = "AI-generated or Fake" if combined_score > 0.5 else "Human Genuine"

    result = {
        "final_label": final_label,
        "roberta_result": roberta_result,
        "ai_detector_result": ai_result,
        "fake_review_result": fake_result,
        "combined_score": combined_score,
    }

    if include_explanations:
        try:
            shap_explanation = explain_roberta(
                text
            )  # should return a list of {feature, weight, indicates}
            if isinstance(shap_explanation, list):
                model_prediction = roberta_result
                explanation = explain_with_xai(text, model_prediction, shap_explanation)

                key_indicators = (
                    explanation.get("detailed_analysis", {})
                    .get("evidence_summary", {})
                    .get("key_indicators", [])
                )
                result["explanations"] = {"roberta": key_indicators}

            else:
                logger.warning("SHAP explanation was not a list")
                result["explanations"] = {"error": "Explanation unavailable"}
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            result["explanations"] = {"error": "Failed to generate explanation"}

    return result
