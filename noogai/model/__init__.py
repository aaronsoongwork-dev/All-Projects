"""
CommentSense: AI-Powered Comment Analysis System

This package provides tools for analyzing comment quality, sentiment, 
relevance, and engagement metrics at scale.
"""

from .dataset import Dataset
from .preprocessor import AdvancedTextPreprocessor
from .sentiment_analysis import SentimentAnalyzer
from .relevance_analysis import RelevanceAnalyzer
from .video_analysis import VideoAnalyzer
from .visualization import CommentAnalyticsDashboard
from .analytics import CommentAnalytics

__version__ = "1.0.0"
__author__ = "Noog Troupers"

__all__ = [
    'Dataset',
    'AdvancedTextPreprocessor',
    'SentimentAnalyzer',
    'RelevanceAnalyzer',
    'VideoAnalyzer',
    'CommentAnalyticsDashboard',
    'CommentAnalytics'
]
