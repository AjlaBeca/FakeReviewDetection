from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch
from lime import lime_text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize once
device = torch.device("cpu")
tokenizer_roberta = None
model_roberta = None

def load_models():
    global tokenizer_roberta, model_roberta
    if tokenizer_roberta is None:
        tokenizer_roberta = RobertaTokenizer.from_pretrained("../models/roberta_finetuned")
    if model_roberta is None:
        model_roberta = RobertaForSequenceClassification.from_pretrained("../models/roberta_finetuned")
        model_roberta.to(device)
        model_roberta.eval()

def predict_roberta(text):
    load_models()
    inputs = tokenizer_roberta(text, return_tensors="pt", truncation=True, padding=True, max_length=256)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model_roberta(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)[0].cpu().numpy()
        predicted_class = probs.argmax()
        confidence = float(probs[predicted_class])
    
    label = "CG" if predicted_class == 0 else "OR"
    return {
        "label": label,
        "confidence": confidence,
        "class_probabilities": {
            "CG": float(probs[0]),
            "OR": float(probs[1])
        }
    }

def explain_roberta(text):
    """Generate LIME explanations"""
    try:
        load_models()
        explainer_lime = lime_text.LimeTextExplainer(class_names=["CG", "OR"])
        
        def classifier_fn(texts):
            inputs = tokenizer_roberta(
                texts, 
                return_tensors="pt", 
                truncation=True, 
                padding=True, 
                max_length=256
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = model_roberta(**inputs)
                return torch.softmax(outputs.logits, dim=1).cpu().numpy()
        
        lime_exp = explainer_lime.explain_instance(
            text, 
            classifier_fn, 
            num_features=15,
            num_samples=100
        )
        
        lime_data = []
        for feature, weight in lime_exp.as_list():
            lime_data.append({
                "feature": str(feature),
                "weight": float(weight),
                "indicates": "CG" if weight > 0 else "OR"
            })
        
        return {"lime": lime_data}
        
    except Exception as e:
        logger.error(f"Explanation failed: {str(e)}", exc_info=True)
        return {"error": str(e)}