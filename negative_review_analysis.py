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
df_cleaned = df[~df['리뷰 내용'].str.contains('등록된 리뷰내용이 없습니다', na=False)]

# --- Negative/Neutral Review Analysis (1-3 stars) ---

# 1. Filter for reviews with rating <= 3
target_reviews = df_cleaned[df_cleaned['평점'] <= 3]
print(f"Found {len(target_reviews)} reviews with a rating of 1-3 stars.")

if len(target_reviews) > 0:
    # 2. Initialize Okt
    okt = Okt()

    # 3. Define stopwords
    stopwords = ['잘', '것', '많이', '더', '좀', '이', '그', '저', '수', '때', '같아요', '있는', '없는', '같습니다', '하고', '정말', '너무', '사용', '후', '입니다', '요', '제', '저']

    # 4. Extract nouns from reviews
    text = " ".join(review for review in target_reviews['리뷰 내용'].astype(str))
    nouns = okt.nouns(text)

    # 5. Manual Corrections
    corrected_nouns = ['아비브' if noun == '아비' else noun for noun in nouns]
    corrected_nouns = ['미끌' if noun == '밀끌' else noun for noun in corrected_nouns] # Added this line

    # 6. Filter out stopwords and single-character words
    filtered_nouns = [noun for noun in corrected_nouns if noun not in stopwords and len(noun) > 1]

    # 7. Count noun frequencies
    word_counts = Counter(filtered_nouns)
    top_keywords = word_counts.most_common(10)

    # 8. Print the review contents
    print("\n--- Reviews Content (1-3 stars) ---")
    for index, row in target_reviews.iterrows():
        print(f"Rating: {row['평점']}\nReview: {row['리뷰 내용']}\n---")


    # 9. Visualization
    if len(word_counts) > 0:
        # Word Cloud
        font_path = 'c:/Windows/Fonts/malgun.ttf'
        filtered_text = " ".join(filtered_nouns)
        try:
            wordcloud = WordCloud(width=800, height=400, background_color='white', font_path=font_path).generate(filtered_text)
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.savefig('reviews_1-3_stars_wordcloud_corrected.png')
            print("\nWord cloud for 1-3 star reviews saved as reviews_1-3_stars_wordcloud_corrected.png")
        except Exception as e:
            print(f"Could not generate word cloud. Error: {e}")

        # Bar Chart
        plt.figure(figsize=(12, 6))
        top_df = pd.DataFrame(top_keywords, columns=['Keyword', 'Frequency'])
        sns.barplot(x='Frequency', y='Keyword', data=top_df, palette='viridis')
        plt.title('Top Keywords in 1-3 Star Reviews (Corrected)', fontsize=15)
        plt.savefig('reviews_1-3_stars_top_keywords_corrected.png')
        print("Bar chart for 1-3 star reviews saved as reviews_1-3_stars_top_keywords_corrected.png")

        # Print top keywords
        print("\n--- Top Keywords in 1-3 Star Reviews (Corrected) ---")
        for word, count in top_keywords:
            print(f"'{word}': {count} times")
    else:
        print("\nNot enough data to generate visualizations.")

else:
    print("No reviews with a rating of 1-3 stars found.")
