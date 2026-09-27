#!/usr/bin/env python3
"""
CommentSense Main Analysis Pipeline

This script demonstrates how to use all the individual modules together
to perform comprehensive comment analysis.
"""

import warnings
warnings.filterwarnings('ignore')

from model import (
    Dataset, 
    AdvancedTextPreprocessor, 
    SentimentAnalyzer,
    RelevanceAnalyzer,
    VideoAnalyzer,
    CommentAnalyticsDashboard,
    CommentAnalytics
)


def run_full_analysis(sample_frac=0.01, dataset_id=1):
    """Run the complete comment analysis pipeline"""
    
    print("🚀 Starting CommentSense Analysis Pipeline")
    print("=" * 50)
    
    # 1. Load Data
    print("\n📁 Loading datasets...")
    dataset = Dataset()
    videos = dataset.getVideos()
    comments = dataset.getComments(dataset_id=dataset_id, sample_frac=sample_frac)
    
    print(f"   Loaded {len(videos)} videos and {len(comments)} comments")
    
    # Clean data
    comments = comments.drop_duplicates(subset=["commentId"])
    videos = videos.drop_duplicates(subset=["videoId"])
    comments = comments.dropna(subset=["textOriginal"])
    print(f"   After cleaning: {len(videos)} videos and {len(comments)} comments")
    
    # 2. Text Preprocessing
    print("\n🔧 Preprocessing text...")
    preprocessor = AdvancedTextPreprocessor()
    
    # Clean text
    comments["textCleaned"] = comments["textOriginal"].apply(preprocessor.clean_text)
    
    # Detect spam
    comments["isSpam"] = comments["textOriginal"].apply(preprocessor.detect_spam)
    
    # Categorize comments
    comments["category"] = comments["textOriginal"].apply(preprocessor.categorize_comment)
    
    print(f"   Spam comments detected: {comments['isSpam'].sum()} ({comments['isSpam'].mean()*100:.1f}%)")
    print(f"   Category distribution: {dict(comments['category'].value_counts())}")
    
    # 3. Sentiment Analysis
    print("\n😊 Analyzing sentiment...")
    sentiment_analyzer = SentimentAnalyzer()
    sentiments, scores = sentiment_analyzer.analyze_sentiment(comments["textCleaned"].tolist())
    comments["sentiment"] = sentiments
    comments["sentiment_score"] = scores
    
    print(f"   Sentiment distribution: {dict(pd.Series(sentiments).value_counts())}")
    
    # 4. Quality Assessment
    print("\n⭐ Assessing comment quality...")
    comments["quality_score"] = comments.apply(
        lambda row: preprocessor.assess_quality(row["textOriginal"], row["sentiment"]), axis=1
    )
    
    print(f"   High quality comments: {comments['quality_score'].sum()} ({comments['quality_score'].mean()*100:.1f}%)")
    
    # 5. Relevance Analysis
    print("\n🎯 Analyzing relevance...")
    relevance_analyzer = RelevanceAnalyzer()
    comments["relevance_score"] = relevance_analyzer.batch_relevance_analysis(comments, videos)
    
    print(f"   Average relevance score: {comments['relevance_score'].mean():.3f}")
    
    # 6. Analytics and KPIs
    print("\n📊 Calculating KPIs and generating insights...")
    analytics = CommentAnalytics()
    analytics.print_analysis_summary(comments)
    
    # 7. Video-level Analysis
    print("\n🎥 Analyzing video performance...")
    video_analyzer = VideoAnalyzer()
    video_stats = video_analyzer.get_video_analytics(comments)
    
    print("\nTop 5 Videos by Comment Count:")
    print(video_stats.head(5).to_string())
    
    # 8. Visualization
    print("\n📈 Creating visualizations...")
    dashboard = CommentAnalyticsDashboard()
    
    # Create and show key visualizations
    quality_fig = dashboard.create_quality_ratio_chart(comments)
    print("   ✅ Quality ratio chart created")
    
    sentiment_fig = dashboard.create_sentiment_breakdown(comments)
    print("   ✅ Sentiment breakdown created")
    
    category_fig = dashboard.create_category_breakdown(comments)
    print("   ✅ Category breakdown created")
    
    relevance_fig = dashboard.create_relevance_distribution(comments)
    print("   ✅ Relevance distribution created")
    
    # 9. Export Results
    print("\n💾 Exporting results...")
    summary_df = analytics.export_summary_report(comments, "comment_analysis_results.csv")
    video_stats.to_csv("video_analytics_summary.csv")
    
    print("   ✅ Results exported to CSV files")
    
    print("\n🎉 Analysis Complete!")
    print("   - comment_analysis_results.csv: Detailed comment analysis")
    print("   - video_analytics_summary.csv: Video-level analytics")
    
    return {
        'comments': comments,
        'videos': videos,
        'video_stats': video_stats,
        'figures': {
            'quality': quality_fig,
            'sentiment': sentiment_fig,
            'category': category_fig,
            'relevance': relevance_fig
        }
    }


def analyze_specific_video(video_id, comments_df):
    """Analyze a specific video in detail"""
    print(f"\n🔍 Detailed Analysis for Video: {video_id}")
    print("=" * 50)
    
    video_analyzer = VideoAnalyzer()
    analytics = CommentAnalytics()
    dashboard = CommentAnalyticsDashboard()
    
    # Get video-specific data
    video_data = comments_df[comments_df['videoId'] == video_id]
    
    if len(video_data) == 0:
        print("❌ No data found for this video ID")
        return None
    
    # Performance metrics
    metrics = video_analyzer.analyze_video_performance(comments_df, video_id)
    print(f"📊 Performance Metrics:")
    for key, value in metrics.items():
        if isinstance(value, dict):
            print(f"   {key}: {value}")
        else:
            print(f"   {key}: {value}")
    
    # Insights
    insights = video_analyzer.get_video_insights(comments_df, video_id)
    print(f"\n💡 Insights:")
    for insight in insights:
        print(f"   • {insight}")
    
    # Sample comments
    high_quality_comments = video_analyzer.get_sample_comments(
        comments_df, video_id, quality_filter='high', limit=3
    )
    
    print(f"\n⭐ Sample High-Quality Comments:")
    for i, (_, comment) in enumerate(high_quality_comments.iterrows(), 1):
        print(f"   {i}. [{comment['sentiment'].upper()}] (Relevance: {comment['relevance_score']:.3f})")
        print(f"      \"{comment['textOriginal'][:100]}...\"")
        print(f"      Category: {comment['category']}\n")
    
    # Create video-specific dashboard
    video_fig = dashboard.create_video_analysis_summary(comments_df, video_id)
    
    return {
        'metrics': metrics,
        'insights': insights,
        'sample_comments': high_quality_comments,
        'figure': video_fig
    }


if __name__ == "__main__":
    import pandas as pd
    
    print("CommentSense: AI-Powered Comment Analysis System")
    print("By: Noog Troupers")
    print("\n" + "=" * 60)
    
    # Run full analysis
    results = run_full_analysis(sample_frac=0.01, dataset_id=1)
    
    # Analyze top video in detail
    if len(results['video_stats']) > 0:
        top_video_id = results['video_stats'].index[0]
        video_analysis = analyze_specific_video(top_video_id, results['comments'])
    
    print("\n✨ All analyses completed successfully!")
