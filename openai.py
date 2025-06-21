from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

device = torch.device("cpu")  # no GPU available

# Load tokenizer and model once, on module load
tokenizer_ai = AutoTokenizer.from_pretrained("roberta-base-openai-detector")
model_ai = AutoModelForSequenceClassification.from_pretrained(
    "roberta-base-openai-detector",
    torch_dtype=torch.float32,
    device_map=None
)
model_ai.to(device)
model_ai.eval()

def predict_ai_generated(text):
    inputs = tokenizer_ai(text, return_tensors="pt", truncation=True, padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model_ai(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)[0].cpu().numpy()
        predicted_class = probs.argmax()
        confidence = float(probs[predicted_class])
    label = "AI" if predicted_class == 1 else "Human"
    return {"label": label, "confidence": confidence, "class_probabilities": {"Human": float(probs[0]), "AI": float(probs[1])}}
