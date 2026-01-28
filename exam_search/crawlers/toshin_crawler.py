"""
東進ハイスクール過去問データベース専用クローラー

このクローラーは、東進ハイスクールの過去問データベースから
大学入試の過去問情報と解答・解説のリンクを取得します。

注意事項:
- 実際のサイト構造は変更される可能性があります
- このコードはサンプルであり、実際の使用前に対象サイトの利用規約を確認してください
- robots.txtの確認とクロール間隔の設定を忘れないでください
"""

import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re

# Django設定の読み込み
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_search.settings')
django.setup()

from exams.models import University, Exam, AnswerSource

logger = logging.getLogger(__name__)


class ToshinExamCrawler:
    """
    東進ハイスクール過去問データベース専用クローラー
    
    クロール対象の例:
    - 大学別過去問一覧ページ
    - 年度別・科目別のPDFリンク
    - 解答・解説のダウンロードリンク
    """
    
    # 大学一覧ページ（例）
    UNIVERSITY_LIST_URL = "https://www.toshin-kakomon.com/university-list"
    
    # 科目マッピング
    SUBJECT_MAPPING = {
        '英語': 'english',
        '数学': 'math',
        '国語': 'japanese',
        '物理': 'physics',
        '化学': 'chemistry',
        '生物': 'biology',
        '日本史': 'history',
        '世界史': 'history',
        '地理': 'geography',
    }
    
    def __init__(self, delay=3.0):
        """
        Args:
            delay (float): リクエスト間隔（秒）
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en;q=0.9',
        })
    
    def fetch_page(self, url):
        """HTMLページを取得してパース"""
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # レスポンスのエンコーディングを適切に設定
            response.encoding = response.apparent_encoding
            
            time.sleep(self.delay)
            
            return BeautifulSoup(response.text, 'html.parser')
        
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def crawl_university_list(self):
        """
        大学一覧ページから大学情報を取得
        
        Returns:
            list: 大学データのリスト
        """
        soup = self.fetch_page(self.UNIVERSITY_LIST_URL)
        if not soup:
            return []
        
        universities = []
        
        # 大学リンクを抽出（例: <a class="university-link" href="/university/tokyo">東京大学</a>）
        university_links = soup.select('a.university-link, li.university-item a')
        
        for link in university_links:
            university_name = link.get_text(strip=True)
            university_url = link.get('href')
            
            if not university_name or not university_url:
                continue
            
            universities.append({
                'name': university_name,
                'url': university_url
            })
            
            logger.info(f"Found university: {university_name}")
        
        return universities
    
    def crawl_university_exams(self, university_url, university_name):
        """
        特定の大学の過去問ページから過去問情報を抽出
        
        Args:
            university_url (str): 大学ページのURL
            university_name (str): 大学名
            
        Returns:
            list: 過去問データのリスト
        """
        # 大学オブジェクトを取得または作成
        university, _ = University.objects.get_or_create(
            name=university_name,
            defaults={
                'school_type': 'university',
                'official_url': ''
            }
        )
        
        soup = self.fetch_page(university_url)
        if not soup:
            return []
        
        exams_data = []
        
        # 年度別のセクションを探す
        year_sections = soup.select('div.year-section, section.exam-year')
        
        for year_section in year_sections:
            # 年度を抽出
            year_text = year_section.select_one('h3, h2, .year-title')
            if not year_text:
                continue
            
            year = self._extract_year(year_text.get_text())
            if not year:
                continue
            
            # 科目別のリンクを抽出
            subject_links = year_section.select('a.subject-link, a.pdf-link')
            
            for link in subject_links:
                exam_data = self._parse_exam_link(
                    link, university, year
                )
                if exam_data:
                    exams_data.append(exam_data)
        
        return exams_data
    
    def _parse_exam_link(self, link_element, university, year):
        """
        過去問リンクから詳細情報を抽出
        
        Args:
            link_element: BeautifulSoupのリンク要素
            university: Universityモデルのインスタンス
            year (int): 年度
            
        Returns:
            dict: 過去問データ
        """
        href = link_element.get('href')
        if not href:
            return None
        
        text = link_element.get_text(strip=True)
        
        # 科目を判定
        subject = self._detect_subject(text)
        
        # 試験種別を判定
        exam_type = self._detect_exam_type(text)
        
        return {
            'university': university,
            'year': year,
            'subject': subject,
            'exam_type': exam_type,
            'problem_url': href,
            'description': text,
            'source_type': 'yobi_school',
        }
    
    def _extract_year(self, text):
        """テキストから年度を抽出"""
        # 西暦
        match = re.search(r'(20\d{2})', text)
        if match:
            return int(match.group(1))
        
        # 令和
        reiwa_match = re.search(r'令和(\d+)年', text)
        if reiwa_match:
            return 2018 + int(reiwa_match.group(1))
        
        # 平成
        heisei_match = re.search(r'平成(\d+)年', text)
        if heisei_match:
            return 1988 + int(heisei_match.group(1))
        
        return None
    
    def _detect_subject(self, text):
        """テキストから科目を判定"""
        for subject_name, subject_code in self.SUBJECT_MAPPING.items():
            if subject_name in text:
                return subject_code
        return 'other'
    
    def _detect_exam_type(self, text):
        """テキストから試験種別を判定"""
        if '推薦' in text or 'AO' in text:
            return '推薦入試'
        elif '前期' in text:
            return '前期日程'
        elif '後期' in text:
            return '後期日程'
        elif '共通テスト' in text or 'センター' in text:
            return '共通テスト'
        else:
            return '一般入試'
    
    def crawl_answer_sources(self, exam_url, exam):
        """
        過去問ページから解答・解説のリンクを抽出
        
        Args:
            exam_url (str): 過去問ページのURL
            exam: Examモデルのインスタンス
            
        Returns:
            list: 解答ソースデータのリスト
        """
        soup = self.fetch_page(exam_url)
        if not soup:
            return []
        
        answer_sources = []
        
        # 解答リンクを探す
        answer_links = soup.select('a.answer-link, a.kaisetsu-link, a[href*="answer"]')
        
        for link in answer_links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            if not href:
                continue
            
            # 詳細解説・動画の有無をチェック
            has_detailed = '詳細' in text or '解説' in text
            has_video = '動画' in text or '映像' in text
            
            answer_sources.append({
                'exam': exam,
                'provider_name': '東進ハイスクール',
                'answer_url': href,
                'has_detailed_explanation': has_detailed,
                'has_video_explanation': has_video,
                'reliability_score': 8,
                'notes': f'東進ハイスクール提供: {text}'
            })
        
        return answer_sources
    
    def save_exams_to_db(self, exams_data):
        """過去問データをデータベースに保存"""
        saved_count = 0
        
        for exam_data in exams_data:
            try:
                exam, created = Exam.objects.update_or_create(
                    university=exam_data['university'],
                    year=exam_data['year'],
                    subject=exam_data['subject'],
                    exam_type=exam_data['exam_type'],
                    defaults={
                        'problem_url': exam_data['problem_url'],
                        'description': exam_data['description'],
                        'source_type': exam_data['source_type'],
                        'scraped_at': datetime.now(),
                        'is_verified': False,
                    }
                )
                
                if created:
                    logger.info(f"✓ Created: {exam}")
                    saved_count += 1
                else:
                    logger.info(f"○ Updated: {exam}")
            
            except Exception as e:
                logger.error(f"✗ Error saving exam: {e}")
        
        logger.info(f"Saved {saved_count} new exams")
        return saved_count
    
    def save_answer_sources_to_db(self, answer_sources_data):
        """解答ソースをデータベースに保存"""
        saved_count = 0
        
        for answer_data in answer_sources_data:
            try:
                answer_source, created = AnswerSource.objects.update_or_create(
                    exam=answer_data['exam'],
                    provider_name=answer_data['provider_name'],
                    defaults={
                        'answer_url': answer_data['answer_url'],
                        'has_detailed_explanation': answer_data['has_detailed_explanation'],
                        'has_video_explanation': answer_data['has_video_explanation'],
                        'reliability_score': answer_data['reliability_score'],
                        'notes': answer_data.get('notes', ''),
                        'last_checked_at': datetime.now(),
                        'is_active': True,
                    }
                )
                
                if created:
                    logger.info(f"✓ Created answer source: {answer_source}")
                    saved_count += 1
                else:
                    logger.info(f"○ Updated answer source: {answer_source}")
            
            except Exception as e:
                logger.error(f"✗ Error saving answer source: {e}")
        
        logger.info(f"Saved {saved_count} new answer sources")
        return saved_count


def main():
    """
    メイン実行関数
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger.info("=" * 80)
    logger.info("東進ハイスクール過去問クローラー開始")
    logger.info("=" * 80)
    
    crawler = ToshinExamCrawler(delay=3.0)
    
    # ステップ1: 大学一覧を取得（例）
    # 実際の運用では、特定の大学に絞ってクロールすることを推奨
    universities = [
        {'name': '東京大学', 'url': 'https://example.com/tokyo'},
        {'name': '京都大学', 'url': 'https://example.com/kyoto'},
        # ... 他の大学
    ]
    
    total_exams = 0
    
    # ステップ2: 各大学の過去問を取得
    for univ_data in universities[:3]:  # テストのため最初の3大学のみ
        logger.info(f"\n処理中: {univ_data['name']}")
        
        exams_data = crawler.crawl_university_exams(
            univ_data['url'],
            univ_data['name']
        )
        
        # データベースに保存
        count = crawler.save_exams_to_db(exams_data)
        total_exams += count
        
        logger.info(f"{univ_data['name']}: {count}件の過去問を保存")
    
    logger.info("=" * 80)
    logger.info(f"クローラー終了 - 合計 {total_exams}件の過去問を保存")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
