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
    "flesch": (86.60, 77.05),
    "gunning_fog": (6.29, 8.18),
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
        "flesch": flesch,
        "gunning_fog": gunning,
    }


def generate_explanation(prediction, features):
    """Generate explanation aligned with actual prediction using research-based thresholds"""
    key_insights = []

    # Define base weights per feature (can be tuned)
    base_weights = {
        "lexical_diversity": 0.8,
        "avg_sentence_length": 0.7,
        "flesch": 0.6,
        "gunning_fog": 0.6,
    }

    feature_weights = {}
    tolerance_ratio = 0.1  # 5% of human average is considered ambiguous

    for feature, (human_avg, ai_avg) in FEATURE_THRESHOLDS.items():
        value = features.get(feature)
        if value is None:
            continue

        human_diff = abs(value - human_avg)
        ai_diff = abs(value - ai_avg)
        tolerance = tolerance_ratio * human_avg

        if abs(human_diff - ai_diff) < tolerance:
            # Too close to distinguish reliably
            weight = 0.0
            insight = f"{feature.replace('_', ' ').capitalize()} is close to both human ({human_avg:.2f}) and AI ({ai_avg:.2f}) averages: ambiguous pattern"
        else:
            is_ai_like = ai_diff < human_diff
            weight = base_weights.get(feature, 0.5)
            weight = weight if is_ai_like else -weight
            direction = "Higher" if value > human_avg else "Lower"
            pattern = "AI patterns" if is_ai_like else "human patterns"
            insight = f"{direction} {feature.replace('_', ' ')} ({value:.2f} vs human avg {human_avg:.2f}) suggests {pattern}"

        feature_weights[feature] = weight
        key_insights.append({"feature": feature, "text": insight, "weight": weight})

    # Sort and limit top 5 impactful insights
    key_insights = sorted(key_insights, key=lambda x: abs(x["weight"]), reverse=True)[
        :5
    ]

    conclusion = (
        "This text shows strong indicators of AI-generated content."
        if prediction["label"] == "AI"
        else "This text appears predominantly human-written."
    )

    # Confidence qualifier
    if prediction["confidence"] < 0.7:
        conclusion += " However, the model expresses some uncertainty."
    elif prediction["confidence"] > 0.9:
        conclusion += " This assessment is made with high confidence."

    return {
        "key_insights": [
            {
                "text": i["text"],
                "type": (
                    "ambiguous"
                    if i["weight"] == 0
                    else "ai-pattern" if i["weight"] > 0 else "human-pattern"
                ),
                "icon": (
                    "❓" if i["weight"] == 0 else "🤖" if i["weight"] > 0 else "👤"
                ),
                "feature": i["feature"],
                "weight": i["weight"],
            }
            for i in key_insights
        ],
        "conclusion": conclusion,
        "research_basis": "Analysis based on linguistic patterns and statistical research findings.",
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


POSITIVE_PHRASES = {
    "great",
    "good",
    "excellent",
    "awesome",
    "perfect",
    "love",
    "nice",
    "glad",
    "like",
    "love",
    "cute",
    "stylish",
    "trendy",
    "great",
    "recommend",
    "best",
    "fantastic",
    "wonderful",
    "amazing",
    "superb",
    "outstanding",
    "fabulous",
    "terrific",
    "super",
    "fine",
    "pleasant",
    "satisfied",
    "happy",
    "delighted",
    "pleased",
    "impressed",
    "top",
    "exceptional",
    "incredible",
    "favorite",
    "admire",
    "enjoy",
    "smooth",
    "easy",
    "effective",
    "quality",
    "valuable",
    "worth",
    "beautiful",
    "brilliant",
    "cool",
    "decent",
    "splendid",
    "stellar",
    "satisfactory",
    "acceptable",
    "admirable",
    "first-class",
    "marvelous",
    "remarkable",
    "superior",
    "agreeable",
    "charming",
    "divine",
    "enjoyable",
    "favorable",
    "heavenly",
    "pleasurable",
    "satisfying",
    "positive",
    "loved",
    "fav",
    "prefer",
    "choice",
    "prime",
    "select",
    "premium",
    "optimal",
    "ideal",
    "suitable",
    "appreciated",
    "approved",
    "cherished",
    "esteemed",
    "prized",
    "treasured",
    "valued",
    "praise",
    "glowing",
    "enthusiastic",
    "encouraging",
    "supportive",
    "upbeat",
    "optimistic",
    "hopeful",
    "promising",
    "bright",
    "fortunate",
    "lucky",
}
