import torch
import spacy
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from textstat import flesch_reading_ease, gunning_fog

# Load models globally
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_path = "../models/roberta_finetuned"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path).to(device)
model.eval()
nlp = spacy.load("en_core_web_sm")

# Research-based thresholds from paper
FEATURE_THRESHOLDS = {
    "avg_sentence_length": (11.67, 14.31),
    "exclamation_ratio": (0.28, 0.52),
    "question_ratio": (0.01, 0.09),
    "lexical_diversity": (0.72, 0.80),
    "first_person_ratio": (4.13 / 63.22, 3.34 / 75.53),
    "passive_ratio": (0.36, 0.47),
    "flesch": (86.60, 77.05),
    "gunning_fog": (6.29, 8.18),
    "positive_phrase_ratio": (0.29, 0.20),
}

POSITIVE_PHRASES = {
    "great",
    "good",
    "excellent",
    "awesome",
    "nice",
    "perfect",
    "love",
    "recommend",
    "best",
    "fantastic",
    "wonderful",
}


def predict(text):
    """Predict if text is AI-generated with confidence scores"""
    inputs = tokenizer(
        text, return_tensors="pt", truncation=True, padding=True, max_length=256
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
        predicted_class = probs.argmax()
        confidence = float(probs[predicted_class])

    return {
        "label": "AI" if predicted_class == 0 else "Human",
        "confidence": confidence,
        "class_probabilities": {"AI": float(probs[0]), "Human": float(probs[1])},
    }


def extract_linguistic_features(text):
    """Extract research-based linguistic features from text"""
    doc = nlp(text)
    sentences = list(doc.sents)
    words = [token.text for token in doc if not token.is_punct]

    if not words:
        return {}

    unique_words = set(word.lower() for word in words)

    # Sentence statistics
    sentence_lengths = [len(sentence) for sentence in sentences]
    avg_sentence_length = np.mean(sentence_lengths) if sentence_lengths else 0

    # Punctuation
    exclamation_ratio = text.count("!") / len(words)
    question_ratio = text.count("?") / len(words)

    # Lexical diversity
    lexical_diversity = len(unique_words) / len(words)

    # Pronoun counts
    first_person = sum(
        1
        for token in doc
        if token.lemma_ in {"i", "me", "my", "mine", "we", "us", "our"}
    )

    # Passive voice detection
    passive_count = sum(1 for token in doc if token.dep_ == "nsubjpass")

    # Positive phrases
    positive_count = sum(1 for word in words if word.lower() in POSITIVE_PHRASES)

    # Readability scores
    flesch = flesch_reading_ease(text)
    gunning = gunning_fog(text)

    return {
        "word_count": len(words),
        "sentence_count": len(sentences),
        "avg_sentence_length": avg_sentence_length,
        "exclamation_ratio": exclamation_ratio,
        "question_ratio": question_ratio,
        "lexical_diversity": lexical_diversity,
        "first_person_ratio": first_person / len(words),
        "passive_ratio": passive_count / len(words),
        "positive_phrase_ratio": positive_count / len(words),
        "flesch": flesch,
        "gunning_fog": gunning,
    }


def generate_explanation(prediction, features):
    """Generate explanation aligned with the actual prediction"""
    # Feature weights based on research significance
    feature_weights = {
        "lexical_diversity": (
            0.8 if features.get("lexical_diversity", 0) > 0.75 else -0.8
        ),
        "avg_sentence_length": (
            0.7 if features.get("avg_sentence_length", 0) > 13 else -0.7
        ),
        "passive_ratio": 0.6 if features.get("passive_ratio", 0) > 0.4 else -0.6,
        "positive_phrase_ratio": (
            -0.7 if features.get("positive_phrase_ratio", 0) > 0.25 else 0.7
        ),
        "flesch": -0.6 if features.get("flesch", 0) > 80 else 0.6,
        "gunning_fog": 0.6 if features.get("gunning_fog", 0) > 7 else -0.6,
    }

    # Sort features by absolute weight
    sorted_features = sorted(
        [
            {"feature": k, "weight": v}
            for k, v in feature_weights.items()
            if k in features
        ],
        key=lambda x: abs(x["weight"]),
        reverse=True,
    )

    # Generate natural language explanations
    key_insights = []
    for feat in sorted_features[:3]:
        feature = feat["feature"]
        value = features[feature]
        human_mean, ai_mean = FEATURE_THRESHOLDS[feature]

        if feat["weight"] > 0:
            insight = (
                f"Higher {feature.replace('_', ' ')} ({value:.2f} vs human avg {human_mean:.2f}) "
                f"suggests AI patterns"
            )
        else:
            insight = (
                f"Lower {feature.replace('_', ' ')} ({value:.2f} vs human avg {human_mean:.2f}) "
                f"suggests human patterns"
            )
        key_insights.append(insight)

    # Final conclusion - ALIGNED WITH ACTUAL PREDICTION
    conclusion = (
        "This text shows strong indicators of AI-generated content"
        if prediction["label"] == "AI"
        else "This text appears predominantly human-written"
    )

    # Add confidence qualifier
    if prediction["confidence"] < 0.7:
        conclusion += ", though with some uncertainty"
    elif prediction["confidence"] > 0.9:
        conclusion += " with high confidence"

    return {
        "key_insights": key_insights,
        "conclusion": conclusion,
        "research_basis": "Analysis based on linguistic patterns from academic research",
    }


def analyze_text(text, explain=False):
    """Main API endpoint for text analysis"""
    prediction = predict(text)

    if not explain:
        return {"prediction": prediction}

    try:
        features = extract_linguistic_features(text)
        explanation = generate_explanation(prediction, features)
        return {"prediction": prediction, "explanation": explanation}
    except Exception as e:
        return {
            "prediction": prediction,
            "error": f"Explanation generation failed: {str(e)}",
        }
