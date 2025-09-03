
import pandas as pd
from collections import Counter
import re

# Load the data
df = pd.read_excel('review_crawling_raw.xlsx')

# --- Summarize Rating Distribution ---
rating_counts = df['rating'].value_counts().sort_index()
print("--- Rating Distribution ---")
for rating, count in rating_counts.items():
    print(f"Rating {rating}: {count} reviews")

# --- Summarize Word Cloud ---
text = " ".join(review for review in df.review.astype(str))
text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣]', '', text)
words = text.split()
word_counts = Counter(words)
most_common_words = word_counts.most_common(10)

print("\n--- Most Common Words in Reviews ---")
for word, count in most_common_words:
    print(f"'{word}': {count} times")

