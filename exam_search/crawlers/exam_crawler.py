"""
過去問クローラー - Requests + BeautifulSoup4

このスクリプトは、大学や予備校のWebサイトから過去問情報をスクレイピングし、
Djangoデータベースに保存します。

警告:
- スクレイピングを行う前に、対象サイトのrobots.txtを確認してください
- 利用規約を遵守してください
- 過度なリクエストでサーバーに負荷をかけないでください
- 実際の運用では、適切な遅延時間を設定してください
"""

import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
import logging

# Django設定の読み込み
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_search.settings')
django.setup()

from exams.models import University, Exam, AnswerSource

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BaseCrawler:
    """
    クローラーの基底クラス
    """
    
    def __init__(self, delay=2.0):
        """
        Args:
            delay (float): リクエスト間の遅延時間（秒）
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_page(self, url):
        """
        URLからHTMLを取得
        
        Args:
            url (str): 取得するURL
            
        Returns:
            BeautifulSoup: パースされたHTML、失敗時はNone
        """
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # リクエスト間隔を空ける
            time.sleep(self.delay)
            
            return BeautifulSoup(response.content, 'html.parser')
        
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def save_to_db(self, data):
        """
        データをデータベースに保存（サブクラスで実装）
        """
        raise NotImplementedError


class UniversityExamCrawler(BaseCrawler):
    """
    大学公式サイトから過去問情報をクロールするクローラー
    
    例: 東京大学の入試情報ページから過去問PDFのリンクを抽出
    """
    
    def __init__(self, university_name, base_url, delay=2.0):
        """
        Args:
            university_name (str): 大学名
            base_url (str): 大学の入試情報ページURL
            delay (float): リクエスト間隔
        """
        super().__init__(delay)
        self.university_name = university_name
        self.base_url = base_url
        self.university = self._get_or_create_university()
    
    def _get_or_create_university(self):
        """
        Universityモデルの取得または作成
        """
        university, created = University.objects.get_or_create(
            name=self.university_name,
            defaults={
                'school_type': 'university',
                'official_url': self.base_url
            }
        )
        
        if created:
            logger.info(f"Created new university: {self.university_name}")
        else:
            logger.info(f"Found existing university: {self.university_name}")
        
        return university
    
    def crawl_exam_list(self):
        """
        過去問一覧ページをクロールしてExamデータを抽出
        
        注意: 実際のHTML構造に合わせてセレクターを調整する必要があります
        """
        soup = self.fetch_page(self.base_url)
        if not soup:
            return []
        
        exams_data = []
        
        # 例: 過去問リンクを含む要素を探す
        # 実際のHTMLに合わせて調整してください
        exam_links = soup.select('a[href*="kakomon"], a[href*="past"], a[href*=".pdf"]')
        
        for link in exam_links:
            try:
                exam_data = self._parse_exam_link(link)
                if exam_data:
                    exams_data.append(exam_data)
            except Exception as e:
                logger.error(f"Error parsing exam link: {e}")
        
        logger.info(f"Found {len(exams_data)} exams for {self.university_name}")
        return exams_data
    
    def _parse_exam_link(self, link_element):
        """
        リンク要素から過去問情報を抽出
        
        Args:
            link_element: BeautifulSoupのリンク要素
            
        Returns:
            dict: 過去問データ、抽出失敗時はNone
        """
        href = link_element.get('href')
        if not href:
            return None
        
        # 相対URLを絶対URLに変換
        problem_url = urljoin(self.base_url, href)
        
        # リンクテキストから情報を抽出
        text = link_element.get_text(strip=True)
        
        # 年度を抽出（例: "2024年度"などから）
        year = self._extract_year(text)
        if not year:
            return None
        
        # 科目を推測
        subject = self._guess_subject(text)
        
        return {
            'university': self.university,
            'year': year,
            'subject': subject,
            'problem_url': problem_url,
            'description': text,
            'source_type': 'official',
            'scraped_at': datetime.now()
        }
    
    def _extract_year(self, text):
        """
        テキストから年度を抽出
        
        Args:
            text (str): 抽出元テキスト
            
        Returns:
            int: 年度、見つからない場合はNone
        """
        import re
        
        # 2020-2030年の範囲で検索
        match = re.search(r'(202[0-9]|203[0-9])', text)
        if match:
            return int(match.group(1))
        
        # 令和表記から変換（例: 令和6年 → 2024年）
        reiwa_match = re.search(r'令和(\d+)年', text)
        if reiwa_match:
            reiwa_year = int(reiwa_match.group(1))
            return 2018 + reiwa_year
        
        return None
    
    def _guess_subject(self, text):
        """
        テキストから科目を推測
        
        Args:
            text (str): 抽出元テキスト
            
        Returns:
            str: 科目コード
        """
        text_lower = text.lower()
        
        subject_keywords = {
            'math': ['数学', 'mathematics', 'math'],
            'english': ['英語', 'english'],
            'japanese': ['国語', 'japanese', '現代文', '古文', '漢文'],
            'physics': ['物理', 'physics'],
            'chemistry': ['化学', 'chemistry'],
            'biology': ['生物', 'biology'],
            'history': ['日本史', '世界史', 'history'],
            'geography': ['地理', 'geography'],
        }
        
        for subject_code, keywords in subject_keywords.items():
            for keyword in keywords:
                if keyword in text or keyword.lower() in text_lower:
                    return subject_code
        
        return 'other'
    
    def save_to_db(self, exams_data):
        """
        抽出した過去問データをデータベースに保存
        
        Args:
            exams_data (list): 過去問データのリスト
        """
        saved_count = 0
        
        for exam_data in exams_data:
            try:
                exam, created = Exam.objects.update_or_create(
                    university=exam_data['university'],
                    year=exam_data['year'],
                    subject=exam_data['subject'],
                    exam_type='一般入試',
                    defaults={
                        'problem_url': exam_data['problem_url'],
                        'description': exam_data['description'],
                        'source_type': exam_data['source_type'],
                        'scraped_at': exam_data['scraped_at'],
                    }
                )
                
                if created:
                    logger.info(f"Created: {exam}")
                    saved_count += 1
                else:
                    logger.info(f"Updated: {exam}")
            
            except Exception as e:
                logger.error(f"Error saving exam: {e}")
        
        logger.info(f"Saved {saved_count} new exams to database")


class YobiSchoolAnswerCrawler(BaseCrawler):
    """
    予備校サイトから解答・解説情報をクロールするクローラー
    
    例: 河合塾、駿台などの解答速報ページから解答リンクを抽出
    """
    
    def __init__(self, provider_name, base_url, delay=2.0):
        """
        Args:
            provider_name (str): 予備校名（例: 河合塾）
            base_url (str): 解答速報ページのURL
            delay (float): リクエスト間隔
        """
        super().__init__(delay)
        self.provider_name = provider_name
        self.base_url = base_url
    
    def crawl_answers(self, university_name, year):
        """
        特定の大学・年度の解答情報をクロール
        
        Args:
            university_name (str): 大学名
            year (int): 年度
            
        Returns:
            list: 解答データのリスト
        """
        # 検索URLを構築（予備校サイトの構造に合わせて調整）
        search_url = f"{self.base_url}?university={university_name}&year={year}"
        
        soup = self.fetch_page(search_url)
        if not soup:
            return []
        
        answers_data = []
        
        # 解答リンクを抽出（実際のHTMLに合わせて調整）
        answer_links = soup.select('a[href*="answer"], a[href*="kaisetsu"]')
        
        for link in answer_links:
            try:
                answer_data = self._parse_answer_link(link, university_name, year)
                if answer_data:
                    answers_data.append(answer_data)
            except Exception as e:
                logger.error(f"Error parsing answer link: {e}")
        
        logger.info(f"Found {len(answers_data)} answers for {university_name} ({year})")
        return answers_data
    
    def _parse_answer_link(self, link_element, university_name, year):
        """
        解答リンクから情報を抽出
        """
        href = link_element.get('href')
        if not href:
            return None
        
        answer_url = urljoin(self.base_url, href)
        text = link_element.get_text(strip=True)
        
        # 科目を推測
        subject = self._guess_subject(text)
        
        # 詳細解説・動画の有無をチェック
        has_detailed = '解説' in text or 'detailed' in text.lower()
        has_video = '動画' in text or 'video' in text.lower()
        
        return {
            'university_name': university_name,
            'year': year,
            'subject': subject,
            'provider_name': self.provider_name,
            'answer_url': answer_url,
            'has_detailed_explanation': has_detailed,
            'has_video_explanation': has_video,
            'reliability_score': 8,  # デフォルト値
        }
    
    def _guess_subject(self, text):
        """科目を推測（UniversityExamCrawlerと同じロジック）"""
        # 簡略化のため省略（実際は上記と同じ実装）
        if '数学' in text or 'math' in text.lower():
            return 'math'
        elif '英語' in text or 'english' in text.lower():
            return 'english'
        # ... 他の科目も同様
        return 'other'
    
    def save_to_db(self, answers_data):
        """
        解答データをデータベースに保存
        """
        saved_count = 0
        
        for answer_data in answers_data:
            try:
                # 対応するExamを検索
                exam = Exam.objects.filter(
                    university__name=answer_data['university_name'],
                    year=answer_data['year'],
                    subject=answer_data['subject']
                ).first()
                
                if not exam:
                    logger.warning(f"Exam not found for {answer_data}")
                    continue
                
                # AnswerSourceを作成または更新
                answer_source, created = AnswerSource.objects.update_or_create(
                    exam=exam,
                    provider_name=answer_data['provider_name'],
                    defaults={
                        'answer_url': answer_data['answer_url'],
                        'has_detailed_explanation': answer_data['has_detailed_explanation'],
                        'has_video_explanation': answer_data['has_video_explanation'],
                        'reliability_score': answer_data['reliability_score'],
                        'last_checked_at': datetime.now(),
                        'is_active': True,
                    }
                )
                
                if created:
                    logger.info(f"Created: {answer_source}")
                    saved_count += 1
                else:
                    logger.info(f"Updated: {answer_source}")
            
            except Exception as e:
                logger.error(f"Error saving answer source: {e}")
        
        logger.info(f"Saved {saved_count} new answer sources to database")


class RobotsTxtChecker:
    """
    robots.txtをチェックしてクロール可否を判定
    """
    
    @staticmethod
    def is_allowed(url, user_agent='*'):
        """
        URLがクロール可能かチェック
        
        Args:
            url (str): チェック対象のURL
            user_agent (str): User-Agent文字列
            
        Returns:
            bool: クロール可能ならTrue
        """
        from urllib.robotparser import RobotFileParser
        
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        try:
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            is_allowed = rp.can_fetch(user_agent, url)
            logger.info(f"robots.txt check for {url}: {is_allowed}")
            
            return is_allowed
        
        except Exception as e:
            logger.warning(f"Failed to check robots.txt: {e}")
            # エラー時は安全側に倒してクロールしない
            return False


def main():
    """
    メイン実行関数 - サンプルクローラーの実行
    """
    logger.info("=" * 60)
    logger.info("過去問クローラー開始")
    logger.info("=" * 60)
    
    # 例1: 東京大学の過去問をクロール
    # 注意: 実際のURLとHTML構造に合わせて調整してください
    tokyo_url = "https://www.u-tokyo.ac.jp/ja/admissions/undergraduate/e01_04.html"
    
    # robots.txtチェック
    if not RobotsTxtChecker.is_allowed(tokyo_url):
        logger.warning(f"Crawling not allowed by robots.txt: {tokyo_url}")
        # return  # 実際の運用ではここでreturn
    
    # 大学の過去問をクロール
    tokyo_crawler = UniversityExamCrawler(
        university_name="東京大学",
        base_url=tokyo_url,
        delay=3.0  # 3秒間隔
    )
    
    exams_data = tokyo_crawler.crawl_exam_list()
    tokyo_crawler.save_to_db(exams_data)
    
    # 例2: 河合塾の解答をクロール
    kawaijuku_url = "https://www.keinet.ne.jp/exam/past/"
    
    kawaijuku_crawler = YobiSchoolAnswerCrawler(
        provider_name="河合塾",
        base_url=kawaijuku_url,
        delay=3.0
    )
    
    answers_data = kawaijuku_crawler.crawl_answers("東京大学", 2024)
    kawaijuku_crawler.save_to_db(answers_data)
    
    logger.info("=" * 60)
    logger.info("クローラー終了")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
