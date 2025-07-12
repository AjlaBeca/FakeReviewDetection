from openai import predict_ai_generated
from bert import predict_fake_review
import logging
from prediction import predict_roberta, explain_roberta
from prediction import explain_text_with_xai

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
            # Get feature attributions from explain_roberta
            feature_attributions = explain_roberta(text)

            # Debug logging
            logger.info(f"Feature attributions type: {type(feature_attributions)}")
            logger.info(f"Feature attributions: {feature_attributions}")

            if isinstance(feature_attributions, list) and len(feature_attributions) > 0:
                # Use the comprehensive explanation function
                explanation = explain_text_with_xai(text)

                # Debug logging
                logger.info(f"Explanation type: {type(explanation)}")
                logger.info(
                    f"Explanation keys: {explanation.keys() if isinstance(explanation, dict) else 'Not a dict'}"
                )

                # Store the full explanation under roberta key
                result["explanations"] = {"roberta": explanation}

            else:
                logger.warning(
                    f"SHAP explanation was not a valid list: {feature_attributions}"
                )
                result["explanations"] = {
                    "roberta": {"error": "No meaningful features found"}
                }

        except Exception as e:
            logger.error(f"Error generating explanation: {e}", exc_info=True)
            result["explanations"] = {
                "roberta": {"error": f"Failed to generate explanation: {str(e)}"}
            }

    return result
