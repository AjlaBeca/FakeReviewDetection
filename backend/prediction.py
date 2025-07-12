import torch
import shap
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from collections import defaultdict
import XAIAnalyzer
import re
import json

# Load model and tokenizer globally
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_path = "../models/roberta_finetuned"
tokenizer_roberta = AutoTokenizer.from_pretrained(model_path)
model_roberta = AutoModelForSequenceClassification.from_pretrained(model_path).to(
    device
)
model_roberta.eval()

# Default temperature for scaling
TEMPERATURE = 2.5


# Custom JSON encoder for numpy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)


def convert_numpy_types(obj):
    """
    Recursively convert numpy types to native Python types
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


def predict_roberta(text, temperature=TEMPERATURE):
    inputs = tokenizer_roberta(
        text, return_tensors="pt", truncation=True, padding=True, max_length=256
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        logits = model_roberta(**inputs).logits
        scaled_logits = logits / temperature
        probs = torch.softmax(scaled_logits, dim=1)[0].cpu().numpy()
        predicted_class = probs.argmax()
        confidence = float(probs[predicted_class])
    label = "CG" if predicted_class == 0 else "OR"
    return {
        "label": label,
        "confidence": confidence,
        "class_probabilities": {"CG": float(probs[0]), "OR": float(probs[1])},
    }


def explain_roberta(text):
    """
    Provide meaningful explanations using gradient-based attribution
    """
    try:
        # Tokenize input
        # Tokenize and move to device
        inputs = tokenizer_roberta(
            text, return_tensors="pt", truncation=True, padding=True, max_length=256
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Extract tokens for display later
        tokens = tokenizer_roberta.convert_ids_to_tokens(inputs["input_ids"][0])

        # Get embeddings from input_ids
        input_ids = inputs["input_ids"]
        attention_mask = inputs["attention_mask"]

        # Get embeddings and set requires_grad = True for gradient-based XAI
        embeddings = model_roberta.roberta.embeddings.word_embeddings(input_ids)
        embeddings.requires_grad_(True)

        # Forward pass
        outputs = model_roberta.roberta(
            inputs_embeds=embeddings,
            attention_mask=inputs.get("attention_mask", None),
            token_type_ids=inputs.get("token_type_ids", None),
        )

        # Get classifier output
        logits = model_roberta.classifier(outputs.last_hidden_state)
        scaled_logits = logits / TEMPERATURE
        probs = torch.softmax(scaled_logits, dim=1)
        predicted_class = probs.argmax(dim=1).item()
        confidence = probs[0, predicted_class].item()

        # Get gradients w.r.t. embeddings
        score = logits[0, predicted_class]

        # Compute gradients
        gradients = torch.autograd.grad(
            outputs=score, inputs=embeddings, create_graph=False, retain_graph=False
        )[0]

        # Get attribution by taking L2 norm of gradients for each token
        attributions = torch.norm(gradients, dim=-1).squeeze().detach().cpu().numpy()

        # Process and return meaningful attributions
        meaningful_features = process_attributions_with_ngrams(
            tokens, attributions, predicted_class, confidence
        )

        # Convert numpy types to native Python types
        meaningful_features = convert_numpy_types(meaningful_features)

        return meaningful_features

    except Exception as e:
        print(f"Gradient explanation failed: {str(e)}")
        # Fall back to improved simple method
        return explain_roberta_simple_improved(text)


def explain_roberta_simple_improved(text):
    """
    Improved fallback explanation using actual words from the text
    """
    try:
        # Get prediction first
        prediction_result = predict_roberta(text)
        predicted_class = 0 if prediction_result["label"] == "CG" else 1
        confidence = prediction_result["confidence"]

        # Tokenize to get actual words
        inputs = tokenizer_roberta(
            text, return_tensors="pt", truncation=True, padding=True, max_length=256
        )
        tokens = tokenizer_roberta.convert_ids_to_tokens(inputs["input_ids"][0])

        # Clean tokens and combine subwords
        words = []
        current_word = ""

        for token in tokens:
            if token in ["<s>", "</s>", "<pad>", "<unk>"]:
                continue

            if token.startswith("Ġ"):
                if current_word:
                    words.append(current_word.strip())
                current_word = token[1:]  # Remove Ġ prefix
            else:
                current_word += token

        if current_word:
            words.append(current_word.strip())

        # Filter out short words and common words
        meaningful_words = [
            w
            for w in words
            if len(w) > 2
            and w.lower()
            not in [
                "the",
                "and",
                "for",
                "are",
                "but",
                "not",
                "you",
                "all",
                "can",
                "had",
                "her",
                "was",
                "one",
                "our",
                "out",
                "day",
                "get",
                "has",
                "him",
                "his",
                "how",
                "its",
                "may",
                "new",
                "now",
                "old",
                "see",
                "two",
                "who",
                "boy",
                "did",
                "man",
                "way",
                "too",
            ]
        ]

        # Create features from actual words in the text
        features = []

        # Define some pattern-based scoring
        cg_patterns = [
            "perfect",
            "amazing",
            "excellent",
            "outstanding",
            "incredible",
            "fantastic",
            "absolutely",
            "definitely",
            "highly",
            "recommend",
            "must-have",
            "flawless",
        ]

        or_patterns = [
            "okay",
            "fine",
            "decent",
            "alright",
            "pretty",
            "quite",
            "somewhat",
            "fairly",
            "rather",
            "maybe",
            "probably",
            "seems",
            "think",
            "feel",
        ]

        # Score words based on patterns and text characteristics
        for word in meaningful_words[:15]:  # Limit to top 15 words
            word_lower = word.lower().strip(".,!?")

            # Base score based on prediction
            base_score = 0.3 if predicted_class == 1 else -0.3

            # Adjust based on patterns
            if word_lower in cg_patterns:
                score = -0.7  # Strong CG indicator
                indicates = "CG"
            elif word_lower in or_patterns:
                score = 0.6  # Strong OR indicator
                indicates = "OR"
            else:
                # Use some heuristics based on word characteristics
                if len(word) > 8:  # Long words might be more human
                    score = base_score + 0.2
                elif word.isupper():  # ALL CAPS might be more CG
                    score = base_score - 0.3
                else:
                    score = base_score

                indicates = "OR" if score > 0 else "CG"

            features.append(
                {"feature": word, "weight": float(score), "indicates": indicates}
            )

        # If we don't have enough features, add the most meaningful ones
        if len(features) < 3:
            # Add most distinctive words from the text
            text_words = text.split()
            for word in text_words[:5]:
                if word.lower().strip(".,!?") not in [
                    f["feature"].lower() for f in features
                ]:
                    features.append(
                        {
                            "feature": word.strip(".,!?"),
                            "weight": 0.4 if predicted_class == 1 else -0.4,
                            "indicates": "OR" if predicted_class == 1 else "CG",
                        }
                    )

        # Sort by absolute weight and return top features
        features.sort(key=lambda x: abs(x["weight"]), reverse=True)

        # Convert numpy types to native Python types
        features = convert_numpy_types(features[:10])

        return features

    except Exception as e:
        print(f"Simple explanation failed: {str(e)}")
        return [{"feature": "unable_to_analyze", "weight": 0.0, "indicates": "CG"}]


# Updated process_attributions_with_ngrams function
def process_attributions_with_ngrams(
    tokens, attributions, predicted_class, confidence, top_k=10, max_n=3
):
    # Merge tokens into meaningful words
    words = []
    word_attributions = []
    current_word = ""
    current_attr = 0.0
    word_complete = False

    for i, (token, attr) in enumerate(zip(tokens, attributions)):
        # Skip special tokens
        if token in ["<s>", "</s>", "<pad>", "<unk>"]:
            continue

        # Handle word boundaries
        if token.startswith("Ġ") and current_word:
            words.append(current_word)
            word_attributions.append(current_attr)
            current_word = token[1:]
            current_attr = float(attr)  # Convert to float
            word_complete = True
        elif token in [".", ",", "!", "?"]:
            if current_word:
                words.append(current_word)
                word_attributions.append(current_attr)
            words.append(token)
            word_attributions.append(float(attr))  # Convert to float
            current_word = ""
            current_attr = 0.0
            word_complete = True
        else:
            current_word += token.replace("Ġ", " ")
            current_attr += float(attr)  # Convert to float
            word_complete = False

    if current_word:
        words.append(current_word)
        word_attributions.append(current_attr)

    # Filter out stop words and meaningless tokens
    STOP_WORDS = set(
        [
            "the",
            "a",
            "an",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "of",
            "and",
            "or",
            "but",
            "is",
            "are",
            "was",
            "were",
            "it",
            "that",
            "this",
        ]
    )
    meaningful_words = []
    meaningful_attrs = []

    for word, attr in zip(words, word_attributions):
        clean_word = word.strip(".,!?;:\"'()[]{}").lower()
        if (
            len(clean_word) > 2
            and clean_word not in STOP_WORDS
            and not clean_word.isdigit()
        ):
            meaningful_words.append(word)
            meaningful_attrs.append(attr)

    # Create n-grams with context-aware scoring
    ngram_features = []
    for n in range(1, max_n + 1):
        for i in range(len(meaningful_words) - n + 1):
            ngram = " ".join(meaningful_words[i : i + n])
            score = sum(meaningful_attrs[i : i + n]) / n  # Average score

            # Boost scores for meaningful phrases
            if n > 1:
                score *= 1.5

            # Penalize generic phrases
            if any(
                word in ["which", "that", "this", "there"] for word in ngram.split()
            ):
                score *= 0.7

            ngram_features.append(
                {
                    "feature": ngram,
                    "weight": float(score),  # Ensure it's a Python float
                    "indicates": "OR" if score > 0 else "CG",
                }
            )

    # Filter and sort features
    ngram_features = sorted(
        ngram_features, key=lambda x: abs(x["weight"]), reverse=True
    )

    # Remove duplicates and similar phrases
    unique_features = []
    seen_phrases = set()

    for feat in ngram_features:
        core_phrase = " ".join(
            [w for w in feat["feature"].split() if w not in STOP_WORDS]
        )
        if core_phrase not in seen_phrases:
            unique_features.append(feat)
            seen_phrases.add(core_phrase)

    return unique_features[:top_k]


# In your prediction.py file, fix the explain_text_with_xai function:


def explain_text_with_xai(text):
    """
    Generate comprehensive explanation using XAI analyzer
    """
    try:
        # Step 1: Get prediction from model
        model_prediction = predict_roberta(text)
        print(f"Model prediction: {model_prediction}")

        # Step 2: Get feature attributions for explanation
        feature_attributions = explain_roberta(text)
        print(f"Feature attributions type: {type(feature_attributions)}")
        print(
            f"Feature attributions length: {len(feature_attributions) if isinstance(feature_attributions, list) else 'N/A'}"
        )

        # Step 3: Initialize XAI analyzer
        from XAIAnalyzer import XAIAnalyzer

        xai_analyzer = XAIAnalyzer()

        # Step 4: Generate comprehensive explanation
        comprehensive_explanation = xai_analyzer.generate_comprehensive_explanation(
            text, model_prediction, feature_attributions
        )

        # Step 5: Convert numpy types
        comprehensive_explanation = convert_numpy_types(comprehensive_explanation)

        print(f"Generated explanation keys: {list(comprehensive_explanation.keys())}")
        return comprehensive_explanation

    except Exception as e:
        print(f"Error in explain_text_with_xai: {e}")
        import traceback

        traceback.print_exc()
        return {
            "error": str(e),
            "prediction": {"label": "Unknown", "confidence": 0.0},
            "conclusion": "Unable to generate explanation due to error",
        }


# Alternative simpler approach if the above doesn't work
def explain_text_simple(text):
    """
    Simple explanation without XAI analyzer
    """
    try:
        # Get prediction
        model_prediction = predict_roberta(text)

        # Get feature attributions
        feature_attributions = explain_roberta(text)

        # Create simple explanation structure
        explanation = {
            "prediction": model_prediction,
            "conclusion": f"The text appears to be {model_prediction['label']}-generated with {model_prediction['confidence']*100:.1f}% confidence.",
            "detailed_analysis": {
                "evidence_summary": {
                    "key_indicators": (
                        feature_attributions[:5]
                        if isinstance(feature_attributions, list)
                        else []
                    )
                }
            },
            "alternative_explanations": [
                {
                    "explanation": "Alternative interpretation available",
                    "reasoning": "Based on different model assumptions",
                    "likelihood": "medium",
                }
            ],
        }

        return convert_numpy_types(explanation)

    except Exception as e:
        print(f"Error in explain_text_simple: {e}")
        return {"error": str(e), "conclusion": "Unable to generate explanation"}
