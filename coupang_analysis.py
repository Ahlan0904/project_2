import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from collections import Counter
import re
from konlpy.tag import Okt

# --- Set Font Globally for Matplotlib ---
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# Load the data
df = pd.read_csv('Coupang-reviews/coupang_reviews.csv')

# --- Data Cleaning ---
original_count = len(df)
df_cleaned = df[~df['리뷰 내용'].str.contains('등록된 리뷰내용이 없습니다', na=False)]
print(f"Removed {original_count - len(df_cleaned)} empty reviews.")
print(f"Analyzing {len(df_cleaned)} remaining reviews.")

# --- Keyword Analysis with Correction ---

# 1. Initialize Okt
okt = Okt()

# 2. Define stopwords
stopwords = ['잘', '것', '많이', '더', '좀', '이', '그', '저', '수', '때', '같아요', '있는', '없는', '같습니다', '하고', '정말', '너무', '사용', '후', '입니다', '요', '제', '저']

# 3. Extract nouns from the text
text = " ".join(review for review in df_cleaned['리뷰 내용'].astype(str))
nouns = okt.nouns(text)

# 4. Manual Correction
corrected_nouns = ['아비브' if noun == '아비' else noun for noun in nouns]

# 5. Filter out stopwords and single-character words
filtered_nouns = [noun for noun in corrected_nouns if noun not in stopwords and len(noun) > 1]

# 6. Count noun frequencies
word_counts = Counter(filtered_nouns)
top_keywords = word_counts.most_common(10)

# 7. Visualization

# Word Cloud
font_path = 'c:/Windows/Fonts/malgun.ttf'
filtered_text = " ".join(filtered_nouns)
try:
    wordcloud = WordCloud(width=800, height=400, background_color='white', font_path=font_path).generate(filtered_text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig('coupang_review_wordcloud_final_corrected.png')
    print("Corrected word cloud saved as coupang_review_wordcloud_final_corrected.png")
except Exception as e:
    print(f"Could not generate word cloud. Error: {e}")


# Bar Chart for Top 10 Keywords
plt.figure(figsize=(12, 6))
top_df = pd.DataFrame(top_keywords, columns=['Keyword', 'Frequency'])
sns.barplot(x='Frequency', y='Keyword', data=top_df, palette='viridis')
plt.title('Top 10 Keywords (Corrected)', fontsize=15)
plt.savefig('coupang_top_keywords_final_corrected.png')
print("Corrected top 10 keywords bar chart saved as coupang_top_keywords_final_corrected.png")

# Print top 10 keywords to console as well
print("\n--- Top 10 Keywords (Corrected) ---")
for word, count in top_keywords:
    print(f"'{word}': {count} times")
