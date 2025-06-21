from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch

tokenizer_roberta = RobertaTokenizer.from_pretrained("roberta_finetuned")
model_roberta = RobertaForSequenceClassification.from_pretrained(
    "roberta_finetuned",
    torch_dtype=torch.float32,
    device_map=None
)
model_roberta.eval()

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
