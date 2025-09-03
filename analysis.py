
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import re

# Load the data
df = pd.read_excel('review_crawling_raw.xlsx')

# --- Rating Analysis and Visualization ---
plt.figure(figsize=(10, 6))
sns.countplot(x='rating', data=df, palette='viridis')
plt.title('Distribution of Ratings', fontsize=15)
plt.xlabel('Rating', fontsize=12)
plt.ylabel('Count', fontsize=12)
plt.savefig('rating_distribution.png')
print("Rating distribution bar chart saved as rating_distribution.png")


# --- Review Text Cleaning and Word Cloud ---
# Combine all reviews into a single string
text = " ".join(review for review in df.review.astype(str))

# Basic text cleaning (remove special characters and numbers)
# I will keep Korean characters and spaces.
text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣]', '', text)

# Path to a Korean font
font_path = 'c:/Windows/Fonts/malgun.ttf'

# Generate word cloud
try:
    wordcloud = WordCloud(width=800, height=400, background_color='white', font_path=font_path).generate(text)
    # Display and save the word cloud
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig('review_wordcloud.png')
    print("Review word cloud saved as review_wordcloud.png")
except Exception as e:
    print(f"Could not generate word cloud. Error: {e}")
    print("Trying to generate word cloud without Korean font support.")
    # Fallback without font path if the font is not found
    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.savefig('review_wordcloud_no_font.png')
    print("Review word cloud saved as review_wordcloud_no_font.png. Korean characters may not be displayed correctly.")
