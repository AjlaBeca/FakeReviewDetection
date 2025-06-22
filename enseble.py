
from openai import predict_ai_generated
from prediction import predict_roberta, explain_roberta

def ensemble_predict(text, include_explanations=False):
    roberta_result = predict_roberta(text)
    ai_result = predict_ai_generated(text)
    
    is_fake = (roberta_result['label'] == "CG") or (ai_result['label'] == "AI")
    final_label = "CG" if is_fake else "OR"
    
    result = {
        "final_label": final_label,
        "roberta_result": roberta_result,
        "ai_detector_result": ai_result,
    }
    
    # Add explanations if requested
    if include_explanations:
        result["explanations"] = {
            "roberta": explain_roberta(text)
        }
    
    return result