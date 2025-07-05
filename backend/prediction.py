import torch
import shap
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from collections import defaultdict
import XAIAnalyzer
import re

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
        return features[:10]

    except Exception as e:
        print(f"Simple explanation failed: {str(e)}")
        return [{"feature": "unable_to_analyze", "weight": 0.0, "indicates": "CG"}]


def process_attributions_with_ngrams(
    tokens, attributions, predicted_class, confidence, top_k=15, max_n=3
):
    """
    Merge subwords to words, then aggregate to n-grams (phrases),
    and return top weighted phrases for explanations.
    """
    # Step 1: Merge subwords into words and aggregate attributions
    words = []
    word_attributions = []

    current_word = ""
    current_attr = 0.0

    for token, attr in zip(tokens, attributions):
        if token in ["<s>", "</s>", "<pad>", "<unk>"]:
            continue

        if token.startswith("Ġ"):
            # Save previous word if exists
            if current_word:
                words.append(current_word)
                word_attributions.append(current_attr)
            current_word = token[1:]  # Remove Ġ prefix
            current_attr = attr
        else:
            current_word += token
            current_attr += attr

    # Add last word
    if current_word:
        words.append(current_word)
        word_attributions.append(current_attr)

    # Step 2: Create n-grams (1 to max_n)
    ngram_scores = defaultdict(float)

    for n in range(1, max_n + 1):
        for i in range(len(words) - n + 1):
            phrase_words = words[i : i + n]
            phrase = " ".join(phrase_words).strip()

            # Sum absolute attributions of words in this phrase
            score = sum(abs(word_attributions[j]) for j in range(i, i + n))

            ngram_scores[phrase] += score

    # Step 3: Sort ngrams by score descending
    sorted_ngrams = sorted(ngram_scores.items(), key=lambda x: x[1], reverse=True)

    # Step 4: Filter out very short phrases or unwanted tokens (optional)
    filtered_ngrams = [
        (phrase, score)
        for phrase, score in sorted_ngrams
        if len(phrase) > 2 and not re.search(r"[^a-zA-Z0-9 čćžšđČĆŽŠĐ]", phrase)
    ]

    # Step 5: Build output list with sign based on original attribution sum

    output = []
    for phrase, score in filtered_ngrams[:top_k]:
        # Get sign of sum of attributions for phrase to know direction (OR vs CG)
        # Find phrase start index
        phrase_words = phrase.split()
        indices = []
        for i in range(len(words) - len(phrase_words) + 1):
            if words[i : i + len(phrase_words)] == phrase_words:
                indices.append(i)
        if not indices:
            continue
        idx = indices[0]  # take first occurrence

        # Sum actual signed attributions (not abs)
        signed_sum = sum(
            word_attributions[j] for j in range(idx, idx + len(phrase_words))
        )

        output.append(
            {
                "feature": phrase,
                "weight": float(signed_sum),
                "indicates": "OR" if signed_sum > 0 else "CG",
            }
        )

    if not output:
        # fallback
        output.append(
            {
                "feature": words[0] if words else "text",
                "weight": 0.5 if predicted_class == 1 else -0.5,
                "indicates": "OR" if predicted_class == 1 else "CG",
            }
        )

    return output


def explain_text_with_xai(text):
    # Step 1: Get prediction from model
    model_prediction = predict_roberta(text)

    # Step 2: Get feature attributions for explanation
    feature_attributions = explain_roberta(text)

    # Step 3: Initialize your XAIAnalyzer
    xai_analyzer = XAIAnalyzer()

    # Step 4: Generate comprehensive explanation
    comprehensive_explanation = xai_analyzer.generate_comprehensive_explanation(
        text, model_prediction, feature_attributions
    )

    return comprehensive_explanation
