import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from pathlib import Path

# Add parent directory to path for model imports
parent_dir = Path(__file__).resolve().parents[2]
sys.path.append(str(parent_dir))

from model.visualization import CommentAnalyticsDashboard

st.set_page_config(page_title="Sample Dataset Analysis (comments1.csv)", layout="wide", page_icon="🤖")
st.sidebar.text("NoogAI Comments Analysis")

leftcol, mid, rightcol = st.columns([1, 1, 1])
header_path = Path(__file__).resolve().parents[2] / "assets" / "header.png"
mid.image(header_path)

# Title and introduction
st.markdown("<h1 style='text-align: center;'>NOOGAI: Sample Dataset Analysis</h1>", unsafe_allow_html=True)

st.divider()

st.markdown("""
<div style='text-align: center; margin-bottom: 30px;'>
<h3>NoogAI Comment Analysis System - Sample Results</h3>
<p><strong>Problem Statement</strong>: Measuring content effectiveness through Share of Engagement (SoE) metrics like likes, shares, saves, and comments is essential. How do we analyze the quality and relevance of comments, at scale?</p>
<p><strong>Solution</strong>: CommentSense provides a comprehensive AI-powered system for analyzing comment quality, sentiment, relevance, and engagement metrics.</p>
<p><em>By: <strong>Noog Troupers</strong></em></p>
</div>
""", unsafe_allow_html=True)

# Load pre-computed data
@st.cache_data
def load_data():
    try:
        # Load comment analysis results
        comments_df = pd.read_csv("https://storage.googleapis.com/dataset_hosting/results/comment1_analysis_results.csv")
        
        # Load video analytics summary
        video_analytics_df = pd.read_csv("https://storage.googleapis.com/dataset_hosting/results/video_analytics_summary.csv")
        
        return comments_df, video_analytics_df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

with st.spinner("Loading pre-computed analysis results..."):
    comments, video_analytics = load_data()

if comments is None or video_analytics is None:
    st.error("Could not load the required data files. Please ensure comment1_analysis_results.csv and video_analytics_summary.csv are available.")
    st.stop()

# Dataset overview
st.subheader("📊 Dataset Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Comments Analyzed", f"{len(comments):,}")
    
with col2:
    st.metric("Total Videos", f"{len(video_analytics):,}")
    
with col3:
    avg_comments_per_video = len(comments) / len(video_analytics)
    st.metric("Avg Comments/Video", f"{avg_comments_per_video:.0f}")
    
with col4:
    total_analyzed = len(comments) + len(video_analytics)
    st.metric("Total Data Points", f"{total_analyzed:,}")

# Key Performance Indicators (KPIs)
st.subheader("🎯 Key Performance Indicators (KPIs)")

def calculate_kpis(df):
    """Calculate key performance indicators matching the notebook"""
    total_comments = len(df)
    
    kpis = {
        'Total Comments': total_comments,
        'Quality Comment Ratio': df['quality_score'].mean(),
        'Spam Rate': df['isSpam'].mean(),
        'Average Relevance Score': df['relevance_score'].mean(),
        'Positive Sentiment %': (df['sentiment'] == 'positive').mean() * 100,
        'Negative Sentiment %': (df['sentiment'] == 'negative').mean() * 100,
        'Neutral Sentiment %': (df['sentiment'] == 'neutral').mean() * 100,
        'Skincare Comments %': (df['category'] == 'skincare').mean() * 100,
        'Makeup Comments %': (df['category'] == 'makeup').mean() * 100,
        'Fragrance Comments %': (df['category'] == 'fragrance').mean() * 100,
        'Other Comments %': (df['category'] == 'other').mean() * 100
    }
    
    return kpis

# Calculate KPIs
kpis = calculate_kpis(comments)

# Display KPIs in a structured layout
st.markdown("### Overall Analysis Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Quality Comment Ratio", f"{kpis['Quality Comment Ratio']:.2%}")
    st.metric("Spam Rate", f"{kpis['Spam Rate']:.2%}")

with col2:
    st.metric("Average Relevance Score", f"{kpis['Average Relevance Score']:.3f}")
    st.metric("Positive Sentiment", f"{kpis['Positive Sentiment %']:.1f}%")

with col3:
    st.metric("Negative Sentiment", f"{kpis['Negative Sentiment %']:.1f}%")
    st.metric("Neutral Sentiment", f"{kpis['Neutral Sentiment %']:.1f}%")

with col4:
    st.metric("Skincare Comments", f"{kpis['Skincare Comments %']:.1f}%")
    st.metric("Makeup Comments", f"{kpis['Makeup Comments %']:.1f}%")

# Initialize dashboard for visualizations
dashboard = CommentAnalyticsDashboard()

# Interactive Visualizations
st.subheader("📈 Interactive Dashboard")

# Row 1: Quality and Sentiment Analysis
col1, col2 = st.columns(2)

with col1:
    # Quality ratio chart
    quality_fig = dashboard.create_quality_ratio_chart(comments)
    st.plotly_chart(quality_fig, use_container_width=True)

with col2:
    # Sentiment breakdown
    sentiment_fig = dashboard.create_sentiment_breakdown(comments)
    st.plotly_chart(sentiment_fig, use_container_width=True)

# Row 2: Category and Spam Analysis
col1, col2 = st.columns(2)

with col1:
    # Category breakdown
    category_fig = dashboard.create_category_breakdown(comments)
    st.plotly_chart(category_fig, use_container_width=True)

with col2:
    # Spam detection chart
    spam_fig = dashboard.create_spam_detection_chart(comments)
    st.plotly_chart(spam_fig, use_container_width=True)

# Full width: Relevance distribution
relevance_fig = dashboard.create_relevance_distribution(comments)
st.plotly_chart(relevance_fig, use_container_width=True)

# Advanced Analytics and Insights - matching notebook methodology
st.subheader("🔍 Advanced Analytics and Insights")

def generate_insights(df):
    """Generate actionable insights from the data - matching notebook methodology"""
    insights = []

    # Quality insights
    quality_ratio = df['quality_score'].mean()
    if quality_ratio < 0.3:
        insights.append(f"⚠️ Low quality comment ratio ({quality_ratio:.1%}). Consider content strategy review.")
    elif quality_ratio > 0.6:
        insights.append(f"✅ High quality comment ratio ({quality_ratio:.1%}). Great audience engagement!")
    else:
        insights.append(f"📊 Moderate quality comment ratio ({quality_ratio:.1%}). Room for improvement.")

    # Spam insights
    spam_rate = df['isSpam'].mean()
    if spam_rate > 0.2:
        insights.append(f"🚨 High spam rate ({spam_rate:.1%}). Implement stricter comment moderation.")
    elif spam_rate < 0.05:
        insights.append(f"✅ Low spam rate ({spam_rate:.1%}). Excellent comment quality control.")
    else:
        insights.append(f"📊 Moderate spam rate ({spam_rate:.1%}). Monitor for trends.")

    # Sentiment insights
    positive_ratio = (df['sentiment'] == 'positive').mean()
    negative_ratio = (df['sentiment'] == 'negative').mean()

    if positive_ratio > 0.5:
        insights.append(f"😊 Positive sentiment dominates ({positive_ratio:.1%}). Audience responds well to content.")
    elif negative_ratio > 0.3:
        insights.append(f"😟 High negative sentiment ({negative_ratio:.1%}). Review content strategy.")
    else:
        insights.append(f"😐 Balanced sentiment distribution. Neutral audience response.")

    # Category insights
    top_category = df['category'].value_counts().index[0]
    top_category_pct = df['category'].value_counts(normalize=True).iloc[0]
    insights.append(f"🏷️ '{top_category}' is the dominant category ({top_category_pct:.1%} of comments).")

    # Relevance insights
    avg_relevance = df['relevance_score'].mean()
    if avg_relevance < 0.1:
        insights.append(f"📝 Low content relevance ({avg_relevance:.3f}). Comments may be off-topic.")
    elif avg_relevance > 0.3:
        insights.append(f"🎯 High content relevance ({avg_relevance:.3f}). Comments align well with video content.")
    else:
        insights.append(f"📊 Moderate content relevance ({avg_relevance:.3f}). Some alignment with video topics.")

    return insights

# Generate and display insights
insights = generate_insights(comments)

st.markdown("### 💡 Key Insights and Recommendations")
for insight in insights:
    st.write(f"• {insight}")

# Per-Video Analytics
st.subheader("🎬 Top Videos by Comment Volume")

# Display top 10 videos by comment count from video analytics
top_videos = video_analytics.head(10)

st.dataframe(
    top_videos.round(3),
    use_container_width=True,
    column_config={
        "videoId": "Video ID",
        "Total_Comments": st.column_config.NumberColumn("Total Comments", format="%d"),
        "Quality_Ratio": st.column_config.ProgressColumn("Quality Ratio", min_value=0, max_value=1),
        "Spam_Rate": st.column_config.ProgressColumn("Spam Rate", min_value=0, max_value=1),
        "Avg_Relevance": st.column_config.NumberColumn("Avg Relevance", format="%.3f"),
        "Avg_Sentiment_Score": st.column_config.NumberColumn("Avg Sentiment Score", format="%.3f")
    }
)

# Category-specific Analysis
st.subheader("🎯 Category-Specific Analysis")

if len(comments) > 0:
    category_analysis = comments.groupby('category').agg({
        'quality_score': ['mean', 'count'],
        'sentiment': lambda x: (x == 'positive').mean(),
        'relevance_score': 'mean',
        'isSpam': 'mean'
    }).round(3)
    
    category_analysis.columns = ['Quality_Ratio', 'Comment_Count', 'Positive_Sentiment_Ratio', 'Avg_Relevance', 'Spam_Rate']
    
    st.dataframe(
        category_analysis,
        use_container_width=True,
        column_config={
            "Quality_Ratio": st.column_config.ProgressColumn("Quality Ratio", min_value=0, max_value=1),
            "Comment_Count": st.column_config.NumberColumn("Comment Count", format="%d"),
            "Positive_Sentiment_Ratio": st.column_config.ProgressColumn("Positive Sentiment", min_value=0, max_value=1),
            "Avg_Relevance": st.column_config.NumberColumn("Avg Relevance", format="%.3f"),
            "Spam_Rate": st.column_config.ProgressColumn("Spam Rate", min_value=0, max_value=1)
        }
    )

# Sample High-Quality Comments
st.subheader("✨ Sample High-Quality Comments")

high_quality_comments = comments[
    (comments['quality_score'] == 1) &
    (comments['isSpam'] == 0)
].sort_values('relevance_score', ascending=False).head(5)

if len(high_quality_comments) > 0:
    for i, (_, comment) in enumerate(high_quality_comments.iterrows()):
        with st.expander(f"High-Quality Comment {i+1} - {comment['sentiment'].upper()} (Relevance: {comment['relevance_score']:.3f})"):
            st.write(f"**Video ID:** {comment['videoId']}")
            st.write(f"**Category:** {comment['category']}")
            st.write(f"**Sentiment Score:** {comment['sentiment_score']:.3f}")
            st.write(f"**Text:** {comment['textOriginal']}")
            st.write(f"**Cleaned Text:** {comment['textCleaned']}")
else:
    st.write("No high-quality comments found in the current dataset.")

# Export Results section
st.subheader("💾 Export and Data Access")

col1, col2 = st.columns(2)

with col1:
    if st.button("📥 Download Comment Analysis Results"):
        csv = comments.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="comment1_analysis_results.csv",
            mime="text/csv"
        )

with col2:
    if st.button("📥 Download Video Analytics Summary"):
        csv = video_analytics.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="video_analytics_summary.csv",
            mime="text/csv"
        )

# Final Summary
st.subheader("📋 Analysis Summary")

st.markdown(f"""
**CommentSense AI Analysis Results - Sample Dataset**

This analysis processed **{len(comments):,} comments** from **{len(video_analytics):,} videos** using advanced AI techniques including:

- **Text Preprocessing & Spam Detection**: Advanced natural language processing with beauty-specific categorization
- **Sentiment Analysis**: RoBERTa-based transformer model for accurate sentiment classification  
- **Relevance Scoring**: TF-IDF cosine similarity between comments and video content
- **Quality Assessment**: Multi-factor quality scoring based on length, relevance, sentiment, and engagement indicators
- **Beauty Category Classification**: Specialized classification for skincare, makeup, and fragrance content

**Key Findings:**
- Quality comment ratio: **{kpis['Quality Comment Ratio']:.1%}**
- Spam detection rate: **{kpis['Spam Rate']:.1%}**
- Average relevance score: **{kpis['Average Relevance Score']:.3f}**
- Dominant sentiment: **{comments['sentiment'].mode().iloc[0] if len(comments) > 0 else 'N/A'}** ({kpis[f'{comments["sentiment"].mode().iloc[0].title()} Sentiment %']:.1f}%)
- Primary category: **{comments['category'].mode().iloc[0] if len(comments) > 0 else 'N/A'}** ({kpis[f'{comments["category"].mode().iloc[0].title()} Comments %']:.1f}%)

This scalable analysis enables data-driven content strategy optimization and audience engagement insights.

### 🚀 Features Demonstrated:
1. **Quality Comment Ratio Analysis** - Identifies high vs low quality comments based on multiple factors
2. **Sentiment Breakdown** - Positive, negative, neutral sentiment analysis per video
3. **Comment Categorization** - Skincare, makeup, fragrance, and other categories
4. **Spam Detection** - Advanced spam detection using multiple indicators
5. **Relevance Analysis** - Measures comment relevance to video content using cosine similarity
6. **Interactive Dashboard** - Visual analytics for easy interpretation
7. **Per-Video Analytics** - Detailed breakdown for each video
8. **KPI Tracking** - Key performance indicators for content effectiveness

*CommentSense: Transforming comment data into actionable insights for content strategy optimization.*
""")

st.success("🎉 Sample dataset analysis complete! This demonstrates the full CommentSense AI methodology using pre-computed results.")

# Processing Statistics
st.subheader("⚡ Processing Statistics")

processing_stats = {
    "Total Comments Processed": len(comments),
    "High Quality Comments": len(comments[comments['quality_score'] == 1]),
    "Spam Comments Detected": len(comments[comments['isSpam'] == 1]),
    "Comments with High Relevance (>0.3)": len(comments[comments['relevance_score'] > 0.3]),
    "Most Common Category": comments['category'].mode().iloc[0] if len(comments) > 0 else "N/A",
    "Most Common Sentiment": comments['sentiment'].mode().iloc[0] if len(comments) > 0 else "N/A",
    "Videos Analyzed": len(video_analytics),
    "Average Comments per Video": f"{len(comments) / len(video_analytics):.0f}"
}

for stat, value in processing_stats.items():
    st.write(f"• **{stat}:** {value}")