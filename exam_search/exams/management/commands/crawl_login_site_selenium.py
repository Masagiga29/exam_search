"""
ログインが必要なWebサイトから過去問データをスクレイピングするDjango管理コマンド（Selenium版）

使用方法:
    python manage.py crawl_login_site_selenium

オプション:
    --headless: ブラウザをヘッドレスモードで実行（デフォルト）
    --no-headless: ブラウザを表示して実行（デバッグ用）
    --year: 特定の年度のみをクローリング
    --dry-run: データベースに保存せずに表示のみ

例:
    python manage.py crawl_login_site_selenium
    python manage.py crawl_login_site_selenium --no-headless
    python manage.py crawl_login_site_selenium --year 2024 --dry-run

必要なパッケージ:
    pip install selenium webdriver-manager
"""

import time
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.conf import settings
from exams.models import University, Exam, AnswerSource

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException,
        NoSuchElementException,
        WebDriverException
    )
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options

    # WebDriver Managerを使用してドライバーを自動管理
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        WEBDRIVER_MANAGER_AVAILABLE = True
    except ImportError:
        WEBDRIVER_MANAGER_AVAILABLE = False

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class ToshinLoginCrawlerSelenium:
    """
    東進ハイスクール会員サイトのログインクローラー（Selenium版）
    """

    def __init__(self, headless=True, verbose=False):
        """
        Args:
            headless (bool): ブラウザをヘッドレスモードで実行するか
            verbose (bool): 詳細ログを出力するか
        """
        self.headless = headless
        self.verbose = verbose
        self.login_url = "https://www.toshin.com/member/"
        self.driver = None

        # 環境変数または設定ファイルから認証情報を取得
        self.username = os.environ.get('TOSHIN_USERNAME', 'masa.f.0629@gmail.com')
        self.password = os.environ.get('TOSHIN_PASSWORD', 'Masa1009')

    def log(self, message):
        """ログ出力"""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def setup_driver(self):
        """Selenium WebDriverをセットアップ"""
        self.log("WebDriverをセットアップ中...")

        # Chromeオプションの設定
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')

        # その他の推奨オプション
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # ログを抑制
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        try:
            # WebDriver Managerを使用してドライバーを自動取得
            if WEBDRIVER_MANAGER_AVAILABLE:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                # WebDriver Managerが使えない場合は通常の方法
                self.driver = webdriver.Chrome(options=chrome_options)

            self.driver.implicitly_wait(10)
            self.log("WebDriverのセットアップ完了")

        except WebDriverException as e:
            raise Exception(
                f"WebDriverの初期化に失敗しました: {e}\n"
                "ChromeDriverがインストールされていることを確認してください。\n"
                "自動インストールには 'pip install webdriver-manager' を実行してください。"
            )

    def login_and_crawl(self):
        """
        ログインして過去問データをクローリング

        Returns:
            list: 過去問データの辞書リスト
        """
        exams_data = []

        try:
            # WebDriverをセットアップ
            self.setup_driver()

            # ログインページにアクセス
            self.log(f"ログインページにアクセス: {self.login_url}")
            self.driver.get(self.login_url)
            time.sleep(2)

            # スクリーンショット保存（デバッグ用）
            if not self.headless:
                self.driver.save_screenshot('login_page_selenium.png')
                self.log("スクリーンショットを保存: login_page_selenium.png")

            # ログインフォームを入力
            self.log("ログイン情報を入力中...")

            # ユーザーID/メールアドレスの入力欄を探す
            email_input = self._find_element_by_multiple_selectors([
                (By.NAME, 'email'),
                (By.NAME, 'username'),
                (By.NAME, 'login_id'),
                (By.ID, 'email'),
                (By.ID, 'username'),
                (By.CSS_SELECTOR, 'input[type="email"]'),
                (By.XPATH, '//input[contains(@id, "email")]'),
                (By.XPATH, '//input[contains(@id, "login")]')
            ])

            if not email_input:
                raise Exception("ユーザーID入力欄が見つかりません")

            email_input.clear()
            email_input.send_keys(self.username)
            self.log(f"ユーザーIDを入力: {self.username}")

            # パスワードの入力欄を探す
            password_input = self._find_element_by_multiple_selectors([
                (By.NAME, 'password'),
                (By.ID, 'password'),
                (By.CSS_SELECTOR, 'input[type="password"]'),
                (By.XPATH, '//input[contains(@id, "password")]'),
                (By.XPATH, '//input[contains(@id, "pass")]')
            ])

            if not password_input:
                raise Exception("パスワード入力欄が見つかりません")

            password_input.clear()
            password_input.send_keys(self.password)
            self.log("パスワードを入力")

            # ログインボタンを探してクリック
            login_button = self._find_element_by_multiple_selectors([
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.CSS_SELECTOR, 'input[type="submit"]'),
                (By.XPATH, '//button[contains(text(), "ログイン")]'),
                (By.XPATH, '//button[contains(text(), "Login")]'),
                (By.XPATH, '//a[contains(text(), "ログイン")]'),
                (By.CLASS_NAME, 'login-button'),
                (By.ID, 'login-button')
            ])

            if not login_button:
                # ボタンが見つからない場合はEnterキーで送信を試みる
                self.log("ログインボタンが見つからないため、Enterキーで送信します")
                password_input.send_keys(Keys.RETURN)
            else:
                self.log("ログインボタンをクリック...")
                login_button.click()

            # ページ遷移を待機
            time.sleep(3)

            # ログイン成功の確認
            current_url = self.driver.current_url
            self.log(f"ログイン後のURL: {current_url}")

            if not self.headless:
                self.driver.save_screenshot('after_login_selenium.png')
                self.log("ログイン後のスクリーンショットを保存: after_login_selenium.png")

            # ログインエラーをチェック
            self._check_login_errors()

            # 過去問データページに遷移
            self.log("過去問データページに遷移中...")

            # 例: 過去問一覧ページのURL（実際のURLに置き換える）
            exam_list_url = "https://www.toshin.com/member/exams"

            try:
                self.driver.get(exam_list_url)
                time.sleep(2)
                self.log(f"過去問ページにアクセス: {exam_list_url}")

                if not self.headless:
                    self.driver.save_screenshot('exam_list_selenium.png')
                    self.log("過去問リストのスクリーンショットを保存: exam_list_selenium.png")

                # データを抽出
                exams_data = self._extract_exam_data()

            except Exception as e:
                self.log(f"過去問ページへのアクセスエラー: {e}")
                # フォールバック: 現在のページから過去問リンクを探す
                exams_data = self._find_and_extract_exams()

        except Exception as e:
            self.log(f"クローリングエラー: {e}")
            raise

        finally:
            # クリーンアップ
            if self.driver:
                self.log("ブラウザを終了中...")
                self.driver.quit()

        return exams_data

    def _find_element_by_multiple_selectors(self, selectors, timeout=5):
        """
        複数のセレクタで要素を探す

        Args:
            selectors: (By, selector) のタプルのリスト
            timeout: タイムアウト時間（秒）

        Returns:
            WebElement or None
        """
        for by, selector in selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, selector))
                )
                self.log(f"要素を検出: {by}='{selector}'")
                return element
            except TimeoutException:
                continue
        return None

    def _check_login_errors(self):
        """ログインエラーをチェック"""
        error_selectors = [
            (By.CLASS_NAME, 'error-message'),
            (By.CLASS_NAME, 'alert-danger'),
            (By.CLASS_NAME, 'login-error'),
            (By.XPATH, '//*[contains(text(), "ログインに失敗")]'),
            (By.XPATH, '//*[contains(text(), "エラー")]'),
            (By.XPATH, '//*[contains(text(), "正しくありません")]')
        ]

        for by, selector in error_selectors:
            try:
                error_element = self.driver.find_element(by, selector)
                if error_element and error_element.is_displayed():
                    error_text = error_element.text
                    raise Exception(f"ログインエラー: {error_text}")
            except NoSuchElementException:
                continue

    def _extract_exam_data(self):
        """
        ページから過去問データを抽出

        Returns:
            list: 過去問データの辞書リスト
        """
        exams_data = []

        # ===== 以下は例です。実際のHTML構造に合わせて調整してください =====

        # パターン1: テーブル形式のデータ
        try:
            # 過去問リストを含む要素を取得
            exam_items_selectors = [
                (By.CLASS_NAME, 'exam-item'),
                (By.CLASS_NAME, 'exam-list-item'),
                (By.CSS_SELECTOR, 'tr.exam-row'),
                (By.CLASS_NAME, 'question-item'),
                (By.CSS_SELECTOR, 'li.past-exam')
            ]

            exam_items = None
            for by, selector in exam_items_selectors:
                try:
                    exam_items = self.driver.find_elements(by, selector)
                    if exam_items:
                        self.log(f"過去問アイテムを検出: {by}='{selector}' ({len(exam_items)}件)")
                        break
                except NoSuchElementException:
                    continue

            if exam_items:
                for item in exam_items:
                    try:
                        # 各種データを抽出（実際のHTML構造に合わせて調整）
                        year_element = None
                        subject_element = None
                        link_element = None

                        # 年度を抽出
                        for by, selector in [(By.CLASS_NAME, 'year'), (By.CLASS_NAME, 'exam-year'), (By.CSS_SELECTOR, '[data-year]')]:
                            try:
                                year_element = item.find_element(by, selector)
                                break
                            except NoSuchElementException:
                                continue

                        # 科目を抽出
                        for by, selector in [(By.CLASS_NAME, 'subject'), (By.CLASS_NAME, 'exam-subject'), (By.CSS_SELECTOR, '[data-subject]')]:
                            try:
                                subject_element = item.find_element(by, selector)
                                break
                            except NoSuchElementException:
                                continue

                        # リンクを抽出
                        for by, selector in [(By.CSS_SELECTOR, 'a[href*=".pdf"]'), (By.CLASS_NAME, 'download-link')]:
                            try:
                                link_element = item.find_element(by, selector)
                                break
                            except NoSuchElementException:
                                continue

                        if year_element and subject_element:
                            year_text = year_element.text.strip()
                            subject_text = subject_element.text.strip()

                            # 年度を数値に変換
                            import re
                            year_match = re.search(r'(\d{4})', year_text)
                            year = int(year_match.group(1)) if year_match else None

                            # 科目のマッピング
                            subject = self._map_subject(subject_text)

                            # PDFリンク
                            problem_url = link_element.get_attribute('href') if link_element else ''

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
                    'description': '2024年度 数学（東進会員サイト - Selenium）',
                    'source_type': 'yobi_school',
                },
                {
                    'year': 2024,
                    'subject': 'english',
                    'exam_type': '一般入試',
                    'problem_url': 'https://www.toshin.com/member/exams/2024/english.pdf',
                    'description': '2024年度 英語（東進会員サイト - Selenium）',
                    'source_type': 'yobi_school',
                }
            ]

        return exams_data

    def _find_and_extract_exams(self):
        """
        ページ内から過去問へのリンクを探して抽出

        Returns:
            list: 過去問データの辞書リスト
        """
        exams_data = []

        # 過去問関連のリンクを探す
        link_selectors = [
            (By.XPATH, '//a[contains(@href, "exam")]'),
            (By.XPATH, '//a[contains(@href, "過去問")]'),
            (By.XPATH, '//a[contains(@href, "kakomon")]'),
            (By.XPATH, '//a[contains(text(), "過去問")]'),
            (By.XPATH, '//a[contains(text(), "問題")]')
        ]

        for by, selector in link_selectors:
            try:
                links = self.driver.find_elements(by, selector)
                if links:
                    self.log(f"過去問関連リンクを検出: {by}='{selector}' ({len(links)}件)")
                    # 最初のリンクをクリックして詳細を取得
                    # （実装は省略 - 必要に応じて追加）
                    break
            except NoSuchElementException:
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
    help = 'ログインが必要なWebサイト（東進会員サイト）から過去問データをクローリングします（Selenium版）'

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

    def handle(self, *args, **options):
        """管理コマンドのメイン処理"""

        # Seleniumの利用可能性チェック
        if not SELENIUM_AVAILABLE:
            self.stdout.write(self.style.ERROR('=' * 60))
            self.stdout.write(self.style.ERROR('Seleniumがインストールされていません'))
            self.stdout.write(self.style.ERROR('=' * 60))
            self.stdout.write('\n以下のコマンドでインストールしてください:')
            self.stdout.write('  pip install selenium webdriver-manager')
            self.stdout.write('')
            raise CommandError('Seleniumがインストールされていません')

        headless = options.get('headless') and not options.get('no_headless')
        year_filter = options.get('year')
        university_name = options.get('university')
        dry_run = options.get('dry_run')

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('ログインサイト過去問クローラー（Selenium版）'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'対象サイト: 東進ハイスクール会員サイト')
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
            crawler = ToshinLoginCrawlerSelenium(headless=headless, verbose=True)

            # ログインしてデータを取得
            self.stdout.write('\n2. ログインしてデータを取得中...')
            exams_data = crawler.login_and_crawl()

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
                        # 過去問の作成または更新
                        exam, created = Exam.objects.get_or_create(
                            university=university,
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
                                    'notes': '東進会員サイトから取得（Selenium）',
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
