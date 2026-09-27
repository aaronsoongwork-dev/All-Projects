import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import nltk
from sklearn.cluster import KMeans
from collections import Counter
import warnings

warnings.filterwarnings('ignore')

# Set style for better visualizations
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Download NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)


class VideoAnalyzer:
    """Handles video-level analytics and insights"""
    
    def __init__(self):
        self.colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
    
    def get_video_analytics(self, comments_df):
        """Generate per-video analytics"""
        video_stats = comments_df.groupby('videoId').agg({
            'commentId': 'count',
            'quality_score': 'mean',
            'isSpam': 'mean',
            'relevance_score': 'mean',
            'sentiment_score': 'mean'
        }).round(3)

        video_stats.columns = ['Total_Comments', 'Quality_Ratio', 'Spam_Rate', 'Avg_Relevance', 'Avg_Sentiment_Score']
        video_stats = video_stats.sort_values('Total_Comments', ascending=False)

        return video_stats
    
    def analyze_video_performance(self, comments_df, video_id):
        """Analyze performance metrics for a specific video"""
        video_data = comments_df[comments_df['videoId'] == video_id]
        
        if len(video_data) == 0:
            return None
        
        metrics = {
            'total_comments': len(video_data),
            'quality_ratio': video_data['quality_score'].mean(),
            'spam_rate': video_data['isSpam'].mean(),
            'avg_relevance': video_data['relevance_score'].mean(),
            'sentiment_breakdown': video_data['sentiment'].value_counts(normalize=True).to_dict(),
            'category_breakdown': video_data['category'].value_counts(normalize=True).to_dict(),
            'high_quality_comments': len(video_data[(video_data['quality_score'] == 1) & (video_data['isSpam'] == 0)])
        }
        
        return metrics
    
    def get_top_performing_videos(self, comments_df, metric='Quality_Ratio', top_n=10):
        """Get top performing videos based on specified metric"""
        video_stats = self.get_video_analytics(comments_df)
        return video_stats.nlargest(top_n, metric)
    
    def get_video_insights(self, comments_df, video_id):
        """Generate actionable insights for a specific video"""
        video_data = comments_df[comments_df['videoId'] == video_id]
        
        if len(video_data) == 0:
            return ["No data available for this video"]
        
        insights = []
        metrics = self.analyze_video_performance(comments_df, video_id)
        
        # Quality insights
        if metrics['quality_ratio'] < 0.3:
            insights.append(f"Low quality comment ratio ({metrics['quality_ratio']:.1%}). Content may not be resonating with audience.")
        elif metrics['quality_ratio'] > 0.6:
            insights.append(f"High quality comment ratio ({metrics['quality_ratio']:.1%}). Excellent audience engagement!")
        
        # Spam insights
        if metrics['spam_rate'] > 0.2:
            insights.append(f"High spam rate ({metrics['spam_rate']:.1%}). Consider improving comment moderation.")
        
        # Sentiment insights
        sentiment = metrics['sentiment_breakdown']
        positive_ratio = sentiment.get('positive', 0)
        negative_ratio = sentiment.get('negative', 0)
        
        if positive_ratio > 0.5:
            insights.append(f"Positive sentiment dominates ({positive_ratio:.1%}). Audience responds well to this content.")
        elif negative_ratio > 0.3:
            insights.append(f"High negative sentiment ({negative_ratio:.1%}). Consider reviewing content strategy.")
        
        # Relevance insights
        if metrics['avg_relevance'] < 0.1:
            insights.append(f"Low content relevance ({metrics['avg_relevance']:.3f}). Comments may be off-topic.")
        elif metrics['avg_relevance'] > 0.3:
            insights.append(f"High content relevance ({metrics['avg_relevance']:.3f}). Comments align well with video content.")
        
        return insights
    
    def compare_videos(self, comments_df, video_ids):
        """Compare performance metrics across multiple videos"""
        comparison_data = []
        
        for video_id in video_ids:
            metrics = self.analyze_video_performance(comments_df, video_id)
            if metrics:
                metrics['video_id'] = video_id
                comparison_data.append(metrics)
        
        return pd.DataFrame(comparison_data)
    
    def get_sample_comments(self, comments_df, video_id, quality_filter='high', limit=5):
        """Get sample comments from a video based on quality filter"""
        video_data = comments_df[comments_df['videoId'] == video_id]
        
        if quality_filter == 'high':
            filtered_data = video_data[
                (video_data['quality_score'] == 1) & 
                (video_data['isSpam'] == 0)
            ].sort_values('relevance_score', ascending=False)
        elif quality_filter == 'low':
            filtered_data = video_data[
                (video_data['quality_score'] == 0) | 
                (video_data['isSpam'] == 1)
            ].sort_values('relevance_score', ascending=True)
        else:
            filtered_data = video_data.sort_values('relevance_score', ascending=False)
        
        return filtered_data.head(limit)[['textOriginal', 'sentiment', 'category', 'relevance_score', 'quality_score', 'isSpam']]

