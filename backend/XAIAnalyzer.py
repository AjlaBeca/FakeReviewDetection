import numpy as np
from collections import Counter
import re

class XAIAnalyzer:
    def __init__(self):
        self.confidence_thresholds = {
            "very_high": 0.9,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
        
    def generate_comprehensive_explanation(self, text, model_prediction, feature_attributions):
        """
        Generate a comprehensive explanation with automatic conclusions
        """
        # Analyze the evidence
        evidence_analysis = self._analyze_evidence(feature_attributions)
        
        # Generate linguistic analysis
        linguistic_analysis = self._analyze_linguistic_patterns(text)
        
        # Generate confidence assessment
        confidence_assessment = self._assess_confidence(model_prediction, evidence_analysis)
        
        # Generate final conclusion
        conclusion = self._generate_conclusion(
            model_prediction, 
            evidence_analysis, 
            linguistic_analysis, 
            confidence_assessment
        )
        
        return {
            "prediction": model_prediction,
            "confidence_level": confidence_assessment["level"],
            "evidence_summary": evidence_analysis,
            "linguistic_analysis": linguistic_analysis,
            "conclusion": conclusion,
            "reasoning_chain": self._build_reasoning_chain(
                evidence_analysis, linguistic_analysis, conclusion
            ),
            "alternative_explanations": self._generate_alternatives(
                model_prediction, evidence_analysis
            )
        }
    
    def _analyze_evidence(self, features):
        """
        Analyze the strength and direction of evidence from features
        """
        if not features:
            return {"strength": "insufficient", "direction": "unclear", "key_indicators": []}
        
        # Separate AI and human indicators
        ai_indicators = [f for f in features if f.get("indicates") == "AI" or f.get("indicates") == "CG"]
        human_indicators = [f for f in features if f.get("indicates") == "Human" or f.get("indicates") == "OR"]
        
        # Calculate evidence strength
        ai_strength = sum(abs(f["weight"]) for f in ai_indicators)
        human_strength = sum(abs(f["weight"]) for f in human_indicators)
        
        # Determine dominant direction
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
        
        # Identify key indicators
        all_features = sorted(features, key=lambda x: abs(x["weight"]), reverse=True)
        key_indicators = all_features[:3]
        
        return {
            "strength": self._categorize_strength(max(ai_strength, human_strength)),
            "direction": direction,
            "ai_evidence_count": len(ai_indicators),
            "human_evidence_count": len(human_indicators),
            "key_indicators": key_indicators,
            "evidence_balance": human_strength / (ai_strength + human_strength + 0.001)
        }
    
    def _analyze_linguistic_patterns(self, text):
        """
        Analyze linguistic patterns in the text
        """
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        # Calculate metrics
        avg_sentence_length = np.mean([len(s.split()) for s in sentences if s.strip()])
        sentence_length_variation = np.std([len(s.split()) for s in sentences if s.strip()])
        
        # Check for patterns
        has_contractions = any(word.lower() in ["can't", "won't", "don't", "isn't", "wasn't"] 
                             for word in words)
        
        exclamation_ratio = text.count('!') / len(text) if text else 0
        question_ratio = text.count('?') / len(text) if text else 0
        
        # Vocabulary analysis
        unique_words = len(set(word.lower() for word in words))
        lexical_diversity = unique_words / len(words) if words else 0
        
        # Emotional language detection
        emotional_words = ["love", "hate", "amazing", "terrible", "wonderful", "awful", 
                          "fantastic", "horrible", "brilliant", "stupid", "crazy", "weird"]
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
            "total_sentences": len([s for s in sentences if s.strip()])
        }
    
    def _assess_confidence(self, model_prediction, evidence_analysis):
        """
        Assess confidence in the prediction based on evidence
        """
        confidence_score = model_prediction.get("confidence", 0)
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
            "adjusted_confidence": adjusted_confidence,
            "level": level,
            "factors": self._identify_confidence_factors(evidence_analysis)
        }
    
    def _generate_conclusion(self, model_prediction, evidence_analysis, linguistic_analysis, confidence_assessment):
        """
        Generate an automatic conclusion based on all analyses
        """
        prediction_label = model_prediction.get("label", "Unknown")
        confidence_level = confidence_assessment["level"]
        evidence_direction = evidence_analysis["direction"]
        key_indicators = evidence_analysis["key_indicators"]
        
        # Build conclusion components
        conclusion_parts = []
        
        # Main prediction statement
        if prediction_label in ["AI", "CG"]:
            conclusion_parts.append(f"The text appears to be AI-generated with {confidence_level} confidence.")
        else:
            conclusion_parts.append(f"The text appears to be human-written with {confidence_level} confidence.")
        
        # Evidence summary
        if key_indicators:
            indicator_names = [ind["feature"] for ind in key_indicators[:2]]
            conclusion_parts.append(f"Key indicators include: {', '.join(indicator_names)}.")
        
        # Linguistic patterns
        if linguistic_analysis["has_contractions"]:
            conclusion_parts.append("The text shows natural human language patterns with contractions.")
        elif linguistic_analysis["sentence_variation"] < 3:
            conclusion_parts.append("The text shows uniform sentence structure typical of AI generation.")
        
        # Confidence qualifier
        if confidence_level == "low":
            conclusion_parts.append("However, the evidence is mixed and the prediction should be treated with caution.")
        elif confidence_level == "very_low":
            conclusion_parts.append("The evidence is insufficient for a reliable determination.")
        
        # Specific pattern insights
        if evidence_direction == "strongly_ai":
            conclusion_parts.append("Multiple AI-typical patterns reinforce this assessment.")
        elif evidence_direction == "mixed":
            conclusion_parts.append("The text contains both AI and human-like characteristics.")
        
        return " ".join(conclusion_parts)
    
    def _build_reasoning_chain(self, evidence_analysis, linguistic_analysis, conclusion):
        """
        Build a step-by-step reasoning chain
        """
        chain = []
        
        # Step 1: Evidence gathering
        chain.append({
            "step": 1,
            "description": "Evidence Analysis",
            "finding": f"Found {evidence_analysis['ai_evidence_count']} AI indicators and {evidence_analysis['human_evidence_count']} human indicators",
            "significance": "Establishes the foundation for classification"
        })
        
        # Step 2: Pattern recognition
        chain.append({
            "step": 2,
            "description": "Pattern Recognition",
            "finding": f"Text exhibits {evidence_analysis['direction'].replace('_', ' ')} characteristics",
            "significance": "Identifies dominant writing patterns"
        })
        
        # Step 3: Linguistic analysis
        chain.append({
            "step": 3,
            "description": "Linguistic Features",
            "finding": f"Sentence variation: {linguistic_analysis['sentence_variation']:.1f}, Contractions: {linguistic_analysis['has_contractions']}",
            "significance": "Reveals natural vs. artificial language use"
        })
        
        # Step 4: Confidence assessment
        chain.append({
            "step": 4,
            "description": "Confidence Evaluation",
            "finding": f"Overall confidence level: {evidence_analysis['strength']}",
            "significance": "Determines reliability of the prediction"
        })
        
        return chain
    
    def _generate_alternatives(self, model_prediction, evidence_analysis):
        """
        Generate alternative explanations
        """
        alternatives = []
        
        prediction_label = model_prediction.get("label", "Unknown")
        
        if prediction_label in ["AI", "CG"]:
            alternatives.append({
                "explanation": "Human author using formal writing style",
                "likelihood": "low" if evidence_analysis["direction"] == "strongly_ai" else "medium",
                "reasoning": "Formal language can sometimes mimic AI patterns"
            })
            
            alternatives.append({
                "explanation": "AI-assisted human writing",
                "likelihood": "medium",
                "reasoning": "Combination of human creativity with AI enhancement"
            })
        else:
            alternatives.append({
                "explanation": "AI trained on informal text",
                "likelihood": "low" if evidence_analysis["direction"] == "strongly_human" else "medium",
                "reasoning": "Modern AI can mimic casual human writing"
            })
            
            alternatives.append({
                "explanation": "Human writing in casual style",
                "likelihood": "high",
                "reasoning": "Natural human expression with informal language"
            })
        
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
            "linguistic_patterns": explanation["linguistic_analysis"]
        }
    }