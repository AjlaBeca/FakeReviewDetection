import numpy as np
from collections import Counter
import re
import unicodedata


class XAIAnalyzer:
    def __init__(self):
        self.confidence_thresholds = {
            "very_high": 0.9,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4,
        }

        # Define AI and Human indicator patterns
        self.ai_patterns = [
            "optimize",
            "optimization",
            "efficiency",
            "solution",
            "ultimate",
            "seamless",
            "comprehensive",
            "innovative",
            "strategic",
            "leverage",
            "utilize",
            "facilitate",
            "implement",
            "enhance",
            "maximize",
            "streamline",
            "methodology",
            "framework",
            "paradigm",
            "synergy",
            "robust",
            "scalable",
            "cutting-edge",
            "state-of-the-art",
            "furthermore",
            "moreover",
            "additionally",
            "consequently",
            "therefore",
        ]

        self.human_patterns = [
            "i",
            "me",
            "my",
            "myself",
            "we",
            "us",
            "our",
            "love",
            "hate",
            "feel",
            "think",
            "believe",
            "guess",
            "probably",
            "maybe",
            "kinda",
            "sorta",
            "awesome",
            "amazing",
            "terrible",
            "weird",
            "crazy",
            "lol",
            "haha",
            "omg",
            "wtf",
            "tbh",
            "imo",
            "basically",
            "literally",
            "actually",
        ]

    def convert_numpy_types(self, obj):
        """
        Recursively convert numpy types to native Python types
        """
        if isinstance(obj, dict):
            return {key: self.convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj

    def generate_comprehensive_explanation(
        self, text, model_prediction, feature_attributions
    ):
        """
        Generate a comprehensive explanation with automatic conclusions
        """
        # Convert numpy types first
        model_prediction = self.convert_numpy_types(model_prediction)
        feature_attributions = self.convert_numpy_types(feature_attributions)

        # Analyze the evidence
        evidence_analysis = self._analyze_evidence(feature_attributions, text)

        # Generate linguistic analysis
        linguistic_analysis = self._analyze_linguistic_patterns(text)

        # Generate confidence assessment
        confidence_assessment = self._assess_confidence(
            model_prediction, evidence_analysis
        )

        # Generate final conclusion
        conclusion = self._generate_conclusion(
            model_prediction,
            evidence_analysis,
            linguistic_analysis,
            confidence_assessment,
            text,
        )

        result = {
            "prediction": model_prediction,
            "confidence_level": confidence_assessment["level"],
            "evidence_summary": evidence_analysis,
            "linguistic_analysis": linguistic_analysis,
            "conclusion": conclusion,
            "reasoning_chain": self._build_reasoning_chain(
                evidence_analysis,
                linguistic_analysis,
                conclusion,
                confidence_assessment,
            ),
            "alternative_explanations": self._generate_alternatives(
                model_prediction, evidence_analysis
            ),
            "summary": self._generate_summary(
                model_prediction.get("label"),
                confidence_assessment["level"],
                evidence_analysis.get("direction", "unclear"),
            ),
        }

        # Convert all numpy types in the final result
        return self.convert_numpy_types(result)

    def _clean_feature_text(self, text):
        try:
            # Decode known encoding issues, normalize characters
            cleaned = (
                text.encode("latin1", "ignore")
                .decode("utf-8", "ignore")
                .replace("Â", "")
                .replace("â", "")
            )
            cleaned = unicodedata.normalize("NFKD", cleaned)
            return cleaned
        except:
            return text

    def _classify_feature_indicator(self, feature_text, weight, model_prediction_label):
        """
        Classify whether a feature indicates AI or Human authorship
        """
        text_lower = feature_text.lower()

        # Check for AI patterns
        ai_score = sum(1 for pattern in self.ai_patterns if pattern in text_lower)

        # Check for Human patterns
        human_score = sum(1 for pattern in self.human_patterns if pattern in text_lower)

        # Use model prediction and weight direction to inform classification
        predicted_ai = model_prediction_label in ["AI", "CG"]

        # If feature has positive weight and model predicts AI, it's likely an AI indicator
        # If feature has negative weight and model predicts AI, it's likely a Human indicator
        if ai_score > human_score:
            return "AI"
        elif human_score > ai_score:
            return "Human"
        else:
            # Use weight and model prediction as fallback
            if predicted_ai:
                return "AI" if weight > 0 else "Human"
            else:
                return "Human" if weight > 0 else "AI"

    def _analyze_evidence(self, features, text):
        """
        Analyze the strength and direction of evidence from features
        """
        if not features:
            return {
                "strength": "insufficient",
                "direction": "unclear",
                "ai_evidence_count": 0,
                "human_evidence_count": 0,
                "key_indicators": [],
                "evidence_balance": 0.5,
            }

        # Get model prediction for context
        model_prediction = getattr(self, "_current_prediction", {})
        model_label = model_prediction.get("label", "Unknown")

        # Clean and annotate features with 'indicates'
        enriched_features = []
        for f in features:
            feature = f.copy()
            feature["weight"] = float(feature["weight"])
            feature["feature"] = self._clean_feature_text(
                feature["feature"].replace("Ġ", " ")
            )

            # Classify the feature
            feature["indicates"] = self._classify_feature_indicator(
                feature["feature"], feature["weight"], model_label
            )

            enriched_features.append(feature)

        # Filter AI/Human features
        ai_indicators = [f for f in enriched_features if f["indicates"] == "AI"]
        human_indicators = [f for f in enriched_features if f["indicates"] == "Human"]

        ai_strength = sum(abs(f["weight"]) for f in ai_indicators)
        human_strength = sum(abs(f["weight"]) for f in human_indicators)

        # Determine direction
        if ai_strength > human_strength * 1.5:
            direction = "strongly_ai"
        elif human_strength > ai_strength * 1.5:
            direction = "strongly_human"
        elif ai_strength > human_strength:
            direction = "moderately_ai"
        elif human_strength > ai_strength:
            direction = "moderately_human"
        else:
            direction = "mixed"

        # Sort by impact
        sorted_features = sorted(
            enriched_features, key=lambda x: abs(x["weight"]), reverse=True
        )
        key_indicators = sorted_features[:3]

        return {
            "strength": self._categorize_strength(max(ai_strength, human_strength)),
            "direction": direction,
            "ai_evidence_count": len(ai_indicators),
            "human_evidence_count": len(human_indicators),
            "key_indicators": key_indicators,
            "evidence_balance": human_strength / (ai_strength + human_strength + 1e-6),
            "all_features": enriched_features,  # For debugging
        }

    def _analyze_linguistic_patterns(self, text):
        """
        Analyze linguistic patterns in the text
        """
        words = text.split()
        sentences = re.split(r"[.!?]+", text)

        # Calculate metrics
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        avg_sentence_length = (
            float(np.mean(sentence_lengths)) if sentence_lengths else 0.0
        )
        sentence_length_variation = (
            float(np.std(sentence_lengths)) if sentence_lengths else 0.0
        )

        # Check for patterns
        has_contractions = bool(re.search(r"\b\w+'\w+\b", text))

        exclamation_ratio = float(text.count("!") / len(text)) if text else 0.0
        question_ratio = float(text.count("?") / len(text)) if text else 0.0

        # Vocabulary analysis
        unique_words = len(set(word.lower() for word in words))
        lexical_diversity = float(unique_words / len(words)) if words else 0.0

        # Emotional language detection
        emotional_words = [
            "love",
            "hate",
            "amazing",
            "terrible",
            "wonderful",
            "awful",
            "fantastic",
            "horrible",
            "brilliant",
            "stupid",
            "crazy",
            "weird",
        ]
        emotional_count = sum(1 for word in words if word.lower() in emotional_words)

        return {
            "avg_sentence_length": avg_sentence_length,
            "sentence_variation": sentence_length_variation,
            "has_contractions": has_contractions,
            "exclamation_ratio": exclamation_ratio,
            "question_ratio": question_ratio,
            "lexical_diversity": lexical_diversity,
            "emotional_language": emotional_count,
            "total_words": len(words),
            "total_sentences": len([s for s in sentences if s.strip()]),
        }

    def _assess_confidence(self, model_prediction, evidence_analysis):
        """
        Assess confidence in the prediction based on evidence
        """
        confidence_score = float(model_prediction.get("confidence", 0))
        evidence_strength = evidence_analysis.get("strength", "low")
        evidence_direction = evidence_analysis.get("direction", "unclear")

        # Adjust confidence based on evidence consistency
        if evidence_direction in ["strongly_ai", "strongly_human"]:
            adjusted_confidence = min(confidence_score * 1.1, 1.0)
            level = "high"
        elif evidence_direction in ["moderately_ai", "moderately_human"]:
            adjusted_confidence = confidence_score
            level = "medium"
        elif evidence_direction == "mixed":
            adjusted_confidence = confidence_score * 0.8
            level = "low"
        else:
            adjusted_confidence = confidence_score * 0.6
            level = "very_low"

        return {
            "original_confidence": confidence_score,
            "adjusted_confidence": float(adjusted_confidence),
            "level": level,
            "factors": self._identify_confidence_factors(evidence_analysis),
        }

    def _generate_conclusion(
        self,
        model_prediction,
        evidence_analysis,
        linguistic_analysis,
        confidence_assessment,
        text,
    ):
        # Store current prediction for feature classification
        self._current_prediction = model_prediction

        prediction_label = model_prediction.get("label", "Unknown")
        confidence_level = confidence_assessment["level"]
        key_indicators = evidence_analysis["key_indicators"]

        # Build natural language explanation
        conclusion_parts = []

        # Confidence statement
        confidence_map = {
            "very_high": "high degree of certainty",
            "high": "strong confidence",
            "medium": "moderate confidence",
            "low": "some confidence",
            "very_low": "low confidence",
        }
        conf_phrase = confidence_map.get(confidence_level, "confidence")

        # Main prediction
        if prediction_label in ["AI", "CG"]:
            conclusion_parts.append(
                f"Our analysis indicates this text is <strong>AI-generated</strong> with {conf_phrase}."
            )
        else:
            conclusion_parts.append(
                f"Our analysis indicates this text is <strong>human-written</strong> with {conf_phrase}."
            )

        # Key evidence
        if key_indicators:
            indicator_desc = []
            # Get clean indicator phrases
            phrases = [i["feature"] for i in key_indicators]
            filtered_phrases = self._filter_redundant_ngrams(
                phrases, original_text=text
            )

            # Re-map indicators based on filtered phrases
            filtered_indicators = [
                i for i in key_indicators if i["feature"] in filtered_phrases
            ]

            for indicator in filtered_indicators:
                direction = (
                    "suggesting AI origin"
                    if indicator["indicates"] == "AI"
                    else "indicating human authorship"
                )
                indicator_desc.append(f"'{indicator['feature']}' ({direction})")

            if indicator_desc:
                conclusion_parts.append(
                    f"The key linguistic markers include: {', '.join(indicator_desc)}."
                )

        # Evidence summary
        ai_count = evidence_analysis["ai_evidence_count"]
        human_count = evidence_analysis["human_evidence_count"]
        conclusion_parts.append(
            f"Found {ai_count} AI indicators and {human_count} human indicators."
        )

        # Linguistic patterns
        if linguistic_analysis["lexical_diversity"] < 0.5:
            conclusion_parts.append(
                "The limited vocabulary diversity is characteristic of AI-generated content."
            )
        elif linguistic_analysis["lexical_diversity"] > 0.7:
            conclusion_parts.append(
                "The rich vocabulary diversity suggests human authorship."
            )

        if linguistic_analysis["emotional_language"] > 3:
            conclusion_parts.append(
                "The presence of emotional language is more typical of human writing."
            )

        # Confidence qualifier
        if confidence_level in ["low", "very_low"]:
            conclusion_parts.append(
                "This assessment should be considered with caution due to ambiguous linguistic signals."
            )

        return " ".join(conclusion_parts)

    def _filter_redundant_ngrams(self, phrases, original_text=None):
        """
        Remove overlapping, redundant, or odd n-grams.
        Keeps longest ones, optionally ensures they exist in original text.
        """
        cleaned = []
        text = original_text or ""

        for phrase in sorted(phrases, key=lambda x: -len(x)):
            # Skip if redundant
            if any(phrase in longer for longer in cleaned):
                continue

            # Skip if phrase not in original text or contains punctuation
            if original_text:
                if phrase not in original_text:
                    continue
                if re.search(r"[^\w\s']", phrase):  # allows apostrophes, blocks others
                    continue

            cleaned.append(phrase)
        return cleaned

    def _build_reasoning_chain(
        self, evidence_analysis, linguistic_analysis, conclusion, confidence_assessment
    ):
        """
        Build a step-by-step reasoning chain
        """
        chain = []

        # Step 1: Evidence gathering
        chain.append(
            {
                "step": 1,
                "description": "Evidence Analysis",
                "finding": f"Found {evidence_analysis['ai_evidence_count']} AI indicators and {evidence_analysis['human_evidence_count']} human indicators",
                "significance": "Establishes the foundation for classification",
            }
        )

        # Step 2: Pattern recognition
        chain.append(
            {
                "step": 2,
                "description": "Pattern Recognition",
                "finding": f"Text exhibits {evidence_analysis['direction'].replace('_', ' ')} characteristics",
                "significance": "Identifies dominant writing patterns",
            }
        )

        # Step 3: Linguistic analysis
        chain.append(
            {
                "step": 3,
                "description": "Linguistic Features",
                "finding": f"Sentence variation: {linguistic_analysis['sentence_variation']:.1f}, Contractions: {linguistic_analysis['has_contractions']}",
                "significance": "Reveals natural vs. artificial language use",
            }
        )

        # Step 4: Confidence assessment
        chain.append(
            {
                "step": 4,
                "description": "Confidence Evaluation",
                "finding": f"Overall confidence level: {confidence_assessment['level']}",
                "significance": "Determines reliability of the prediction",
            }
        )

        return chain

    def _generate_alternatives(self, model_prediction, evidence_analysis):
        """
        Generate alternative explanations
        """
        alternatives = []

        prediction_label = model_prediction.get("label", "Unknown")

        if prediction_label in ["AI", "CG"]:
            alternatives.append(
                {
                    "explanation": "Human author using formal writing style",
                    "likelihood": (
                        "low"
                        if evidence_analysis["direction"] == "strongly_ai"
                        else "medium"
                    ),
                    "reasoning": "Formal language can sometimes mimic AI patterns",
                }
            )

            alternatives.append(
                {
                    "explanation": "AI-assisted human writing",
                    "likelihood": "medium",
                    "reasoning": "Combination of human creativity with AI enhancement",
                }
            )
        else:
            alternatives.append(
                {
                    "explanation": "AI trained on informal text",
                    "likelihood": (
                        "low"
                        if evidence_analysis["direction"] == "strongly_human"
                        else "medium"
                    ),
                    "reasoning": "Modern AI can mimic casual human writing",
                }
            )

            alternatives.append(
                {
                    "explanation": "Human writing in casual style",
                    "likelihood": "high",
                    "reasoning": "Natural human expression with informal language",
                }
            )

        return alternatives

    def _categorize_strength(self, strength_value):
        """Categorize numerical strength into descriptive terms"""
        if strength_value > 3.0:
            return "very_strong"
        elif strength_value > 2.0:
            return "strong"
        elif strength_value > 1.0:
            return "moderate"
        else:
            return "weak"

    def _identify_confidence_factors(self, evidence_analysis):
        """Identify factors affecting confidence"""
        factors = []

        if evidence_analysis["ai_evidence_count"] > 3:
            factors.append("Multiple AI indicators present")

        if evidence_analysis["human_evidence_count"] > 3:
            factors.append("Multiple human indicators present")

        if evidence_analysis["direction"] == "mixed":
            factors.append("Conflicting evidence reduces confidence")

        if len(evidence_analysis["key_indicators"]) < 2:
            factors.append("Limited distinctive features")

        return factors

    def _generate_summary(self, label, confidence_level, direction):
        base = "This review is likely "
        label_text = "AI-generated" if label in ["AI", "CG"] else "human-written"

        if direction == "mixed":
            qualifier = "based on mixed linguistic signals"
        elif "strongly" in direction:
            qualifier = "based on strong linguistic patterns"
        else:
            qualifier = "with moderate textual indicators"

        return f"{base}{label_text} {qualifier} and {confidence_level} confidence."


# Usage example
def explain_with_xai(text, model_prediction, feature_attributions):
    """
    Generate comprehensive XAI explanation with automatic conclusions
    """
    xai_analyzer = XAIAnalyzer()

    # Get comprehensive explanation
    explanation = xai_analyzer.generate_comprehensive_explanation(
        text, model_prediction, feature_attributions
    )

    # Format for your API response
    return {
        "prediction": explanation["prediction"],
        "confidence": explanation["confidence_level"],
        "explanation": explanation["conclusion"],
        "reasoning_steps": explanation["reasoning_chain"],
        "alternative_explanations": explanation["alternative_explanations"],
        "detailed_analysis": {
            "evidence_summary": explanation["evidence_summary"],
            "linguistic_patterns": explanation["linguistic_analysis"],
        },
    }
