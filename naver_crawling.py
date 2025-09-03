
import time
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import konlpy
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import PIL
import re

# --- 의존성 설치 안내 ---
# 이 스크립트를 실행하기 전에, 터미널에 아래 명령어를 입력하여 필요한 라이브러리를 설치해주세요.
# conda install pandas matplotlib seaborn selenium numpy wordcloud konlpy pillow openpyxl

# --- 사용자 설정 ---
target_url = "https://shopping.naver.com/window-products/beauty/12234269135"
sleep_delay = 1.5

# --- 데이터프레임 초기화 (날짜, 평점 컬럼 추가) ---
df = pd.DataFrame(columns=['date', 'rating', 'review'])

# --- 웹 드라이버 설정 ---
print("웹 드라이버를 설정합니다...")
options = webdriver.ChromeOptions()
# options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
service = Service(ChromeDriverManager().install())
browser = webdriver.Chrome(service=service, options=options)
print("드라이버 설정 완료.")

# --- 크롤링 시작 ---
try:
    browser.get(target_url)
    print(f"페이지로 이동: {target_url}")
    time.sleep(sleep_delay)

    print("리뷰 탭을 찾기 위해 스크롤합니다...")
    browser.execute_script("window.scrollTo(0, 800);")
    time.sleep(1)
    
    review_tab_selector = "//a[contains(text(), '리뷰')]"
    review_tab = WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, review_tab_selector)))
    browser.execute_script("arguments[0].click();", review_tab)
    print("리뷰 탭을 클릭했습니다.")
    time.sleep(sleep_delay)

    page_count = 1
    while True:
        print(f"--- {page_count} 페이지 리뷰 수집 시작 ---")
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.PxsZltB5tV")))
        review_elements = browser.find_elements(By.CSS_SELECTOR, "li.PxsZltB5tV")
        print(f"현재 페이지에서 {len(review_elements)}개의 리뷰를 찾았습니다.")
        
        for review_element in review_elements:
            date_text, rating_text, review_text = '', '', ''
            try:
                # 날짜, 평점, 리뷰 텍스트 수집
                date_text = review_element.find_element(By.CSS_SELECTOR, 'div.Db9Dtnf7gY > span.MX91DFZo2F').text
                rating_text = review_element.find_element(By.CSS_SELECTOR, 'em.n6zq2yy0KA').text
                review_text = review_element.find_element(By.CSS_SELECTOR, 'div.KqJ8Qqw082 span.MX91DFZo2F').text
                
                if review_text:
                    new_row = pd.DataFrame([{'date': date_text, 'rating': rating_text, 'review': review_text}])
                    df = pd.concat([df, new_row], ignore_index=True)
            except Exception:
                continue

        current_page_element = browser.find_element(By.CSS_SELECTOR, "a.hyY6CXtbcn[aria-current='true']")
        current_page = int(current_page_element.text)

        next_page = current_page + 1
        try:
            page_button_xpath = f"//a[contains(@class, 'hyY6CXtbcn') and text()='{next_page}']"
            page_button = WebDriverWait(browser, 2).until(EC.element_to_be_clickable((By.XPATH, page_button_xpath)))
            browser.execute_script("arguments[0].click();", page_button)
            print(f"{next_page} 페이지로 이동...")
            page_count += 1
            time.sleep(sleep_delay)
        except Exception:
            try:
                next_list_button_xpath = "//a[contains(text(), '다음')]"
                next_list_button = WebDriverWait(browser, 2).until(EC.element_to_be_clickable((By.XPATH, next_list_button_xpath)))
                browser.execute_script("arguments[0].click();", next_list_button)
                print("[다음 >] 목록으로 이동합니다.")
                page_count = (current_page // 10) * 10 + 1
                time.sleep(sleep_delay)
            except Exception:
                print("더 이상 다음 페이지가 없어 크롤링을 종료합니다.")
                break

finally:
    browser.quit()
    print("크롤링 완료. 브라우저를 종료합니다.")

# --- 데이터 저장 및 분석 ---
if not df.empty:
    df.drop_duplicates(inplace=True)
    print(f"총 {len(df)}개의 고유한 리뷰를 수집했습니다.")
    df.to_excel('review_crawling_raw.xlsx', index=False)
    print("review_crawling_raw.xlsx 파일 저장 완료.")

    def preprocessing(input_df):
        proc_df = input_df.copy()
        proc_df['one_month'] = proc_df['review'].apply(lambda x: "한달사용기" in str(x)[:8])
        proc_df['repeat_purchase'] = proc_df['review'].apply(lambda x: "재구매" in str(x)[:8])
        
        def clean_text(row):
            review = str(row['review'])
            if row['one_month']: review = review[5:]
            if row['repeat_purchase']: review = review[3:]
            return review.strip()
            
        proc_df['review'] = proc_df.apply(clean_text, axis=1)
        # 날짜와 평점도 함께 반환하도록 수정
        return proc_df[['date', 'rating', 'review', 'one_month', 'repeat_purchase']]

    prep_df = preprocessing(df)
    prep_df.to_excel('review_crawling_prep.xlsx', index=False)
    print("전처리 완료. review_crawling_prep.xlsx 파일 저장 완료.")

    print("형태소 분석을 시작합니다... (Okt, 명사/형용사 추출)")
    okt = konlpy.tag.Okt()
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False

    prep_df['review_cleaned'] = prep_df['review'].str.replace('[^가-힣a-zA-Z0-9]', ' ', regex=True)
    
    keywords = []
    for review in prep_df['review_cleaned']:
        if isinstance(review, str) and review.strip():
            pos_tagged = okt.pos(review, stem=True)
            for word, tag in pos_tagged:
                if tag in ['Noun', 'Adjective']:
                    keywords.append(word)

    if not keywords:
        print("분석할 키워드(명사, 형용사)가 없어 시각화 자료를 생성하지 않습니다.")
    else:
        df_word = pd.DataFrame({'word': keywords})
        df_word = df_word[df_word['word'].str.len() > 1]
        df_word['count'] = 1
        df_word = df_word.groupby('word', as_index=False).count().sort_values('count', ascending=False)
        print("형태소 분석 완료.")

        print("막대 그래프를 생성합니다...")
        top20 = df_word.head(20)
        plt.figure(figsize=(10, 8))
        sns.barplot(data=top20, y='word', x='count', palette='viridis')
        plt.title('리뷰 키워드 상위 20개 (명사/형용사)')
        plt.xlabel('빈도수')
        plt.ylabel('키워드')
        plt.savefig('naver_review_barPlot.png', dpi=300, bbox_inches='tight')
        print("naver_review_barPlot.png 저장 완료.")
        plt.close()

        print("워드클라우드를 생성합니다...")
        dic_word = df_word.set_index('word').to_dict()['count']
        
        wc = WordCloud(random_state=42, width=400, height=400, background_color='white', font_path='C:/Windows/Fonts/malgun.ttf')
        img_wordcloud = wc.generate_from_frequencies(dic_word)
        plt.figure(figsize=(10, 10))
        plt.axis('off')
        plt.imshow(img_wordcloud)
        plt.savefig('naver_review_wordCloud.png', dpi=300, bbox_inches='tight')
        print("naver_review_wordCloud.png 저장 완료.")
        plt.close()

    print("\n--- 모든 작업 완료 ---")
else:
    print("수집된 리뷰가 없어 분석을 진행하지 않습니다.")
