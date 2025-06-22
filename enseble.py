from prediction import predict_roberta, explain_roberta
from openai import predict_ai_generated


def ensemble_predict(text, include_explanations=False):
    roberta_result = predict_roberta(text)
    ai_result = predict_ai_generated(text)
    
    # Weighted ensemble instead of simple OR
    roberta_weight = 0.6  # Trust your model slightly more
    ai_weight = 0.4
    
    # Get probabilities from both models
    roberta_cg_prob = roberta_result['class_probabilities']['CG']
    ai_ai_prob = ai_result['class_probabilities']['AI']
    
    # Calculate weighted combined score
    combined_score = (
        roberta_cg_prob * roberta_weight +
        ai_ai_prob * ai_weight
    )
    
    # Determine final label based on combined score
    final_label = "CG" if combined_score > 0.5 else "OR"
    
    # Prepare result with combined score
    result = {
        "final_label": final_label,
        "roberta_result": roberta_result,
        "ai_detector_result": ai_result,
        "combined_score": combined_score
    }
    
    # Add explanations if requested
    if include_explanations:
        try:
            explanations = explain_roberta(text)
            result["explanations"] = {"roberta": explanations}
        except Exception as e:
            result["explanations"] = {"error": str(e)}
    
    return result