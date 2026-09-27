import pandas as pd
import re
import string
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Optional imports for translation features (commented out by default)
from langdetect import detect
from googletrans import Translator
import asyncio

# Download NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)

class AdvancedTextPreprocessor:
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))

        # Beauty category keywords
        self.category_keywords = {
            'skincare': ['skincare', 'skin', 'moisturizer', 'cleanser', 'serum', 'cream', 'lotion',
                        'acne', 'pores', 'wrinkles', 'anti-aging', 'hydrating', 'dry skin', 'oily skin',
                        'sensitive skin', 'sunscreen', 'spf', 'retinol', 'vitamin c', 'hyaluronic',
                        'exfoliate', 'toner', 'mask', 'facial', 'dermatologist'],

            'makeup': ['makeup', 'foundation', 'concealer', 'lipstick', 'eyeshadow', 'mascara',
                      'eyeliner', 'blush', 'bronzer', 'highlighter', 'primer', 'setting spray',
                      'powder', 'contour', 'brow', 'eyebrow', 'lip gloss', 'lip liner', 'palette',
                      'brush', 'beauty blender', 'sponge', 'coverage', 'matte', 'dewy', 'shimmer'],

            'fragrance': ['perfume', 'fragrance', 'cologne', 'scent', 'smell', 'aroma', 'notes',
                         'floral', 'woody', 'citrus', 'vanilla', 'musk', 'fresh', 'sweet', 'spicy',
                         'eau de toilette', 'eau de parfum', 'body spray', 'long lasting',
                         'signature scent', 'top notes', 'base notes', 'middle notes']
        }

        # Spam indicators
        self.spam_keywords = [
            'buy now', 'click here', 'subscribe', 'free', 'visit', 'winner', 'win', 'cash', 'prize',
            'limited time', 'act now', 'urgent', 'amazing deal', 'check out my', 'follow me',
            'dm me', 'link in bio', 'promo code', 'discount', '50% off', 'sale'
        ]

    def clean_text(self, text):
        """Clean and preprocess text"""
        if pd.isna(text) or not isinstance(text, str):
            return ""

        # Convert to lowercase and strip
        text = str(text).lower().strip()

        # Remove URLs, mentions, hashtags
        text = re.sub(r'http\S+|www\S+|@\w+|#\w+', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Tokenize
        tokens = word_tokenize(text)

        # Remove stopwords and punctuation
        tokens = [word for word in tokens if word not in self.stop_words and word not in string.punctuation]

        # Stem tokens
        tokens = [self.stemmer.stem(word) for word in tokens if len(word) > 2]

        return ' '.join(tokens)

    async def translate_text(self, text):
        """Translate text to English"""
        # Detect if text is English, if so no translation needed
        try:
            if detect(text) == 'en':
                return text
        except Exception as e:
            return text

        # If the text is not English translate it to English
        async with Translator() as translator:
          try:
              translated_obj = await translator.translate(text, dest='en')
              return translated_obj.text
          except Exception as e:
              print(f"Translation error: {e}")
              return text

    async def batch_translate_text(self, texts, batch_size=100):
        """Translate a list of texts to English in batches"""
        translated_texts = []
        async with Translator() as translator:
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                try:
                    # Filter out empty strings or non-string types before translating
                    valid_batch = [text for text in batch if isinstance(text, str) and text.strip()]
                    if not valid_batch:
                        translated_texts.extend([""] * len(batch)) # Maintain original list length
                        continue

                    # Detect language for the first item as a proxy
                    lang = 'en'
                    try:
                        lang = detect(valid_batch[0])
                    except:
                        pass # Assume English if detection fails

                    if lang == 'en':
                        translated_texts.extend(batch)
                    else:
                        translated_batch_objs = await translator.translate(valid_batch, dest='en')
                        # Ensure translated texts align with the original batch, handling empty inputs
                        translated_results = []
                        valid_batch_idx = 0
                        for original_text in batch:
                            if isinstance(original_text, str) and original_text.strip():
                                translated_results.append(translated_batch_objs[valid_batch_idx].text)
                                valid_batch_idx += 1
                            else:
                                translated_results.append("") # Append empty string for invalid inputs
                        translated_texts.extend(translated_results)

                except Exception as e:
                    print(f"Batch translation error (batch {i//batch_size + 1}): {e}")
                    translated_texts.extend(batch) # Append original texts in case of error

        return translated_texts

    def detect_spam(self, text):
        """Detect spam comments with improved logic"""
        if pd.isna(text) or not isinstance(text, str):
            return 1

        text = str(text).lower()

        # Remove emojis for length check
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+", flags=re.UNICODE)

        text_no_emoji = emoji_pattern.sub('', text)

        # Check for very short comments (likely spam/low quality)
        if len(text_no_emoji.strip()) < 3:
            return 1

        # Check for excessive repetition
        words = text_no_emoji.split()
        if len(words) > 1 and len(set(words)) / len(words) < 0.5:
            return 1

        # Check for spam keywords
        spam_score = sum(1 for keyword in self.spam_keywords if keyword in text)
        if spam_score >= 2:
            return 1

        # Check for excessive caps
        if len(text) > 10 and sum(1 for c in text if c.isupper()) / len(text) > 0.7:
            return 1

        return 0

    def categorize_comment(self, text):
        """Categorize comments into beauty categories"""
        if pd.isna(text) or not isinstance(text, str):
            return 'other'

        text = str(text).lower()
        category_scores = {}

        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            category_scores[category] = score

        if max(category_scores.values()) == 0:
            return 'other'

        return max(category_scores.keys(), key=category_scores.get)

    def assess_quality(self, text, sentiment=None):
        """Assess comment quality based on multiple factors"""
        if pd.isna(text) or not isinstance(text, str):
            return 0

        text = str(text).lower()
        quality_score = 0

        # Length factor (reasonable length comments are better)
        word_count = len(text.split())
        if 5 <= word_count <= 50:
            quality_score += 2
        elif 3 <= word_count < 5 or 50 < word_count <= 100:
            quality_score += 1

        # Product relevance
        for keywords in self.category_keywords.values():
            if any(keyword in text for keyword in keywords):
                quality_score += 2
                break

        # Sentiment consideration
        if sentiment and sentiment != 'neutral':
            quality_score += 1

        # Engagement indicators
        engagement_words = ['love', 'amazing', 'recommend', 'favorite', 'best', 'great', 'good', 'bad', 'disappointed']
        if any(word in text for word in engagement_words):
            quality_score += 1

        # Quality threshold
        return 1 if quality_score >= 3 else 0