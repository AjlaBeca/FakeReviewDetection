from prediction import predict_roberta
from openai import predict_ai_generated

def ensemble_predict(text, include_explanations=False):
    roberta_result = predict_roberta(text)
    ai_result = predict_ai_generated(text)
    
    # Simple weighted ensemble
    roberta_weight = 0.6
    ai_weight = 0.4
    
    # Get probabilities
    roberta_cg_prob = roberta_result['class_probabilities']['CG']
    ai_ai_prob = ai_result['class_probabilities']['AI']
    
    # Calculate combined score
    combined_score = (
        roberta_cg_prob * roberta_weight +
        ai_ai_prob * ai_weight
    )
    
    # Determine final label
    final_label = "AI" if combined_score > 0.5 else "Human"
    
    # Prepare result
    result = {
        "final_label": final_label,
        "roberta_result": roberta_result,
        "ai_detector_result": ai_result,
        "combined_score": combined_score
    }
    
    # Add explanations if requested
    if include_explanations:
        from prediction import explain_roberta
        result["explanations"] = {"roberta": explain_roberta(text)}
    
    return result