from prediction import predict_roberta
from openai import predict_ai_generated
from bert import predict_fake_review


def ensemble_predict(text, include_explanations=False):
    roberta_result = predict_roberta(text)
    ai_result = predict_ai_generated(text)
    fake_result = predict_fake_review(text)

    # Weights can be tuned, example weights:
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
        from prediction import explain_roberta

        result["explanations"] = {"roberta": explain_roberta(text)}

    return result
