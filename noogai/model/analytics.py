import pandas as pd
import numpy as np
from collections import Counter


class CommentAnalytics:
    """Handles KPI calculations and insights generation"""
    
    def __init__(self):
        pass
    
    def calculate_kpis(self, df):
        """Calculate key performance indicators"""
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
    
    def generate_insights(self, df):
        """Generate actionable insights from the data"""
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
            insights.append(f"📊 Moderate spam rate ({spam_rate:.1%}). Monitor and improve moderation.")

        # Sentiment insights
        positive_ratio = (df['sentiment'] == 'positive').mean()
        negative_ratio = (df['sentiment'] == 'negative').mean()

        if positive_ratio > 0.5:
            insights.append(f"😊 Positive sentiment dominates ({positive_ratio:.1%}). Audience responds well to content.")
        elif negative_ratio > 0.3:
            insights.append(f"😟 High negative sentiment ({negative_ratio:.1%}). Review content strategy.")
        else:
            insights.append(f"😐 Mixed sentiment distribution. Monitor audience reactions closely.")

        # Category insights
        top_category = df['category'].value_counts().index[0]
        top_category_pct = df['category'].value_counts(normalize=True).iloc[0]
        insights.append(f"📊 '{top_category}' is the dominant category ({top_category_pct:.1%} of comments).")

        # Relevance insights
        avg_relevance = df['relevance_score'].mean()
        if avg_relevance < 0.1:
            insights.append(f"⚠️ Low content relevance ({avg_relevance:.3f}). Comments may be off-topic.")
        elif avg_relevance > 0.3:
            insights.append(f"✅ High content relevance ({avg_relevance:.3f}). Comments align well with video content.")
        else:
            insights.append(f"📊 Moderate content relevance ({avg_relevance:.3f}). Could improve topic alignment.")

        return insights
    
    def category_specific_analysis(self, df):
        """Perform category-specific quality analysis"""
        category_quality = df.groupby('category').agg({
            'quality_score': ['mean', 'count'],
            'sentiment': lambda x: (x == 'positive').mean(),
            'relevance_score': 'mean',
            'isSpam': 'mean'
        }).round(3)

        category_quality.columns = [
            'Quality_Ratio', 'Comment_Count', 
            'Positive_Sentiment_Ratio', 'Avg_Relevance', 'Spam_Rate'
        ]
        
        return category_quality.sort_values('Comment_Count', ascending=False)
    
    def engagement_analysis(self, df):
        """Analyze engagement patterns"""
        engagement_metrics = {
            'total_engagement': len(df),
            'quality_engagement': df['quality_score'].sum(),
            'legitimate_engagement': len(df[df['isSpam'] == 0]),
            'positive_engagement': len(df[df['sentiment'] == 'positive']),
            'category_engagement': df['category'].value_counts().to_dict(),
            'avg_relevance': df['relevance_score'].mean()
        }
        
        return engagement_metrics
    
    def generate_recommendations(self, df):
        """Generate specific recommendations based on analysis"""
        recommendations = []
        
        kpis = self.calculate_kpis(df)
        
        # Quality recommendations
        if kpis['Quality Comment Ratio'] < 0.4:
            recommendations.append("📝 Focus on creating more engaging content to improve comment quality")
            recommendations.append("🎯 Consider A/B testing different content formats")
        
        # Spam recommendations
        if kpis['Spam Rate'] > 0.15:
            recommendations.append("🛡️ Implement automated spam detection systems")
            recommendations.append("👥 Increase human moderation during peak hours")
        
        # Sentiment recommendations
        if kpis['Negative Sentiment %'] > 25:
            recommendations.append("💡 Review content strategy to address negative feedback")
            recommendations.append("🤝 Engage more actively with audience concerns")
        
        # Category recommendations
        dominant_category = df['category'].value_counts().index[0]
        if kpis[f'{dominant_category.title()} Comments %'] > 70:
            recommendations.append(f"🎨 Consider diversifying content beyond {dominant_category}")
            recommendations.append("📊 Explore cross-category content opportunities")
        
        # Relevance recommendations
        if kpis['Average Relevance Score'] < 0.2:
            recommendations.append("🎯 Improve video titles and descriptions for better relevance")
            recommendations.append("🏷️ Use more specific and targeted tags")
        
        return recommendations
    
    def export_summary_report(self, df, filename="comment_analysis_report.csv"):
        """Export comprehensive summary report"""
        # Create summary dataframe
        summary_df = df[[
            'videoId', 'commentId', 'textOriginal', 'textCleaned',
            'sentiment', 'sentiment_score', 'category',
            'quality_score', 'isSpam', 'relevance_score'
        ]].copy()

        # Add quality labels
        summary_df['quality_label'] = summary_df['quality_score'].map({0: 'Low Quality', 1: 'High Quality'})
        summary_df['spam_label'] = summary_df['isSpam'].map({0: 'Legitimate', 1: 'Spam'})
        
        # Save to CSV
        summary_df.to_csv(filename, index=False)
        
        return summary_df
    
    def print_analysis_summary(self, df):
        """Print a comprehensive analysis summary"""
        kpis = self.calculate_kpis(df)
        insights = self.generate_insights(df)
        recommendations = self.generate_recommendations(df)
        
        print("=" * 60)
        print("COMMENT ANALYSIS SUMMARY REPORT")
        print("=" * 60)
        
        print("\n📊 KEY PERFORMANCE INDICATORS:")
        print("-" * 40)
        for kpi, value in kpis.items():
            if '%' in kpi or 'Ratio' in kpi or 'Rate' in kpi or 'Score' in kpi:
                print(f"{kpi}: {value:.2f}%" if '%' in kpi else f"{kpi}: {value:.3f}")
            else:
                print(f"{kpi}: {value:,}")
        
        print("\n🔍 KEY INSIGHTS:")
        print("-" * 40)
        for insight in insights:
            print(f"• {insight}")
        
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 40)
        for rec in recommendations:
            print(f"• {rec}")
        
        print("\n📈 CATEGORY BREAKDOWN:")
        print("-" * 40)
        category_analysis = self.category_specific_analysis(df)
        print(category_analysis.to_string())
        
        print("\n" + "=" * 60)
        print("END OF REPORT")
        print("=" * 60)
