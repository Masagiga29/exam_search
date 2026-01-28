"""
Django管理コマンド: クローラー実行

使用例:
    # すべての有効なクローラーを実行
    python manage.py run_crawler --all

    # 特定のクローラーを実行
    python manage.py run_crawler --crawler toshin

    # 特定の大学のみクロール
    python manage.py run_crawler --university "東京大学"

    # DRY RUNモード（データベースに保存しない）
    python manage.py run_crawler --dry-run

    # リンク検証のみ実行
    python manage.py run_crawler --validate-links

    # データ品質レポートを生成
    python manage.py run_crawler --report
"""

import os
import sys
import logging
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# crawlersディレクトリをパスに追加
CRAWLERS_DIR = os.path.join(settings.BASE_DIR, 'crawlers')
if CRAWLERS_DIR not in sys.path:
    sys.path.insert(0, CRAWLERS_DIR)

try:
    # クローラーモジュールのインポート
    from exam_crawler import UniversityExamCrawler, YobiSchoolAnswerCrawler
    from toshin_crawler import ToshinExamCrawler
    from crawler_utils import LinkValidator, DuplicateDetector, DataQualityReporter
    from crawler_config import (
        CRAWLER_CONFIGS, TARGET_UNIVERSITIES, TARGET_YEARS, LOGGING_CONFIG
    )
    CRAWLERS_AVAILABLE = True
except ImportError as e:
    CRAWLERS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class CrawlerRunner:
    """
    クローラーの実行を管理するクラス
    """

    def __init__(self, command, dry_run=False):
        """
        Args:
            command: Django管理コマンドのインスタンス
            dry_run (bool): Trueの場合、データベースに保存しない
        """
        self.command = command
        self.dry_run = dry_run
        self.stats = {
            'start_time': datetime.now(),
            'universities_processed': 0,
            'exams_saved': 0,
            'answers_saved': 0,
            'errors': 0,
        }

    def log(self, message, level='info'):
        """ログ出力"""
        if level == 'error':
            self.command.stdout.write(self.command.style.ERROR(message))
        elif level == 'warning':
            self.command.stdout.write(self.command.style.WARNING(message))
        elif level == 'success':
            self.command.stdout.write(self.command.style.SUCCESS(message))
        else:
            self.command.stdout.write(message)

    def run_toshin_crawler(self, university_filter=None):
        """
        東進ハイスクールクローラーを実行

        Args:
            university_filter (str): 特定の大学名でフィルター
        """
        self.log("=" * 80)
        self.log("東進ハイスクールクローラー開始", 'success')
        self.log("=" * 80)

        config = CRAWLER_CONFIGS['toshin']
        if not config['enabled']:
            self.log("東進クローラーは無効化されています", 'warning')
            return

        crawler = ToshinExamCrawler(delay=config['delay'])

        # 対象大学をフィルター
        universities = TARGET_UNIVERSITIES
        if university_filter:
            universities = [
                u for u in universities
                if university_filter in u['name']
            ]

        for univ_data in universities:
            try:
                self.log(f"\n処理中: {univ_data['name']}")
                self.stats['universities_processed'] += 1

                # 過去問データを取得
                exam_url = f"{config['base_url']}/university/{univ_data['name']}"
                exams_data = crawler.crawl_university_exams(
                    exam_url,
                    univ_data['name']
                )

                # データベースに保存（DRY RUNでない場合のみ）
                if not self.dry_run:
                    count = crawler.save_exams_to_db(exams_data)
                    self.stats['exams_saved'] += count
                    self.log(f"✓ {count}件の過去問を保存", 'success')
                else:
                    self.log(f"[DRY RUN] {len(exams_data)}件の過去問を取得", 'warning')

            except Exception as e:
                self.log(f"✗ Error processing {univ_data['name']}: {e}", 'error')
                self.stats['errors'] += 1

    def run_all_crawlers(self, university_filter=None):
        """
        有効なすべてのクローラーを実行

        Args:
            university_filter (str): 特定の大学名でフィルター
        """
        self.log("=" * 80)
        self.log("全クローラー実行開始", 'success')
        self.log("=" * 80)

        # 各クローラーを実行
        for crawler_id, config in CRAWLER_CONFIGS.items():
            if not config['enabled']:
                self.log(f"スキップ: {config['name']} (無効)", 'warning')
                continue

            self.log(f"\n実行中: {config['name']}")

            if crawler_id == 'toshin':
                self.run_toshin_crawler(university_filter)
            # 他のクローラーも同様に追加

    def validate_all_links(self):
        """
        すべてのリンクを検証
        """
        self.log("=" * 80)
        self.log("リンク検証開始", 'success')
        self.log("=" * 80)

        validator = LinkValidator()

        # 過去問リンクの検証
        self.log("\n過去問PDFリンクを検証中...")
        exam_result = validator.validate_exams()
        self.log(
            f"結果: {exam_result['valid']}件有効, "
            f"{exam_result['invalid']}件無効",
            'success'
        )

        # 解答ソースリンクの検証
        self.log("\n解答ソースリンクを検証中...")
        answer_result = validator.validate_answer_sources()
        self.log(
            f"結果: {answer_result['active']}件有効, "
            f"{answer_result['inactive']}件無効",
            'success'
        )

    def remove_duplicates(self):
        """
        重複データを削除
        """
        self.log("=" * 80)
        self.log("重複データ削除開始", 'success')
        self.log("=" * 80)

        deleted = DuplicateDetector.remove_duplicates(dry_run=self.dry_run)

        if self.dry_run:
            self.log(f"[DRY RUN] {deleted}件の重複を削除できます", 'warning')
        else:
            self.log(f"✓ {deleted}件の重複を削除しました", 'success')

    def generate_report(self):
        """
        データ品質レポートを生成
        """
        self.command.stdout.write("=" * 80)
        self.command.stdout.write(self.command.style.SUCCESS("データ品質レポート生成"))
        self.command.stdout.write("=" * 80)

        reporter = DataQualityReporter()
        report = reporter.generate_report()

        # レポートを手動で出力
        self.command.stdout.write("\n" + "=" * 80)
        self.command.stdout.write("データ品質レポート")
        self.command.stdout.write("=" * 80)
        self.command.stdout.write(f"生成日時: {report['timestamp']}")
        self.command.stdout.write("")

        self.command.stdout.write("【大学】")
        self.command.stdout.write(f"  総数: {report['universities']['total']}")
        self.command.stdout.write(f"  過去問あり: {report['universities']['with_exams']}")
        self.command.stdout.write("")

        self.command.stdout.write("【過去問】")
        self.command.stdout.write(f"  総数: {report['exams']['total']}")
        self.command.stdout.write(f"  検証済み: {report['exams']['verified']}")
        self.command.stdout.write(f"  PDF有り: {report['exams']['with_pdf']}")
        self.command.stdout.write(f"  解答有り: {report['exams']['with_answers']}")
        self.command.stdout.write("")

        if report['exams']['by_year']:
            self.command.stdout.write("  年度別:")
            for year, count in sorted(report['exams']['by_year'].items()):
                self.command.stdout.write(f"    {year}年: {count}件")
            self.command.stdout.write("")

        if report['exams']['by_subject']:
            self.command.stdout.write("  科目別:")
            for subject, count in sorted(report['exams']['by_subject'].items()):
                self.command.stdout.write(f"    {subject}: {count}件")
            self.command.stdout.write("")

        self.command.stdout.write("【解答ソース】")
        self.command.stdout.write(f"  総数: {report['answer_sources']['total']}")
        self.command.stdout.write(f"  有効: {report['answer_sources']['active']}")
        self.command.stdout.write(f"  詳細解説あり: {report['answer_sources']['with_detailed_explanation']}")
        self.command.stdout.write(f"  動画解説あり: {report['answer_sources']['with_video']}")
        self.command.stdout.write("")

        if report['answer_sources']['by_provider']:
            self.command.stdout.write("  予備校別:")
            for provider, count in sorted(report['answer_sources']['by_provider'].items()):
                self.command.stdout.write(f"    {provider}: {count}件")

        self.command.stdout.write("=" * 80)

    def print_stats(self):
        """
        実行統計を表示
        """
        duration = datetime.now() - self.stats['start_time']

        self.command.stdout.write("\n" + "=" * 80)
        self.command.stdout.write(self.command.style.SUCCESS("実行統計"))
        self.command.stdout.write("=" * 80)
        self.command.stdout.write(f"開始時刻: {self.stats['start_time']}")
        self.command.stdout.write(f"実行時間: {duration}")
        self.command.stdout.write(f"処理大学数: {self.stats['universities_processed']}")
        self.command.stdout.write(f"保存過去問数: {self.stats['exams_saved']}")
        self.command.stdout.write(f"保存解答数: {self.stats['answers_saved']}")
        self.command.stdout.write(f"エラー数: {self.stats['errors']}")
        self.command.stdout.write("=" * 80)


class Command(BaseCommand):
    help = '過去問クローラーを実行します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='すべての有効なクローラーを実行'
        )

        parser.add_argument(
            '--crawler',
            type=str,
            choices=['toshin', 'kawaijuku', 'sundai'],
            help='実行するクローラーを指定'
        )

        parser.add_argument(
            '--university',
            type=str,
            help='クロール対象の大学名（部分一致）'
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='DRY RUNモード（データベースに保存しない）'
        )

        parser.add_argument(
            '--validate-links',
            action='store_true',
            help='リンクの有効性を検証'
        )

        parser.add_argument(
            '--remove-duplicates',
            action='store_true',
            help='重複データを削除'
        )

        parser.add_argument(
            '--report',
            action='store_true',
            help='データ品質レポートを生成'
        )

    def handle(self, *args, **options):
        """管理コマンドのメイン処理"""

        # クローラーモジュールが利用可能か確認
        if not CRAWLERS_AVAILABLE:
            self.command.stdout.write(self.style.ERROR('=' * 80))
            self.command.stdout.write(self.style.ERROR('クローラーモジュールのインポートエラー'))
            self.command.stdout.write(self.style.ERROR('=' * 80))
            self.command.stdout.write(self.style.ERROR(f'\nエラー詳細: {IMPORT_ERROR}'))
            self.command.stdout.write(self.style.WARNING('\n必要なファイルが見つかりません。以下を確認してください:'))
            self.command.stdout.write('  - crawlers/exam_crawler.py')
            self.command.stdout.write('  - crawlers/toshin_crawler.py')
            self.command.stdout.write('  - crawlers/crawler_utils.py')
            self.command.stdout.write('  - crawlers/crawler_config.py')
            self.command.stdout.write(self.style.WARNING('\n代わりに以下のコマンドを使用できます:'))
            self.command.stdout.write('  python manage.py crawl_exam_data')
            raise CommandError('クローラーモジュールが見つかりません')

        # 引数チェック
        if not any([
            options['all'],
            options['crawler'],
            options['validate_links'],
            options['remove_duplicates'],
            options['report']
        ]):
            self.stdout.write(self.style.WARNING('オプションを指定してください'))
            self.stdout.write('\n使用例:')
            self.stdout.write('  python manage.py run_crawler --all')
            self.stdout.write('  python manage.py run_crawler --crawler toshin')
            self.stdout.write('  python manage.py run_crawler --validate-links')
            self.stdout.write('  python manage.py run_crawler --report')
            self.stdout.write('\nヘルプを表示: python manage.py run_crawler --help')
            return

        dry_run = options.get('dry_run')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN モード: データベースには保存しません\n'))

        # クローラー実行
        runner = CrawlerRunner(command=self, dry_run=dry_run)

        try:
            if options['all']:
                runner.run_all_crawlers(options.get('university'))

            elif options['crawler'] == 'toshin':
                runner.run_toshin_crawler(options.get('university'))

            if options['validate_links']:
                runner.validate_all_links()

            if options['remove_duplicates']:
                runner.remove_duplicates()

            if options['report']:
                runner.generate_report()

            # 統計表示
            runner.print_stats()

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n実行が中断されました"))
            runner.print_stats()
            raise CommandError('実行が中断されました')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"エラーが発生しました: {e}"))
            runner.print_stats()
            raise CommandError(f'エラー: {e}')
