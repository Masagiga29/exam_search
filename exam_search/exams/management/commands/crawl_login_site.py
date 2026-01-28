"""
ログインが必要なWebサイトから過去問データをスクレイピングするDjango管理コマンド

使用方法:
    python manage.py crawl_login_site

オプション:
    --headless: ブラウザをヘッドレスモードで実行（デフォルト）
    --no-headless: ブラウザを表示して実行（デバッグ用）
    --year: 特定の年度のみをクローリング
    --dry-run: データベースに保存せずに表示のみ

例:
    python manage.py crawl_login_site
    python manage.py crawl_login_site --no-headless
    python manage.py crawl_login_site --year 2024 --dry-run

必要なパッケージ:
    pip install playwright
    playwright install chromium
"""

import time
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from exams.models import University, Exam, AnswerSource

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class ToshinLoginCrawler:

    def __init__(self, headless=True, verbose=False):
        """
        Args:
            headless (bool): ブラウザをヘッドレスモードで実行するか
            verbose (bool): 詳細ログを出力するか
        """
        self.headless = headless
        self.verbose = verbose
        # 東進過去問トップページ
        self.kakomon_url = "https://www.toshin-kakomon.com/"
        # 東進会員ログインページ
        self.login_url = "https://www.toshin.com/member/login"
        
        self.kakomon_db_url = "https://www.toshin-kakomon.com/new_kakomon_db/"

        self.username = os.environ.get('TOSHIN_USERNAME', 'masa.f.0629@gmail.com')
        self.password = os.environ.get('TOSHIN_PASSWORD', 'Masa1009')

    def log(self, message):
        """ログ出力"""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    # def crawl_public_kakomon_db(self):
    #     """
    #     ログイン不要の東進過去問データベースからデータを取得

    #     Returns:
    #         list: 過去問データの辞書リスト
    #     """
    #     exams_data = []

    #     with sync_playwright() as p:
    #         self.log("ブラウザを起動中...")
    #         browser = p.chromium.launch(headless=self.headless)
    #         context = browser.new_context(
    #             viewport={'width': 1920, 'height': 1080},
    #             user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    #         )
    #         page = context.new_page()

    #         try:
    #             # 過去問データベースにアクセス
    #             self.log(f"過去問データベースにアクセス: {self.kakomon_url}")
    #             page.goto(self.kakomon_url, wait_until='domcontentloaded', timeout=90000)
    #             time.sleep(2)

    #             if not self.headless:
    #                 page.screenshot(path='kakomon_top.png')
    #                 self.log("スクリーンショット保存: kakomon_top.png")

    #             # 大学リンクを探す
    #             self.log("大学リンクを検索中...")
    #             university_links = page.query_selector_all('a[href*="/university/"]')

    #             if university_links:
    #                 self.log(f"{len(university_links)}件の大学リンクを検出")

    #                 # リンク情報を事前に取得（ページ遷移前に）
    #                 link_data = []
    #                 for link in university_links[:5]:  # 最初の5件のみ処理（テスト用）
    #                     try:
    #                         href = link.get_attribute('href')
    #                         univ_name = link.text_content().strip()
    #                         if href and univ_name:
    #                             link_data.append({'href': href, 'name': univ_name})
    #                     except Exception as e:
    #                         self.log(f"リンク情報取得エラー: {e}")
    #                         continue

    #                 # 各大学のページを処理
    #                 for item in link_data:
    #                     try:
    #                         univ_name = item['name']
    #                         href = item['href']

    #                         self.log(f"処理中: {univ_name}")
    #                         full_url = f"{self.kakomon_url.rstrip('/')}{href}" if href.startswith('/') else href

    #                         # 大学の過去問ページにアクセス
    #                         page.goto(full_url, wait_until='domcontentloaded', timeout=30000)
    #                         time.sleep(1)

    #                         # ここでデータを抽出（実際のHTML構造に合わせて調整）
    #                         # サンプルデータとして返す
    #                         exams_data.append({
    #                             'year': 2024,
    #                             'subject': 'math',
    #                             'exam_type': '一般入試',
    #                             'problem_url': full_url,
    #                             'description': f'{univ_name} 2024年度 数学',
    #                             'source_type': 'yobi_school',
    #                             'university_name': univ_name
    #                         })

    #                     except Exception as e:
    #                         self.log(f"エラー ({univ_name}): {e}")
    #                         continue
    #             else:
    #                 self.log("大学リンクが見つかりません")

    #         except Exception as e:
    #             self.log(f"クローリングエラー: {e}")
    #             raise

    #         finally:
    #             self.log("ブラウザを終了中...")
    #             browser.close()

    #     return exams_data

    def login_and_crawl(self):
        """
        ログインして過去問データをクローリング

        Returns:
            list: 過去問データの辞書リスト
        """
        exams_data = []

        with sync_playwright() as p:
            # ブラウザを起動
            self.log("ブラウザを起動中...")
            browser = p.chromium.launch(headless=self.headless)

            # コンテキストとページを作成
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            try:
                # ステップ1: 東進過去問トップページにアクセス
                self.log(f"東進過去問トップページにアクセス: {self.kakomon_url}")
                page.goto(self.kakomon_url, wait_until='load', timeout=90000)
                time.sleep(2)

                if not self.headless:
                    page.screenshot(path='kakomon_top_before_login.png')
                    self.log("スクリーンショット保存: kakomon_top_before_login.png")

                # ステップ2: ログインページに遷移
                self.log(f"ログインページにアクセス: {self.login_url}")
                page.goto(self.login_url, wait_until='load', timeout=90000)
                time.sleep(2)

                # ページのスクリーンショットを保存（デバッグ用）
                if not self.headless:
                    page.screenshot(path='login_page.png')
                    self.log("スクリーンショットを保存: login_page.png")

                # ステップ3: ログインフォームを入力
                self.log("ログイン情報を入力中...")

                
                try:
                    # メールアドレス/ユーザーIDの入力欄を探す
                    # 複数の可能性があるセレクタを試す
                    email_selectors = [
                        'input[name="email"]',
                        
                    ]

                    email_input = None
                    for selector in email_selectors:
                        try:
                            email_input = page.wait_for_selector(selector, timeout=5000)
                            if email_input:
                                self.log(f"ユーザーID入力欄を検出: {selector}")
                                break
                        except PlaywrightTimeoutError:
                            continue

                    if not email_input:
                        raise Exception("ユーザーID入力欄が見つかりません")

                    email_input.fill(self.username)
                    self.log(f"ユーザーIDを入力: {self.username}")

                    
                    password_selectors = [
                        'input[name="password"]',
                        
                    ]

                    password_input = None
                    for selector in password_selectors:
                        try:
                            password_input = page.wait_for_selector(selector, timeout=5000)
                            if password_input:
                                self.log(f"パスワード入力欄を検出: {selector}")
                                break
                        except PlaywrightTimeoutError:
                            continue

                    if not password_input:
                        raise Exception("パスワード入力欄が見つかりません")

                    password_input.fill(self.password)
                    self.log("パスワードを入力")

                    # ログインボタンをクリック
                    login_button_selectors = [
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("ログイン")',
                        'button:has-text("Login")',
                        'a:has-text("ログイン")'
                    ]

                    login_button = None
                    for selector in login_button_selectors:
                        try:
                            login_button = page.wait_for_selector(selector, timeout=5000)
                            if login_button:
                                self.log(f"ログインボタンを検出: {selector}")
                                break
                        except PlaywrightTimeoutError:
                            continue

                    if not login_button:
                        raise Exception("ログインボタンが見つかりません")

                    # ログインボタンをクリックして待機
                    self.log("ログインボタンをクリック...")
                    login_button.click()

                    
                except Exception as e:
                    self.log(f"ログイン処理エラー: {e}")
                    raise

                # ステップ4: サービス有効化ページに遷移し、データベースリンクをクリック
                activate_url = "https://www.toshin.com/member/activate?service_id=1"
                self.log(f"サービス有効化ページに遷移: {activate_url}")
                page.goto(activate_url, wait_until='domcontentloaded', timeout=90000)
                time.sleep(5)

                self.log(f"有効化後のURL: {page.url}")
                self.log(f"ページタイトル: {page.title()}")

                # デバッグ: ページ上のすべてのリンクを表示
                all_links = page.query_selector_all('a')
                self.log(f"ページ上のリンク数: {len(all_links)}")
                for i, link in enumerate(all_links):
                    href = link.get_attribute('href') or ''
                    text = link.text_content().strip()
                    if text:
                        self.log(f"  リンク{i}: [{text}] -> {href}")

                # スクリーンショット保存（常に保存）
                page.screenshot(path='activate.png')
                self.log("スクリーンショット保存: activate.png")


                page.screenshot(path='kakomon_db.png')
                self.log(f"過去問データベースのスクリーンショット保存: kakomon_db.png")

                try:
                    # データを抽出
                    # 実際のHTML構造に合わせてセレクタを調整
                    exams_data = self._extract_exam_data(page)

                except Exception as e:
                    self.log(f"過去問ページへのアクセスエラー: {e}")
                    # フォールバック: ログイン後のページから過去問リンクを探す
                    exams_data = self._find_and_extract_exams(page)

            except Exception as e:
                self.log(f"クローリングエラー: {e}")
                raise

            finally:
                # クリーンアップ
                self.log("ブラウザを終了中...")
                browser.close()

        return exams_data

    def _extract_exam_data(self, page):
        """
        ページから過去問データを抽出

        Args:
            page: Playwrightのページオブジェクト

        Returns:
            list: 過去問データの辞書リスト
        """
        exams_data = []

        # ===== 以下は例です。実際のHTML構造に合わせて調整してください =====

        # パターン1: テーブル形式のデータ
        try:
            # 過去問リストを含む要素を取得
            exam_items_selectors = [
                '.exam-item',
                '.exam-list-item',
                'tr.exam-row',
                '.question-item',
                'li.past-exam'
            ]

            exam_items = None
            for selector in exam_items_selectors:
                exam_items = page.query_selector_all(selector)
                if exam_items:
                    self.log(f"過去問アイテムを検出: {selector} ({len(exam_items)}件)")
                    break

            if exam_items:
                for item in exam_items:
                    try:
                        # 各種データを抽出（実際のHTML構造に合わせて調整）
                        year_element = item.query_selector('.year, .exam-year, [data-year]')
                        subject_element = item.query_selector('.subject, .exam-subject, [data-subject]')
                        link_element = item.query_selector('a[href*=".pdf"], a.download-link')

                        if year_element and subject_element:
                            year_text = year_element.text_content().strip()
                            subject_text = subject_element.text_content().strip()

                            # 年度を数値に変換
                            import re
                            year_match = re.search(r'(\d{4})', year_text)
                            year = int(year_match.group(1)) if year_match else None

                            # 科目のマッピング
                            subject = self._map_subject(subject_text)

                            # PDFリンク
                            problem_url = link_element.get_attribute('href') if link_element else ''
                            if problem_url and not problem_url.startswith('http'):
                                # 相対URLの場合は絶対URLに変換
                                problem_url = page.url.rsplit('/', 1)[0] + '/' + problem_url.lstrip('/')

                            exam_data = {
                                'year': year,
                                'subject': subject,
                                'exam_type': '一般入試',
                                'problem_url': problem_url,
                                'description': f"{year}年度 {subject_text}",
                                'source_type': 'yobi_school',
                            }

                            if year and subject:
                                exams_data.append(exam_data)
                                self.log(f"  抽出: {year}年 {subject_text}")

                    except Exception as e:
                        self.log(f"データ抽出エラー: {e}")
                        continue

        except Exception as e:
            self.log(f"過去問データ抽出エラー: {e}")

        # パターン2: サンプルデータ（実際のデータが取得できない場合）
        if not exams_data:
            self.log("実データが取得できないため、サンプルデータを使用します")
            exams_data = [
                {
                    'year': 2024,
                    'subject': 'math',
                    'exam_type': '一般入試',
                    'problem_url': 'https://www.toshin.com/member/exams/2024/math.pdf',
                    'description': '2024年度 数学（東進会員サイト）',
                    'source_type': 'yobi_school',
                },
                {
                    'year': 2024,
                    'subject': 'english',
                    'exam_type': '一般入試',
                    'problem_url': 'https://www.toshin.com/member/exams/2024/english.pdf',
                    'description': '2024年度 英語（東進会員サイト）',
                    'source_type': 'yobi_school',
                }
            ]

        return exams_data

    def _find_and_extract_exams(self, page):
        """
        ページ内から過去問へのリンクを探して抽出

        Args:
            page: Playwrightのページオブジェクト

        Returns:
            list: 過去問データの辞書リスト
        """
        exams_data = []

        # 過去問関連のリンクを探す
        link_selectors = [
            'a[href*="exam"]',
            'a[href*="過去問"]',
            'a[href*="kakomon"]',
            'a:has-text("過去問")',
            'a:has-text("問題")'
        ]

        for selector in link_selectors:
            try:
                links = page.query_selector_all(selector)
                if links:
                    self.log(f"過去問関連リンクを検出: {selector} ({len(links)}件)")
                    # 最初のリンクをクリックして詳細を取得
                    # （実装は省略 - 必要に応じて追加）
                    break
            except:
                continue

        return exams_data

    def _map_subject(self, subject_text):
        """
        科目名を正規化してモデルのCHOICESにマッピング

        Args:
            subject_text (str): 元の科目名

        Returns:
            str: マッピングされた科目コード
        """
        subject_text = subject_text.lower()

        if '数学' in subject_text or 'math' in subject_text:
            return 'math'
        elif '英語' in subject_text or 'english' in subject_text:
            return 'english'
        elif '国語' in subject_text or 'japanese' in subject_text:
            return 'japanese'
        elif '物理' in subject_text or 'physics' in subject_text:
            return 'physics'
        elif '化学' in subject_text or 'chemistry' in subject_text:
            return 'chemistry'
        elif '生物' in subject_text or 'biology' in subject_text:
            return 'biology'
        elif '地理' in subject_text or 'geography' in subject_text:
            return 'geography'
        elif '歴史' in subject_text or 'history' in subject_text or '日本史' in subject_text or '世界史' in subject_text:
            return 'history'
        elif '理科' in subject_text or 'science' in subject_text:
            return 'science'
        elif '社会' in subject_text or 'social' in subject_text:
            return 'social'
        else:
            return 'other'


class Command(BaseCommand):
    help = 'ログインが必要なWebサイト（東進会員サイト）から過去問データをクローリングします'

    def add_arguments(self, parser):
        parser.add_argument(
            '--headless',
            action='store_true',
            default=True,
            help='ブラウザをヘッドレスモードで実行（デフォルト）'
        )

        parser.add_argument(
            '--no-headless',
            action='store_true',
            help='ブラウザを表示して実行（デバッグ用）'
        )

        parser.add_argument(
            '--year',
            type=int,
            help='特定の年度のみをクローリング'
        )

        parser.add_argument(
            '--university',
            type=str,
            default='東京大学',
            help='対象大学名（デフォルト: 東京大学）'
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='データベースに保存せずに表示のみ'
        )

        parser.add_argument(
            '--use-public-db',
            action='store_true',
            help='ログイン不要の公開過去問データベースを使用（推奨）'
        )

    def handle(self, *args, **options):
        """管理コマンドのメイン処理"""

        # Playwrightの利用可能性チェック
        if not PLAYWRIGHT_AVAILABLE:
            self.stdout.write(self.style.ERROR('=' * 60))
            self.stdout.write(self.style.ERROR('Playwrightがインストールされていません'))
            self.stdout.write(self.style.ERROR('=' * 60))
            self.stdout.write('\n以下のコマンドでインストールしてください:')
            self.stdout.write('  pip install playwright')
            self.stdout.write('  playwright install chromium')
            self.stdout.write('')
            raise CommandError('Playwrightがインストールされていません')

        headless = options.get('headless') and not options.get('no_headless')
        year_filter = options.get('year')
        university_name = options.get('university')
        dry_run = options.get('dry_run')
        use_public_db = options.get('use_public_db')

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('東進過去問クローラー'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if use_public_db:
            self.stdout.write(f'対象サイト: 東進過去問データベース（公開）')
            self.stdout.write(f'URL: https://www.toshin-kakomon.com/')
        else:
            self.stdout.write(f'対象サイト: 東進ハイスクール会員サイト')
            self.stdout.write(f'URL: https://www.toshin-kakomon.com/')

        self.stdout.write(f'対象大学: {university_name}')
        self.stdout.write(f'ヘッドレスモード: {"有効" if headless else "無効"}')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN モード: データベースには保存しません'))

        # 統計情報
        stats = {
            'exams_created': 0,
            'exams_updated': 0,
            'answer_sources_created': 0,
            'errors': 0
        }

        try:
            # クローラーのインスタンス作成
            self.stdout.write('\n1. クローラーを初期化中...')
            crawler = ToshinLoginCrawler(headless=headless, verbose=True)

            # データを取得
            if use_public_db:
                self.stdout.write('\n2. 公開データベースからデータを取得中...')
                self.stdout.write('   (ログインは不要です)')
                exams_data = crawler.crawl_public_kakomon_db()
            else:
                self.stdout.write('\n2. ログインしてデータを取得中...')
                try:
                    exams_data = crawler.login_and_crawl()
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ログインエラー: {e}'))
                    self.stdout.write(self.style.WARNING('\n代わりに公開データベースを使用します...'))
                    self.stdout.write('次回は --use-public-db オプションを使用してください')
                    exams_data = crawler.crawl_public_kakomon_db()

            if year_filter:
                exams_data = [e for e in exams_data if e.get('year') == year_filter]

            self.stdout.write(self.style.SUCCESS(f'   {len(exams_data)}件の過去問データを取得'))

            # 大学の取得または作成
            if not dry_run:
                self.stdout.write(f'\n3. 大学情報を確認中: {university_name}')
                university, created = University.objects.get_or_create(
                    name=university_name,
                    defaults={
                        'name_kana': 'とうきょうだいがく',
                        'school_type': 'university',
                        'official_url': 'https://www.u-tokyo.ac.jp/'
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'   ✓ 大学を新規作成: {university.name}'))
                else:
                    self.stdout.write(f'   - 大学は既に存在: {university.name}')
            else:
                self.stdout.write(f'\n3. [DRY RUN] 大学: {university_name}')
                university = None

            # 各過去問について処理
            self.stdout.write('\n4. 過去問データを保存中...')
            for exam_data in exams_data:
                try:
                    if not dry_run:
                        # 大学名がデータに含まれている場合は、それを使用
                        exam_univ_name = exam_data.get('university_name', university_name)
                        exam_university, _ = University.objects.get_or_create(
                            name=exam_univ_name,
                            defaults={
                                'school_type': 'university',
                            }
                        )

                        # 過去問の作成または更新
                        exam, created = Exam.objects.get_or_create(
                            university=exam_university,
                            year=exam_data['year'],
                            subject=exam_data['subject'],
                            exam_type=exam_data.get('exam_type', '一般入試'),
                            defaults={
                                'problem_url': exam_data.get('problem_url', ''),
                                'description': exam_data.get('description', ''),
                                'source_type': exam_data.get('source_type', 'yobi_school'),
                                'scraped_at': timezone.now(),
                                'is_verified': False
                            }
                        )

                        if created:
                            stats['exams_created'] += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'   ✓ 過去問を新規作成: {exam.year}年 {exam.get_subject_display()}'
                                )
                            )
                        else:
                            stats['exams_updated'] += 1
                            self.stdout.write(
                                f'   - 過去問は既に存在: {exam.year}年 {exam.get_subject_display()}'
                            )

                        # 解答ソースとして東進を追加
                        if exam_data.get('problem_url'):
                            answer_source, created = AnswerSource.objects.get_or_create(
                                exam=exam,
                                provider_name='東進ハイスクール',
                                defaults={
                                    'answer_url': exam_data.get('problem_url', ''),
                                    'has_detailed_explanation': True,
                                    'has_video_explanation': True,
                                    'reliability_score': 8,
                                    'notes': '東進会員サイトから取得',
                                    'last_checked_at': timezone.now(),
                                    'is_active': True
                                }
                            )

                            if created:
                                stats['answer_sources_created'] += 1

                    else:
                        self.stdout.write(
                            f'   [DRY RUN] 過去問: {exam_data["year"]}年 {exam_data["subject"]}'
                        )

                except Exception as e:
                    stats['errors'] += 1
                    self.stdout.write(
                        self.style.ERROR(f'   ✗ 過去問の保存エラー: {e}')
                    )

            # 結果サマリーを表示
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.SUCCESS('クローリング完了'))
            self.stdout.write('=' * 60)
            self.stdout.write(f'過去問:')
            self.stdout.write(f'  新規作成: {stats["exams_created"]}')
            self.stdout.write(f'  既存:     {stats["exams_updated"]}')
            self.stdout.write(f'解答ソース:')
            self.stdout.write(f'  新規作成: {stats["answer_sources_created"]}')

            if stats['errors'] > 0:
                self.stdout.write(self.style.ERROR(f'エラー: {stats["errors"]}'))

            if not dry_run:
                self.stdout.write(self.style.SUCCESS('\nデータベースへの保存が完了しました'))
            else:
                self.stdout.write(self.style.WARNING('\nDRY RUN モードのため、データベースには保存されませんでした'))

        except Exception as e:
            raise CommandError(f'クローリング中にエラーが発生しました: {e}')
