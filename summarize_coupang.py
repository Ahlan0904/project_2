
import pandas as pd
from collections import Counter
import re

# Load the data
df = pd.read_csv('Coupang-reviews/coupang_reviews.csv')

# Extract and clean text data
text = " ".join(review for review in df['리뷰 내용'].astype(str))
text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣]', '', text)

# Keyword Extraction (Word Frequency)
words = text.split()
word_counts = Counter(words)
top_keywords = word_counts.most_common(10)

print("--- Top 10 Keywords in Coupang Reviews ---")
for word, count in top_keywords:
    print(f"'{word}': {count} times")
