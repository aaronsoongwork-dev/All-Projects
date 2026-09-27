import streamlit as st
import pandas as pd
from pathlib import Path
import requests
import os
import sys
dashboard_dir = Path(__file__).parent
sys.path.insert(0, str(dashboard_dir))
from helper import get_video_id, get_all_comments
from dotenv import load_dotenv
import asyncio

# Add the parent directory to the path to import model modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.preprocessor import AdvancedTextPreprocessor
from model.sentiment_analysis import SentimentAnalyzer
from model.relevance_analysis import RelevanceAnalyzer
from model.analytics import CommentAnalytics
from model.visualization import CommentAnalyticsDashboard

load_dotenv()

st.set_page_config(page_title="Dashboard", layout="wide", page_icon="📊")

leftcol, mid, rightcol = st.columns([1, 1, 1])
header_path = Path(__file__).resolve().parents[1] / "assets" / "header.png"
mid.image(header_path)
mid.header("NoogAI Video Comments Analysis")
st.sidebar.text("NoogAI Comments Analysis")
st.sidebar.success("View Sample Dataset Analysis for Demo Data.")

st.divider()

st.success("Welcome to the NoogAI YouTube Comments Analysis Dashboard! 🎉")
st.success("Enter a YouTube link to get started.")
st.success("Or use the Sample Dataset Analysis page for demo data.")

if "YOUTUBE_API_KEY" in os.environ:
    API_KEY = os.getenv("YOUTUBE_API_KEY")
else:
    st.warning("YOUTUBE_API_KEY environment variable not set. Please set a valid API key to use this application.", )
    st.stop()

with st.form("video_form"):
    link = st.text_input("Enter YouTube Video Link:", placeholder="https://www.youtube.com/watch?v=example")
    submitted = st.form_submit_button("Analyze")

if get_video_id(link) is None and submitted:
    st.error("Invalid YouTube Video URL. Please try again.")
    st.stop()
elif get_video_id(link) is None and not submitted:
    st.text("Awaiting YouTube Video URL input...")
    st.stop()
else:
    video_id = get_video_id(link)

# Get video details
video_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={video_id}&key={API_KEY}"
video_response = requests.get(video_url).json()

video_details = pd.DataFrame(columns=["Title", "Description", "Views", "Likes", "Comments"])
video_details["Title"] = [video_response["items"][0]["snippet"]["title"]]
video_details["Description"] = [video_response["items"][0]["snippet"]["description"]]
video_details["Views"] = [video_response["items"][0]["statistics"].get("viewCount", 0)]
video_details["Likes"] = [video_response["items"][0]["statistics"].get("likeCount", 0)]
video_details["Comments"] = [video_response["items"][0]["statistics"].get("commentCount", 0)]

st.header("Comments Data")
st.divider()

# Get comments (first 10000 comments - limit due to API constraints)
comments = pd.DataFrame.from_dict(get_all_comments(video_id, API_KEY, limit=10000))

# Basic Cleaning
st.write(f"Fetched {len(comments)} comments initially...")

# Remove duplicates
comments = comments.drop_duplicates(subset=["text"])

# Drop rows with missing comment text
comments = comments.dropna(subset=["text"])
st.write(f"After cleaning: {len(comments)} comments")

if len(comments) == 0:
    st.warning("No comments found for this video or comments are disabled.")
    st.stop()

# Perform comprehensive analysis
with st.spinner("Performing comprehensive comment analysis..."):
    
    try:
        # Initialize analyzers
        preprocessor = AdvancedTextPreprocessor()
        sentiment_analyzer = SentimentAnalyzer()
        relevance_analyzer = RelevanceAnalyzer()
        analytics = CommentAnalytics()
        dashboard = CommentAnalyticsDashboard()
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔄 Preprocessing text and detecting spam...")
        progress_bar.progress(20)
        
        # Clean text
        comments["textCleaned"] = comments["text"].apply(preprocessor.clean_text)
        
        # Detect spam
        comments["isSpam"] = comments["text"].apply(preprocessor.detect_spam)
        
        # Categorize comments
        comments["category"] = comments["text"].apply(preprocessor.categorize_comment)
        
        status_text.text("🎯 Analyzing sentiment...")
        progress_bar.progress(50)
        
        # Sentiment analysis
        sentiments, scores = sentiment_analyzer.analyze_sentiment(comments["textCleaned"].tolist())
        comments["sentiment"] = sentiments
        comments["sentiment_score"] = scores
        
        status_text.text("📊 Calculating relevance scores...")
        progress_bar.progress(70)
        
        # Create video data for relevance analysis
        video_data = pd.DataFrame({
            'videoId': [video_id],
            'title': [video_response["items"][0]["snippet"]["title"]],
            'description': [video_response["items"][0]["snippet"]["description"]],
            'tags': [" ".join(video_response["items"][0]["snippet"].get("tags", []))]
        })
        
        # Add videoId to comments for relevance analysis
        comments["videoId"] = video_id
        
        # Calculate relevance scores
        comments["relevance_score"] = relevance_analyzer.batch_relevance_analysis(comments, video_data)
        
        status_text.text("🔍 Assessing comment quality...")
        progress_bar.progress(90)
        
        # Quality assessment
        comments["quality_score"] = comments.apply(
            lambda row: preprocessor.assess_quality(row["text"], row["sentiment"]), axis=1
        )
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis completed!")
        
    except Exception as e:
        st.error(f"An error occurred during analysis: {str(e)}")
        st.write("Please try again with a different video or check your internet connection.")
        st.stop()

# Display results
st.subheader("📈 Analysis Results")

# Calculate KPIs
kpis = analytics.calculate_kpis(comments)

# Display KPIs in columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Comments", f"{kpis['Total Comments']:,}")
    st.metric("Quality Ratio", f"{kpis['Quality Comment Ratio']:.2%}")

with col2:
    st.metric("Spam Rate", f"{kpis['Spam Rate']:.2%}")
    st.metric("Avg Relevance", f"{kpis['Average Relevance Score']:.3f}")

with col3:
    st.metric("Positive Sentiment", f"{kpis['Positive Sentiment %']:.1f}%")
    st.metric("Negative Sentiment", f"{kpis['Negative Sentiment %']:.1f}%")

with col4:
    st.metric("Skincare Comments", f"{kpis['Skincare Comments %']:.1f}%")
    st.metric("Makeup Comments", f"{kpis['Makeup Comments %']:.1f}%")

# Generate insights
insights = analytics.generate_insights(comments)

st.subheader("💡 Key Insights")
for insight in insights:
    st.write(f"• {insight}")

# Visualizations
st.subheader("📊 Visualizations")

col1, col2 = st.columns(2)

with col1:
    # Quality ratio chart
    quality_fig = dashboard.create_quality_ratio_chart(comments)
    st.plotly_chart(quality_fig, use_container_width=True)
    
    # Category breakdown
    category_fig = dashboard.create_category_breakdown(comments)
    st.plotly_chart(category_fig, use_container_width=True)

with col2:
    # Sentiment breakdown
    sentiment_fig = dashboard.create_sentiment_breakdown(comments)
    st.plotly_chart(sentiment_fig, use_container_width=True)
    
    # Spam detection chart
    spam_fig = dashboard.create_spam_detection_chart(comments)
    st.plotly_chart(spam_fig, use_container_width=True)

# Relevance distribution (full width)
relevance_fig = dashboard.create_relevance_distribution(comments)
st.plotly_chart(relevance_fig, use_container_width=True)

# Sample high-quality comments
st.subheader("✨ Sample High-Quality Comments")

high_quality_comments = comments[
    (comments['quality_score'] == 1) &
    (comments['isSpam'] == 0)
].sort_values('relevance_score', ascending=False).head(5)

if len(high_quality_comments) > 0:
    for i, (_, comment) in enumerate(high_quality_comments.iterrows()):
        with st.expander(f"Comment {i+1} - {comment['sentiment'].upper()} (Relevance: {comment['relevance_score']:.3f})"):
            st.write(f"**Author:** {comment['author']}")
            st.write(f"**Category:** {comment['category']}")
            st.write(f"**Likes:** {comment['likes']}")
            st.write(f"**Text:** {comment['text']}")
else:
    st.write("No high-quality comments found.")

# Detailed data
st.subheader("📋 Detailed Analysis Data")

# Display video details
st.write("**Video Information:**")
st.dataframe(video_details, use_container_width=True)

# Export functionality
st.subheader("💾 Export Results")
if st.button("Download Analysis Results as CSV"):
    # Create comprehensive export dataframe
    export_df = comments[['author', 'text', 'textCleaned', 'sentiment', 'sentiment_score', 
                         'category', 'quality_score', 'isSpam', 'relevance_score', 'likes']].copy()
    
    # Add quality and spam labels for readability
    export_df['quality_label'] = export_df['quality_score'].map({0: 'Low Quality', 1: 'High Quality'})
    export_df['spam_label'] = export_df['isSpam'].map({0: 'Legitimate', 1: 'Spam'})
    
    # Convert to CSV
    csv = export_df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"video_{video_id}_analysis.csv",
        mime="text/csv"
    )

# Category-specific analysis
st.subheader("🎯 Category-Specific Analysis")
if len(comments) > 0:
    category_analysis = comments.groupby('category').agg({
        'quality_score': ['mean', 'count'],
        'sentiment': lambda x: (x == 'positive').mean(),
        'relevance_score': 'mean',
        'isSpam': 'mean'
    }).round(3)
    
    category_analysis.columns = ['Quality_Ratio', 'Comment_Count', 'Positive_Sentiment_Ratio', 'Avg_Relevance', 'Spam_Rate']
    st.dataframe(category_analysis, use_container_width=True)

# Display comments with analysis (with pagination for large datasets)
st.write("**Comments Analysis:**")
display_columns = ['author', 'text', 'sentiment', 'category', 'quality_score', 'isSpam', 'relevance_score', 'likes']

# Add filtering options
col1, col2, col3 = st.columns(3)
with col1:
    sentiment_filter = st.selectbox("Filter by Sentiment", ['All', 'positive', 'negative', 'neutral'])
with col2:
    category_filter = st.selectbox("Filter by Category", ['All'] + list(comments['category'].unique()))
with col3:
    quality_filter = st.selectbox("Filter by Quality", ['All', 'High Quality', 'Low Quality'])

# Apply filters
filtered_comments = comments.copy()
if sentiment_filter != 'All':
    filtered_comments = filtered_comments[filtered_comments['sentiment'] == sentiment_filter]
if category_filter != 'All':
    filtered_comments = filtered_comments[filtered_comments['category'] == category_filter]
if quality_filter == 'High Quality':
    filtered_comments = filtered_comments[filtered_comments['quality_score'] == 1]
elif quality_filter == 'Low Quality':
    filtered_comments = filtered_comments[filtered_comments['quality_score'] == 0]

st.write(f"Showing {len(filtered_comments)} of {len(comments)} comments")
if len(filtered_comments) > 0:
    st.dataframe(filtered_comments[display_columns], use_container_width=True)
else:
    st.write("No comments match the current filters.")

# Performance statistics
st.subheader("⚡ Processing Statistics")
processing_stats = {
    "Total Comments Processed": len(comments),
    "High Quality Comments": len(comments[comments['quality_score'] == 1]),
    "Spam Comments Detected": len(comments[comments['isSpam'] == 1]),
    "Comments with High Relevance (>0.3)": len(comments[comments['relevance_score'] > 0.3]),
    "Most Common Category": comments['category'].mode().iloc[0] if len(comments) > 0 else "N/A",
    "Most Common Sentiment": comments['sentiment'].mode().iloc[0] if len(comments) > 0 else "N/A"
}

for stat, value in processing_stats.items():
    st.write(f"• **{stat}:** {value}")

st.success("🎉 Analysis complete! The dashboard shows comprehensive insights based on the CommentSense AI methodology.")

# Summary section similar to notebook
st.subheader("📋 Analysis Summary")
st.write(f"""
**CommentSense AI Analysis Results**

This analysis processed **{len(comments):,} comments** from the video using advanced AI techniques including:

- **Text Preprocessing & Spam Detection**: Advanced natural language processing with beauty-specific categorization
- **Sentiment Analysis**: RoBERTa-based transformer model for accurate sentiment classification  
- **Relevance Scoring**: TF-IDF cosine similarity between comments and video content
- **Quality Assessment**: Multi-factor quality scoring based on length, relevance, sentiment, and engagement indicators
- **Beauty Category Classification**: Specialized classification for skincare, makeup, and fragrance content

**Key Findings:**
- Quality comment ratio: **{kpis['Quality Comment Ratio']:.1%}**
- Spam detection rate: **{kpis['Spam Rate']:.1%}**
- Average relevance score: **{kpis['Average Relevance Score']:.3f}**
- Dominant sentiment: **{comments['sentiment'].mode().iloc[0] if len(comments) > 0 else 'N/A'}** 
- Primary category: **{comments['category'].mode().iloc[0] if len(comments) > 0 else 'N/A'}**

This scalable analysis enables data-driven content strategy optimization and audience engagement insights.
""")


