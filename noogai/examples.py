#!/usr/bin/env python3
"""
CommentSense Examples

This script shows how to use individual components of the CommentSense system.
"""

import warnings
warnings.filterwarnings('ignore')

from model import (
    Dataset, 
    AdvancedTextPreprocessor, 
    SentimentAnalyzer,
    RelevanceAnalyzer,
    CommentAnalytics
)


def example_text_preprocessing():
    """Example of text preprocessing"""
    print("🔧 Text Preprocessing Example")
    print("-" * 30)
    
    preprocessor = AdvancedTextPreprocessor()
    
    sample_text = "OMG this mascara is AMAZING!!! 😍 Love love love it! #bestmascara #makeup"
    
    # Clean text
    cleaned = preprocessor.clean_text(sample_text)
    print(f"Original: {sample_text}")
    print(f"Cleaned:  {cleaned}")
    
    # Detect spam
    spam_score = preprocessor.detect_spam(sample_text)
    print(f"Spam Score: {spam_score} ({'Spam' if spam_score else 'Legitimate'})")
    
    # Categorize
    category = preprocessor.categorize_comment(sample_text)
    print(f"Category: {category}")
    
    # Assess quality
    quality = preprocessor.assess_quality(sample_text, sentiment="positive")
    print(f"Quality: {quality} ({'High' if quality else 'Low'})")
    
    print()


def example_sentiment_analysis():
    """Example of sentiment analysis"""
    print("😊 Sentiment Analysis Example")
    print("-" * 30)
    
    analyzer = SentimentAnalyzer()
    
    sample_comments = [
        "I love this product so much!",
        "This is terrible, waste of money",
        "It's okay, nothing special",
        "Best purchase ever! Highly recommend!"
    ]
    
    sentiments, scores = analyzer.analyze_sentiment(sample_comments)
    
    for comment, sentiment, score in zip(sample_comments, sentiments, scores):
        print(f"Comment: \"{comment}\"")
        print(f"Sentiment: {sentiment} (confidence: {score:.3f})")
        print()


def example_relevance_analysis():
    """Example of relevance analysis"""
    print("🎯 Relevance Analysis Example")
    print("-" * 30)
    
    analyzer = RelevanceAnalyzer()
    
    video_title = "Best Foundation for Oily Skin - Review"
    video_description = "Testing the new foundation formula for oily and combination skin types"
    
    comments = [
        "Perfect for my oily skin! Thanks for the review",
        "What about dry skin? Does it work?",
        "First! Love your channel!",
        "The foundation coverage looks amazing"
    ]
    
    for comment in comments:
        relevance = analyzer.calculate_relevance_score(
            comment, video_title, video_description
        )
        print(f"Comment: \"{comment}\"")
        print(f"Relevance Score: {relevance:.3f}")
        print()


def example_quick_analysis():
    """Quick analysis example with small dataset"""
    print("⚡ Quick Analysis Example")
    print("-" * 30)
    
    # Load small sample
    dataset = Dataset()
    comments = dataset.getComments(dataset_id=1, sample_frac=0.005)  # 0.5% sample
    
    print(f"Analyzing {len(comments)} comments...")
    
    # Quick preprocessing
    preprocessor = AdvancedTextPreprocessor()
    comments["textCleaned"] = comments["textOriginal"].apply(preprocessor.clean_text)
    comments["isSpam"] = comments["textOriginal"].apply(preprocessor.detect_spam)
    comments["category"] = comments["textOriginal"].apply(preprocessor.categorize_comment)
    
    # Quick sentiment analysis (first 10 comments)
    analyzer = SentimentAnalyzer()
    sample_comments = comments["textCleaned"].head(10).tolist()
    sentiments, scores = analyzer.analyze_sentiment(sample_comments)
    comments.loc[:9, "sentiment"] = sentiments
    comments.loc[:9, "sentiment_score"] = scores
    
    # Quick analytics
    analytics = CommentAnalytics()
    
    print("\nQuick Stats:")
    print(f"- Total comments: {len(comments)}")
    print(f"- Spam rate: {comments['isSpam'].mean():.1%}")
    print(f"- Category breakdown: {dict(comments['category'].value_counts())}")
    print(f"- Sentiment (first 10): {dict(pd.Series(sentiments).value_counts())}")
    
    print("\nSample Comments:")
    for i, (_, row) in enumerate(comments.head(5).iterrows(), 1):
        print(f"{i}. \"{row['textOriginal'][:80]}...\"")
        print(f"   Category: {row['category']}, Spam: {'Yes' if row['isSpam'] else 'No'}")
        if pd.notna(row.get('sentiment')):
            print(f"   Sentiment: {row['sentiment']}")
        print()


if __name__ == "__main__":
    import pandas as pd
    
    print("CommentSense Examples")
    print("=" * 50)
    
    try:
        example_text_preprocessing()
        example_sentiment_analysis()
        example_relevance_analysis()
        example_quick_analysis()
        
        print("✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("Make sure all required packages are installed:")
        print("pip install pandas torch transformers scikit-learn plotly nltk")
