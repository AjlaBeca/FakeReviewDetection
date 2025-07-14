from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

device = torch.device("cpu")
tokenizer_fake = None
model_fake = None


def load_fake_review_model():
    global tokenizer_fake, model_fake
    if tokenizer_fake is None:
        tokenizer_fake = AutoTokenizer.from_pretrained("yartyjung/Fake-Review-Detector")
    if model_fake is None:
        model_fake = AutoModelForSequenceClassification.from_pretrained(
            "yartyjung/Fake-Review-Detector"
        )
        model_fake.to(device)
        model_fake.eval()


def predict_fake_review(text):
    load_fake_review_model()
    inputs = tokenizer_fake(
        text, return_tensors="pt", truncation=True, padding=True, max_length=256
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model_fake(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)[0].cpu().numpy()
        predicted_class = probs.argmax()
        confidence = float(probs[predicted_class])

    label = "Fake" if predicted_class == 1 else "Genuine"

    return {
        "label": label,
        "confidence": confidence,
        "class_probabilities": {"Genuine": float(probs[0]), "Fake": float(probs[1])},
    }
