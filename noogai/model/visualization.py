import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class CommentAnalyticsDashboard:
    def __init__(self):
        self.colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']

    def create_quality_ratio_chart(self, df):
        """Create quality ratio visualization"""
        quality_counts = df['quality_score'].value_counts()

        fig = go.Figure(data=[
            go.Pie(labels=['Low Quality', 'High Quality'],
                   values=[quality_counts.get(0, 0), quality_counts.get(1, 0)],
                   hole=0.4,
                   marker_colors=['#FF6B6B', '#4ECDC4'])
        ])

        fig.update_layout(
            title="Comment Quality Ratio",
            annotations=[dict(text='Quality<br>Ratio', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )

        return fig

    def create_sentiment_breakdown(self, df):
        """Create sentiment breakdown visualization"""
        sentiment_counts = df['sentiment'].value_counts()

        fig = px.bar(x=sentiment_counts.index, y=sentiment_counts.values,
                     title="Sentiment Distribution",
                     labels={'x': 'Sentiment', 'y': 'Count'},
                     color=sentiment_counts.index,
                     color_discrete_sequence=self.colors)

        fig.update_layout(showlegend=False)
        return fig

    def create_category_breakdown(self, df):
        """Create category breakdown visualization"""
        category_counts = df['category'].value_counts()

        fig = px.pie(values=category_counts.values, names=category_counts.index,
                     title="Comment Categories",
                     color_discrete_sequence=self.colors)

        return fig

    def create_spam_detection_chart(self, df):
        """Create spam detection visualization"""
        spam_counts = df['isSpam'].value_counts()

        fig = go.Figure(data=[
            go.Bar(x=['Legitimate', 'Spam'],
                   y=[spam_counts.get(0, 0), spam_counts.get(1, 0)],
                   marker_color=['#4ECDC4', '#FF6B6B'])
        ])

        fig.update_layout(title="Spam Detection Results")
        return fig

    def create_relevance_distribution(self, df):
        """Create relevance score distribution"""
        fig = px.histogram(df, x='relevance_score',
                          title="Comment Relevance Score Distribution",
                          labels={'x': 'Relevance Score', 'y': 'Count'})

        fig.add_vline(x=df['relevance_score'].mean(), line_dash="dash",
                     annotation_text=f"Mean: {df['relevance_score'].mean():.3f}")

        return fig

    def create_video_analysis_summary(self, df, video_id):
        """Create per-video analysis summary"""
        video_data = df[df['videoId'] == video_id]

        if len(video_data) == 0:
            return None

        # Create subplot figure
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Quality Ratio', 'Sentiment Distribution',
                           'Category Breakdown', 'Relevance Scores'),
            specs=[[{'type': 'domain'}, {'type': 'xy'}],
                   [{'type': 'domain'}, {'type': 'xy'}]]
        )

        # Quality ratio pie chart
        quality_counts = video_data['quality_score'].value_counts()
        fig.add_trace(go.Pie(labels=['Low Quality', 'High Quality'],
                            values=[quality_counts.get(0, 0), quality_counts.get(1, 0)],
                            name="Quality"), row=1, col=1)

        # Sentiment bar chart
        sentiment_counts = video_data['sentiment'].value_counts()
        fig.add_trace(go.Bar(x=sentiment_counts.index, y=sentiment_counts.values,
                            name="Sentiment"), row=1, col=2)

        # Category pie chart
        category_counts = video_data['category'].value_counts()
        fig.add_trace(go.Pie(labels=category_counts.index, values=category_counts.values,
                            name="Category"), row=2, col=1)

        # Relevance histogram
        fig.add_trace(go.Histogram(x=video_data['relevance_score'], name="Relevance"),
                     row=2, col=2)

        fig.update_layout(height=800, title_text=f"Video Analysis Summary - {video_id}")

        return fig
