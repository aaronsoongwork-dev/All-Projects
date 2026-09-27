import pandas as pd
import torch
from transformers import pipeline
import warnings

warnings.filterwarnings('ignore')


class SentimentAnalyzer:
    def __init__(self, model_name="cardiffnlp/twitter-roberta-base-sentiment-latest"):
        """Initialize sentiment analyzer with specified model"""
        self.model_name = model_name
        self.device_index = 0 if torch.cuda.is_available() else -1
        
        print(f"Initializing sentiment analysis model: {self.model_name}")
        print(f"Using device: {'GPU' if self.device_index == 0 else 'CPU'}")
        
        self.analyzer = pipeline(
            "sentiment-analysis",
            model=self.model_name,
            truncation=True,
            device=self.device_index,
        )

    def analyze_sentiment(self, texts, batch_size=64):
        """Perform batch sentiment analysis on texts"""
        if isinstance(texts, str):
            texts = [texts]
        
        # Prepare texts for analysis
        texts_series = pd.Series(texts).fillna("").astype(str)
        unique_texts = list(pd.Series(texts_series.unique()))
        
        # Batch processing to avoid memory issues
        label_map = {}
        score_map = {}
        
        for i in range(0, len(unique_texts), batch_size):
            batch = unique_texts[i:i + batch_size]
            try:
                results = self.analyzer(batch, truncation=True, max_length=512)
                for text, result in zip(batch, results):
                    label_map[text] = result["label"]
                    score_map[text] = result["score"]
            except Exception as e:
                print(f"Error processing batch {i//batch_size + 1}: {e}")
                # Handle failed batch by assigning neutral sentiment
                for text in batch:
                    label_map[text] = "neutral"
                    score_map[text] = 0.5
        
        # Map results back
        sentiments = texts_series.map(label_map).tolist()
        scores = texts_series.map(score_map).tolist()
        
        return sentiments, scores

    def analyze_single_text(self, text):
        """Analyze sentiment of a single text"""
        try:
            result = self.analyzer(text, truncation=True, max_length=512)
            return result[0]["label"], result[0]["score"]
        except Exception as e:
            print(f"Error analyzing text: {e}")
            return "neutral", 0.5