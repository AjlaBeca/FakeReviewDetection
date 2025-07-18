from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

device = torch.device("cpu")
tokenizer_ai = None
model_ai = None


def load_models():
    global tokenizer_ai, model_ai
    try:
        if tokenizer_ai is None:
            tokenizer_ai = AutoTokenizer.from_pretrained("roberta-base-openai-detector")
        if model_ai is None:
            model_ai = AutoModelForSequenceClassification.from_pretrained(
                "roberta-base-openai-detector"
            )
            model_ai.to(device)
            model_ai.eval()
    except Exception as e:
        raise RuntimeError(f"Failed to load OpenAI model: {e}")


def predict_ai_generated(text):
    load_models()
    inputs = tokenizer_ai(text, return_tensors="pt", truncation=True, padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model_ai(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)[0].cpu().numpy()
        predicted_class = probs.argmax()
        confidence = float(probs[predicted_class])

    label = "AI" if predicted_class == 0 else "Human"

    return {
        "label": label,
        "confidence": confidence,
        "class_probabilities": {"AI": float(probs[0]), "Human": float(probs[1])},
    }
