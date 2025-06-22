from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch
import shap
from lime import lime_text
import numpy as np

tokenizer_roberta = RobertaTokenizer.from_pretrained("roberta_finetuned")
model_roberta = RobertaForSequenceClassification.from_pretrained(
    "roberta_finetuned",
    torch_dtype=torch.float32,
    device_map=None
)
model_roberta.eval()

explainer_shap = shap.Explainer(model_roberta, tokenizer_roberta)
explainer_lime = lime_text.LimeTextExplainer(class_names=["CG", "OR"])

def predict_roberta(text):
    inputs = tokenizer_roberta(text, return_tensors="pt", truncation=True, padding=True, max_length=256)
    with torch.no_grad():
        outputs = model_roberta(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
        predicted_class = probs.argmax()
        confidence = float(probs[predicted_class])
    label = "CG" if predicted_class == 0 else "OR"
    return {"label": label, "confidence": confidence, "class_probabilities": {"CG": float(probs[0]), "OR": float(probs[1])}}
def explain_roberta(text):
    """Generate LIME explanations only"""
    try:
        # LIME explanation
        explainer_lime = lime_text.LimeTextExplainer(class_names=["CG", "OR"])
        
        def classifier_fn(texts):
            inputs = tokenizer_roberta(
                texts, 
                return_tensors="pt", 
                truncation=True, 
                padding=True, 
                max_length=256
            )
            with torch.no_grad():
                outputs = model_roberta(**inputs)
                logits = outputs.logits
                return torch.softmax(logits, dim=1).detach().numpy()
        
        lime_exp = explainer_lime.explain_instance(
            text, 
            classifier_fn, 
            num_features=10, 
            num_samples=100
        )
        
        lime_data = []
        for feature, weight in lime_exp.as_list():
            lime_data.append({
                "feature": str(feature),  # Convert to string
                "weight": float(weight),
                "indicates": "CG" if weight > 0 else "OR"
            })
        
        return {
            "lime": lime_data
        }
        
    except Exception as e:
        logger.error(f"Explanation failed: {str(e)}", exc_info=True)
        return {
            "error": str(e)
        }