"""
過去問データをクローリングしてDjangoモデルに投入する管理コマンド

使用方法:
    python manage.py crawl_exam_data

オプション:
    --university: 特定の大学のみをクローリング
    --year: 特定の年度のみをクローリング
    --dry-run: データベースに保存せずに表示のみ

例:
    python manage.py crawl_exam_data
    python manage.py crawl_exam_data --university "東京大学"
    python manage.py crawl_exam_data --year 2024 --dry-run
"""

import time
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from exams.models import University, Exam, AnswerSource
from datetime import datetime


class ExamCrawler:
    """過去問データをクローリングするクラス"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def log(self, message):
        """ログ出力"""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def fetch_page(self, url, max_retries=3):
        """
        URLからHTMLを取得する

        Args:
            url: 取得するURL
            max_retries: リトライ回数

        Returns:
            BeautifulSoupオブジェクト
        """
        for attempt in range(max_retries):
            try:
                self.log(f"Fetching: {url}")
                response = self.session.get(url, timeout=10)
                response.raise_for_status()

                # 文字化け対策
                response.encoding = response.apparent_encoding

                return BeautifulSoup(response.text, 'html.parser')

            except requests.RequestException as e:
                self.log(f"Error fetching {url} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # 指数バックオフ

        return None

    def crawl_sample_university_list(self):
        """
        サンプル: 大学一覧をクローリングする

        実際のサイトに合わせてセレクタを調整してください

        Returns:
            list: 大学情報の辞書リスト
        """
        universities = []

        # ===== サンプル実装 =====
        # 実際のWebサイトに合わせて以下を修正してください

        # 例1: 静的なサンプルデータ
        sample_universities = [
            {
                'name': '東京大学',
                'name_kana': 'とうきょうだいがく',
                'school_type': 'university',
                'official_url': 'https://www.u-tokyo.ac.jp/'
            },
            {
                'name': '京都大学',
                'name_kana': 'きょうとだいがく',
                'school_type': 'university',
                'official_url': 'https://www.kyoto-u.ac.jp/'
            },
            {
                'name': '大阪大学',
                'name_kana': 'おおさかだいがく',
                'school_type': 'university',
                'official_url': 'https://www.osaka-u.ac.jp/'
            }
        ]

        universities.extend(sample_universities)

        # 例2: 実際のWebサイトからクローリングする場合
        # try:
        #     # 大学一覧ページのURL（実際のURLに置き換える）
        #     url = "https://example.com/university-list"
        #     soup = self.fetch_page(url)
        #
        #     # 大学情報を抽出（セレクタは実際のHTMLに合わせる）
        #     for item in soup.select('.university-item'):
        #         university = {
        #             'name': item.select_one('.name').text.strip(),
        #             'name_kana': item.select_one('.kana').text.strip(),
        #             'school_type': 'university',
        #             'official_url': item.select_one('a')['href']
        #         }
        #         universities.append(university)
        #
        # except Exception as e:
        #     self.log(f"Error crawling university list: {e}")

        self.log(f"Found {len(universities)} universities")
        return universities

    def crawl_sample_exams(self, university_name, year=None):
        """
        サンプル: 特定大学の過去問をクローリングする

        Args:
            university_name: 大学名
            year: 年度（Noneの場合は全年度）

        Returns:
            list: 過去問情報の辞書リスト
        """
        exams = []

        # ===== サンプル実装 =====
        # 実際のWebサイトに合わせて以下を修正してください

        # 例1: 静的なサンプルデータ
        if university_name == '東京大学':
            sample_exams = [
                {
                    'year': 2024,
                    'subject': 'mathematics',
                    'exam_type': 'general',
                    'problem_url': 'https://example.com/todai/2024/math.pdf',
                    'description': '2024年度 東京大学 数学 前期試験',
                    'source_type': 'official',
                },
                {
                    'year': 2024,
                    'subject': 'english',
                    'exam_type': 'general',
                    'problem_url': 'https://example.com/todai/2024/english.pdf',
                    'description': '2024年度 東京大学 英語 前期試験',
                    'source_type': 'official',
                },
                {
                    'year': 2023,
                    'subject': 'mathematics',
                    'exam_type': 'general',
                    'problem_url': 'https://example.com/todai/2023/math.pdf',
                    'description': '2023年度 東京大学 数学 前期試験',
                    'source_type': 'official',
                }
            ]

            if year:
                sample_exams = [e for e in sample_exams if e['year'] == year]

            exams.extend(sample_exams)

        # 例2: 実際のWebサイトからクローリングする場合
        # try:
        #     # 過去問ページのURL（実際のURLに置き換える）
        #     url = f"https://example.com/exams/{university_name}"
        #     if year:
        #         url += f"?year={year}"
        #
        #     soup = self.fetch_page(url)
        #
        #     # 過去問情報を抽出（セレクタは実際のHTMLに合わせる）
        #     for item in soup.select('.exam-item'):
        #         exam = {
        #             'year': int(item.select_one('.year').text),
        #             'subject': item.select_one('.subject')['data-subject'],
        #             'exam_type': item.select_one('.exam-type')['data-type'],
        #             'problem_url': item.select_one('.pdf-link')['href'],
        #             'description': item.select_one('.description').text.strip(),
        #             'source_type': 'official',
        #         }
        #         exams.append(exam)
        #
        # except Exception as e:
        #     self.log(f"Error crawling exams for {university_name}: {e}")

        self.log(f"Found {len(exams)} exams for {university_name}")
        return exams

    def crawl_sample_answer_sources(self, exam_info):
        """
        サンプル: 特定過去問の解答・解説ソースをクローリングする

        Args:
            exam_info: 過去問情報の辞書

        Returns:
            list: 解答ソース情報の辞書リスト
        """
        answer_sources = []

        # ===== サンプル実装 =====
        # 実際のWebサイトに合わせて以下を修正してください

        # 例1: 静的なサンプルデータ
        sample_sources = [
            {
                'provider_name': '河合塾',
                'answer_url': f"https://example.com/kawaijuku/answers/{exam_info['year']}.pdf",
                'has_detailed_explanation': True,
                'has_video_explanation': False,
                'reliability_score': 9,
                'notes': '詳細な解説付き'
            },
            {
                'provider_name': '東進ハイスクール',
                'answer_url': f"https://example.com/toshin/answers/{exam_info['year']}.pdf",
                'has_detailed_explanation': True,
                'has_video_explanation': True,
                'reliability_score': 8,
                'notes': '動画解説あり'
            }
        ]

        answer_sources.extend(sample_sources)

        # 例2: 実際のWebサイトからクローリングする場合
        # try:
        #     # 解答・解説ページのURL（実際のURLに置き換える）
        #     url = f"https://example.com/answers?year={exam_info['year']}&subject={exam_info['subject']}"
        #     soup = self.fetch_page(url)
        #
        #     # 解答ソース情報を抽出（セレクタは実際のHTMLに合わせる）
        #     for item in soup.select('.answer-source'):
        #         source = {
        #             'provider_name': item.select_one('.provider').text.strip(),
        #             'answer_url': item.select_one('a')['href'],
        #             'has_detailed_explanation': 'detailed' in item.get('class', []),
        #             'has_video_explanation': 'video' in item.get('class', []),
        #             'reliability_score': int(item.select_one('.rating')['data-score']),
        #             'notes': item.select_one('.notes').text.strip() if item.select_one('.notes') else ''
        #         }
        #         answer_sources.append(source)
        #
        # except Exception as e:
        #     self.log(f"Error crawling answer sources: {e}")

        self.log(f"Found {len(answer_sources)} answer sources")
        return answer_sources


class Command(BaseCommand):
    help = '過去問データをWebサイトからクローリングしてデータベースに投入します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--university',
            type=str,
            help='特定の大学のみをクローリング'
        )

        parser.add_argument(
            '--year',
            type=int,
            help='特定の年度のみをクローリング'
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='データベースに保存せずに表示のみ'
        )

    def handle(self, *args, **options):
        """管理コマンドのメイン処理"""

        university_filter = options.get('university')
        year_filter = options.get('year')
        dry_run = options.get('dry_run')  # Djangoは自動的にハイフンをアンダースコアに変換

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('過去問データクローラー'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN モード: データベースには保存しません'))

        # クローラーのインスタンス作成
        crawler = ExamCrawler(verbose=True)

        # 統計情報
        stats = {
            'universities_created': 0,
            'universities_updated': 0,
            'exams_created': 0,
            'exams_updated': 0,
            'answer_sources_created': 0,
            'answer_sources_updated': 0,
            'errors': 0
        }

        try:
            # 大学一覧を取得
            self.stdout.write('\n1. 大学情報を取得中...')
            universities_data = crawler.crawl_sample_university_list()

            if university_filter:
                universities_data = [
                    u for u in universities_data
                    if university_filter.lower() in u['name'].lower()
                ]

            self.stdout.write(self.style.SUCCESS(f'   {len(universities_data)}件の大学を取得'))

            # 各大学について処理
            for uni_data in universities_data:
                self.stdout.write(f'\n2. {uni_data["name"]} の過去問を取得中...')

                # 大学の作成または更新
                if not dry_run:
                    university, created = University.objects.get_or_create(
                        name=uni_data['name'],
                        defaults={
                            'name_kana': uni_data['name_kana'],
                            'school_type': uni_data['school_type'],
                            'official_url': uni_data['official_url']
                        }
                    )

                    if created:
                        stats['universities_created'] += 1
                        self.stdout.write(self.style.SUCCESS(f'   ✓ 大学を新規作成: {university.name}'))
                    else:
                        stats['universities_updated'] += 1
                        self.stdout.write(f'   - 大学は既に存在: {university.name}')
                else:
                    self.stdout.write(f'   [DRY RUN] 大学: {uni_data["name"]}')
                    university = None

                # 過去問を取得
                exams_data = crawler.crawl_sample_exams(uni_data['name'], year_filter)
                self.stdout.write(self.style.SUCCESS(f'   {len(exams_data)}件の過去問を取得'))

                # 各過去問について処理
                for exam_data in exams_data:
                    try:
                        if not dry_run:
                            # 過去問の作成または更新
                            exam, created = Exam.objects.get_or_create(
                                university=university,
                                year=exam_data['year'],
                                subject=exam_data['subject'],
                                exam_type=exam_data['exam_type'],
                                defaults={
                                    'problem_url': exam_data['problem_url'],
                                    'description': exam_data['description'],
                                    'source_type': exam_data['source_type'],
                                    'scraped_at': timezone.now(),
                                    'is_verified': True
                                }
                            )

                            if created:
                                stats['exams_created'] += 1
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'     ✓ 過去問を新規作成: {exam.year}年 {exam.get_subject_display()}'
                                    )
                                )
                            else:
                                stats['exams_updated'] += 1
                                self.stdout.write(
                                    f'     - 過去問は既に存在: {exam.year}年 {exam.get_subject_display()}'
                                )
                        else:
                            self.stdout.write(
                                f'     [DRY RUN] 過去問: {exam_data["year"]}年 {exam_data["subject"]}'
                            )
                            exam = None

                        # 解答・解説ソースを取得
                        answer_sources_data = crawler.crawl_sample_answer_sources(exam_data)

                        for source_data in answer_sources_data:
                            try:
                                if not dry_run:
                                    # 解答ソースの作成または更新
                                    answer_source, created = AnswerSource.objects.get_or_create(
                                        exam=exam,
                                        provider_name=source_data['provider_name'],
                                        defaults={
                                            'answer_url': source_data['answer_url'],
                                            'has_detailed_explanation': source_data['has_detailed_explanation'],
                                            'has_video_explanation': source_data['has_video_explanation'],
                                            'reliability_score': source_data['reliability_score'],
                                            'notes': source_data['notes'],
                                            'last_checked_at': timezone.now(),
                                            'is_active': True
                                        }
                                    )

                                    if created:
                                        stats['answer_sources_created'] += 1
                                        self.stdout.write(
                                            self.style.SUCCESS(
                                                f'       ✓ 解答ソースを新規作成: {answer_source.provider_name}'
                                            )
                                        )
                                    else:
                                        stats['answer_sources_updated'] += 1
                                else:
                                    self.stdout.write(
                                        f'       [DRY RUN] 解答ソース: {source_data["provider_name"]}'
                                    )

                            except Exception as e:
                                stats['errors'] += 1
                                self.stdout.write(
                                    self.style.ERROR(f'       ✗ 解答ソースの保存エラー: {e}')
                                )

                    except Exception as e:
                        stats['errors'] += 1
                        self.stdout.write(
                            self.style.ERROR(f'     ✗ 過去問の保存エラー: {e}')
                        )

                # サーバーに負荷をかけないよう待機
                time.sleep(1)

            # 結果サマリーを表示
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.SUCCESS('クローリング完了'))
            self.stdout.write('=' * 60)
            self.stdout.write(f'大学:')
            self.stdout.write(f'  新規作成: {stats["universities_created"]}')
            self.stdout.write(f'  既存:     {stats["universities_updated"]}')
            self.stdout.write(f'過去問:')
            self.stdout.write(f'  新規作成: {stats["exams_created"]}')
            self.stdout.write(f'  既存:     {stats["exams_updated"]}')
            self.stdout.write(f'解答ソース:')
            self.stdout.write(f'  新規作成: {stats["answer_sources_created"]}')
            self.stdout.write(f'  既存:     {stats["answer_sources_updated"]}')

            if stats['errors'] > 0:
                self.stdout.write(self.style.ERROR(f'エラー: {stats["errors"]}'))

            if not dry_run:
                self.stdout.write(self.style.SUCCESS('\nデータベースへの保存が完了しました'))
            else:
                self.stdout.write(self.style.WARNING('\nDRY RUN モードのため、データベースには保存されませんでした'))

        except Exception as e:
            raise CommandError(f'クローリング中にエラーが発生しました: {e}')
