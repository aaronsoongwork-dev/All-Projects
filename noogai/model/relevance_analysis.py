import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RelevanceAnalyzer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english', ngram_range=(1, 2))

    def calculate_relevance_score(self, comment_text, video_title, video_description="", video_tags=""):
        """Calculate relevance score using cosine similarity"""
        try:
            # Combine video content
            video_content = f"{video_title} {video_description} {video_tags}".strip()

            if not comment_text or not video_content:
                return 0.0

            # Create TF-IDF vectors
            texts = [str(comment_text), str(video_content)]
            tfidf_matrix = self.vectorizer.fit_transform(texts)

            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

            return float(similarity)
        except:
            return 0.0

    def batch_relevance_analysis(self, comments_df, videos_df):
        """Perform batch relevance analysis"""
        # Merge comments with video data
        merged_df = comments_df.merge(videos_df[['videoId', 'title', 'description', 'tags']],
                                     on='videoId', how='left')

        # Calculate relevance scores
        relevance_scores = []
        for _, row in merged_df.iterrows():
            score = self.calculate_relevance_score(
                row.get('textOriginal', ''),
                row.get('title', ''),
                row.get('description', ''),
                row.get('tags', '')
            )
            relevance_scores.append(score)

        return relevance_scores