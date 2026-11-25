
# AI-Generated Product Review Detection

An NLP and machine learning project investigating how AI-generated product reviews can be distinguished from human-written reviews. The project compares multiple model architectures, examines linguistic patterns across the two classes, and explores ways to make model predictions more understandable to users through a browser extension.

## Research Overview

The project investigates two related questions:

- **Detection:** How effectively can different machine learning approaches distinguish AI-generated reviews from human-written ones?
- **Interpretability:** What linguistic and stylistic patterns differentiate the two types of reviews, and how can these patterns help users understand model predictions?

Rather than focusing solely on classification performance, the project also examines differences in vocabulary, sentence structure, sentiment, readability, and other linguistic features.

## Dataset

The experiments use a dataset of **40,412 Amazon product reviews**, divided into two balanced classes:

| Label | Description | Samples |
|---|---|---:|
| CG | Computer-generated reviews | 20,206 |
| OR | Original human-written reviews | 20,206 |

Each sample includes the product category, rating, class label, and review text.

The dataset was split into training and test sets using an 80/20 split.

**Important limitation:** The dataset represents a specific distinction between computer-generated and original reviews. It should not be treated as a comprehensive representation of fraudulent reviews or all forms of AI-generated text.

## Model Comparison

I experimented with several approaches to compare their ability to distinguish the two classes.

| Model | Accuracy |
|---|---:|
| Logistic Regression | 86% |
| Linear SVC | 94% |
| Random Forest | 84% |
| XGBoost | 83% |
| GRU | 95% |
| LSTM | 93% |
| RoBERTa | 97% |
| RoBERTa + Label Smoothing | 98% |
| DeBERTa-v3 | 98% |

All results are based on the project's test split and should be interpreted within the limitations of the dataset.

### Key Findings

Transformer-based models achieved the strongest classification results, with RoBERTa using label smoothing and DeBERTa-v3 both reaching 98% accuracy.

Label smoothing was also explored as a way to reduce model overconfidence while maintaining classification performance.

## Linguistic Analysis

To better understand the differences between the two classes, I examined a range of linguistic and stylistic characteristics.

The analysis included:

- **Vocabulary:** Word frequency, lexical diversity, and class-associated phrases.
- **Sentence structure:** Sentence length, syntactic complexity, and grammatical patterns.
- **Sentiment:** Polarity, subjectivity, and emotional language.
- **Readability:** Flesch Reading Ease and Gunning Fog scores.
- **Language characteristics:** Part-of-speech distributions, pronoun usage, punctuation, and named entity density.
- **Language model analysis:** Perplexity measurements using GPT-2.

Statistical comparisons, including Welch's t-tests, were used to investigate differences between the classes.

### Observations

The analysis revealed several recurring tendencies:

- Human-written reviews were generally more personal and spontaneous, with greater use of first-person language.
- Computer-generated reviews tended to be longer and more structurally complex.
- Generated reviews showed higher lexical diversity and perplexity patterns that differed from original reviews.
- Differences also appeared in readability, punctuation, sentiment, and grammatical structure.

These findings describe patterns in the dataset rather than universal characteristics of human or AI-generated writing.

## Explainability

I explored explainability from two complementary angles.

### Model-level explainability

SHAP was used to investigate feature contributions in traditional machine learning models, particularly models trained on TF-IDF representations.

This provided a way to examine which words and phrases influenced individual predictions. However, the resulting SHAP values were relatively small, limiting how useful these explanations were in practice.

### Linguistic explanations

I also investigated whether measurable linguistic differences could provide more accessible explanations of model predictions.

This analysis informed the browser extension, which compares review characteristics with patterns observed in the two classes. It presents ranked indicators suggesting whether particular characteristics are more associated with human-written or computer-generated reviews.

These indicators are intended as supporting insights, not as definitive explanations of a model's internal reasoning.

## Browser Extension

The research was incorporated into a browser extension designed to make review analysis accessible to users.

The extension allows users to select review text and request an assessment through a FastAPI backend.

### Features

- Review classification using an ensemble of three models.
- Individual model confidence scores.
- Combined prediction based on weighted model probabilities.
- Linguistic analysis with accessible explanations.
- Review history and analysis management.

The ensemble combines a fine-tuned RoBERTa model with two publicly available Hugging Face models.

The extension was developed using JavaScript and integrates with the backend through FastAPI.

## Technologies

| Area | Technologies |
|---|---|
| Programming | Python, JavaScript |
| NLP | NLTK, spaCy, TextBlob |
| Machine Learning | scikit-learn, XGBoost |
| Deep Learning | PyTorch, Hugging Face Transformers |
| Explainability | SHAP |
| Backend | FastAPI |
| Browser Extension | JavaScript, HTML, CSS |
| Language Analysis | TextStat, GPT-2 |

## Limitations and Future Work

The project has several limitations:

- The dataset is limited to English-language Amazon product reviews.
- The generation process and labeling methodology are not sufficiently documented to establish how representative the generated reviews are of current AI systems.
- Detection performance may decrease when applied to reviews generated by newer or previously unseen language models.
- High classification confidence does not necessarily indicate a well-calibrated prediction.
- Linguistic patterns can overlap between human-written and AI-generated text, making individual predictions uncertain.

Future work could explore more diverse datasets, newer language models, improved probability calibration, and more robust explainability methods.

## Repository

This repository contains the implementation of the research project, including the machine learning experiments and browser extension.

