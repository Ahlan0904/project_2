from bs4 import BeautifulSoup as bs
from pathlib import Path
from openpyxl import Workbook
from fake_useragent import UserAgent
from requests.exceptions import RequestException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import os
import re
import requests as rq
import math
import sys
import csv


class ChromeDriver:
    def __init__(self) -> None:
        self.set_options()
        self.set_driver()

    def set_options(self) -> None:
        self.options = Options()
        #self.options.add_argument("--headless")
        self.options.add_argument("lang=ko_KR")
        self.options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.options.add_argument("--log-level=3")
        self.options.add_experimental_option("detach", True)
        self.options.add_experimental_option("excludeSwitches", ["enable-logging"])
    def set_driver(self) -> None:
        from selenium.webdriver.chrome.service import Service
        driver_path = os.path.join(os.getcwd(), "chromedriver.exe")
        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=self.options)


class Coupang:
    @staticmethod
    def get_product_code(url_or_id: str) -> str:
        # productId(제품번호)만 입력된 경우
        if url_or_id.isdigit():
            return url_or_id
        # URL이 입력된 경우
        elif "products/" in url_or_id:
            prod_code: str = url_or_id.split("products/")[-1].split("?")[0]
            return prod_code
        # 그냥 숫자 문자열인 경우
        return url_or_id

    @staticmethod
    def get_soup_object(resp: rq.Response) -> bs:
        return bs(resp.text, "html.parser")

    def __del__(self) -> None:
        if self.ch.driver:
            self.ch.driver.quit()

    def __init__(self) -> None:
        self.base_review_url: str = "https://www.coupang.com/vp/product/reviews"
        self.sd = SaveData()
        self.retries = 10
        self.delay = 0.5
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ko,en;q=0.9,en-US;q=0.8",
            "cookie": "_fbp=fb.1.1709172148924.2042270649; gd1=Y; delivery_toggle=false; srp_delivery_toggle=true; MARKETID=17272706554699560993959; x-coupang-accept-language=ko-KR;",
            "priority": "u=1, i",
            "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }
        self.ch = ChromeDriver()

    def get_product_info(self, prod_code: str) -> tuple:
        # productId로 직접 상품 페이지 접근
        url = f"https://www.coupang.com/vp/products/{prod_code}"
        self.ch.driver.get(url=url)
            
        WebDriverWait(self.ch.driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        page_source: str = self.ch.driver.page_source
        soup = bs(page_source, "html.parser")
        
        # 상품명 찾기 - 여러 셀렉터 시도
        title_element = soup.select_one("h1.prod-buy-header__title")
        if not title_element:
            # 다른 셀렉터들 시도
            title_selectors = [
                "h1[class*='title']",
                ".prod-buy-header h1",
                "h1",
                "[class*='product-title']",
                "[class*='prod-title']"
            ]
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    break
        
        if not title_element:
            raise Exception("상품명을 찾을 수 없습니다")
        
        # 리뷰 개수 찾기 - 여러 셀렉터 시도
        count_element = soup.select("span.count")
        if not count_element:
            count_selectors = [
                "span[class*='count']",
                "[class*='review-count']",
                "[class*='total']"
            ]
            for selector in count_selectors:
                count_element = soup.select(selector)
                if count_element:
                    break
        
        if not count_element:
            print("리뷰 개수를 찾을 수 없어 기본값(3000)을 사용합니다")
            review_count = 3000
        else:
            review_count = int(re.sub("[^0-9]", "", count_element[0].text.strip()))
        
        return (
            title_element.text.strip(),
            review_count
        )

    def start(self) -> None:
        self.sd.create_directory()
        URL: str = self.input_review_url()
        self.headers["Referer"] = URL
        prod_code: str = self.get_product_code(URL)

        # 상품 정보 추출
        try:
            self.title, review_count = self.get_product_info(prod_code=prod_code)
        except Exception as e:
            print(
                {"error": f"상품 기본 정보를 불러오는 도중 오류가 발생했습니다.: {e}"}
            )
            sys.exit()
        if review_count > 1500:
            review_pages = 300
        else:
            review_pages: int = self.calculate_total_pages(review_count)
        # Set payload - itemId 사용
        payloads = [
            {
                "productId": prod_code,
                "page": page,
                "size": 5,
                "sortBy": "ORDER_SCORE_ASC",
                "ratings": "",
                "q": "",
                "viRoleCode": 2,
                "ratingSummary": True,
            }
            for page in range(1, min(review_pages + 1, 101))
        ]

        # 데이터 추출
        for payload in payloads:
            self.fetch(payload=payload)

    def fetch(self, payload: list[dict]) -> None:
        now_page: str = payload["page"]
        print(f"\n[INFO] Start crawling page {now_page} ...\n")
        attempt: int = 0
        while attempt < self.retries:
            try:
                resp = rq.get(
                    url=self.base_review_url,
                    headers=self.headers,
                    params=payload,
                    timeout=10,
                )
                html = resp.text
                soup = bs(html, "html.parser")

                # 상품명
                title = soup.select_one("h1.prod-buy-header__title")
                if title == None or title.text == "":
                    title = "-"
                else:
                    title = title.text.strip()

                # Article Boxes
                article_lenth = len(soup.select("article.sdp-review__article__list"))

                for idx in range(article_lenth):
                    dict_data: dict[str, str | int] = dict()
                    articles = soup.select("article.sdp-review__article__list")

                    # 리뷰 날짜
                    review_date = articles[idx].select_one(
                        "div.sdp-review__article__list__info__product-info__reg-date"
                    )
                    if review_date == None or review_date.text == "":
                        review_date = "-"
                    else:
                        review_date = review_date.text.strip()

                    # 구매자 이름
                    user_name = articles[idx].select_one(
                        "span.sdp-review__article__list__info__user__name"
                    )
                    if user_name == None or user_name.text == "":
                        user_name = "-"
                    else:
                        user_name = user_name.text.strip()

                    # 평점
                    rating = articles[idx].select_one(
                        "div.sdp-review__article__list__info__product-info__star-orange"
                    )
                    if rating == None:
                        rating = 0
                    else:
                        rating = int(rating.attrs["data-rating"])

                    # 구매자 상품명
                    prod_name = articles[idx].select_one(
                        "div.sdp-review__article__list__info__product-info__name"
                    )
                    if prod_name == None or prod_name.text == "":
                        prod_name = "-"
                    else:
                        prod_name = prod_name.text.strip()

                    # 헤드라인(타이틀)
                    headline = articles[idx].select_one(
                        "div.sdp-review__article__list__headline"
                    )
                    if headline == None or headline.text == "":
                        headline = "등록된 헤드라인이 없습니다"
                    else:
                        headline = headline.text.strip()

                    # 리뷰 내용
                    review_content = articles[idx].select_one(
                        "div.sdp-review__article__list__review > div"
                    )
                    if review_content == None:
                        review_content = "등록된 리뷰내용이 없습니다"
                    else:
                        review_content = re.sub(
                            "[\n\t]", "", review_content.text.strip()
                        )

                    # 맛 만족도
                    answer = articles[idx].select_one(
                        "span.sdp-review__article__list__survey__row__answer"
                    )
                    if answer == None or answer.text == "":
                        answer = "맛 평가 없음"
                    else:
                        answer = answer.text.strip()

                    dict_data["title"] = self.title
                    dict_data["prod_name"] = prod_name
                    dict_data["review_date"] = review_date
                    dict_data["user_name"] = user_name
                    dict_data["rating"] = rating
                    dict_data["headline"] = headline
                    dict_data["review_content"] = review_content
                    dict_data["answer"] = answer
                    self.sd.save(datas=dict_data)
                    print(dict_data, "\n")
                time.sleep(1)
                return
            except RequestException as e:
                attempt += 1
                print(f"Attempt {attempt}/{self.retries} failed: {e}")
                if attempt < self.retries:
                    time.sleep(self.delay)
                else:
                    print(f"최대 요청 만료! 다시 실행하세요.")
                    sys.exit()

    @staticmethod
    def clear_console() -> None:
        command: str = "clear"
        if os.name in ("nt", "dos"):
            command = "cls"
        os.system(command=command)

    def input_review_url(self) -> str:
        while True:
            self.clear_console()
            user_input: str = input(
                "상품 URL 또는 productId(제품번호)를 입력해주세요\n\n"
                "예시:\n"
                "1. 전체 URL: https://www.coupang.com/vp/products/8693177441?itemId=25240134057...\n"
                "2. productId만: 8693177441\n\n"
                "입력: "
            )
            if not user_input:
                self.clear_console()
                print("입력값이 없습니다")
                continue
            return user_input

    def calculate_total_pages(self, review_counts: int) -> int:
        reviews_per_page: int = 5
        return int(math.ceil(review_counts / reviews_per_page))


class SaveData:
    def __init__(self) -> None:
        self.header = ["이름", "작성일자", "평점", "리뷰 내용", "세정력", "촉촉함", "피부자극"]
        self.rows = []
        self.dir_name = "Coupang-reviews"
        self.create_directory()

    def create_directory(self) -> None:
        if not os.path.exists(self.dir_name):
            os.makedirs(self.dir_name)

    def save(self, datas: dict[str, str | int]) -> None:
        row = [
            datas["user_name"],
            datas["review_date"],
            datas["rating"],
            datas["review_content"],
            datas.get("cleansing", "-"),
            datas.get("moisture", "-"),
            datas.get("irritation", "-")
        ]
        self.rows.append(row)
        file_name: str = os.path.join(self.dir_name, datas["title"] + ".csv")
        with open(file_name, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self.header)
            writer.writerows(self.rows)

    def __del__(self) -> None:
        pass


if __name__ == "__main__":
    coupang = Coupang()
    coupang.start()