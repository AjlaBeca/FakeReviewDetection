from prediction import predict_roberta
from openai import predict_ai_generated

def ensemble_predict(text):
    roberta_result = predict_roberta(text)
    ai_result = predict_ai_generated(text)

    # Simple ensemble: consider text fake if either model says it's AI-generated/fake
    is_fake = (roberta_result['label'] == "CG") or (ai_result['label'] == "AI")
    final_label = "CG" if is_fake else "OR"

    return {
        "final_label": final_label,
        "roberta_result": roberta_result,
        "ai_detector_result": ai_result,
    }
