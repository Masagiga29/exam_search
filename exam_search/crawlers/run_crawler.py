#!/usr/bin/env python
"""
クローラー実行スクリプト

使用例:
    # すべての有効なクローラーを実行
    python run_crawler.py --all

    # 特定のクローラーを実行
    python run_crawler.py --crawler toshin

    # 特定の大学のみクロール
    python run_crawler.py --university "東京大学"

    # DRY RUNモード（データベースに保存しない）
    python run_crawler.py --dry-run

    # リンク検証のみ実行
    python run_crawler.py --validate-links

    # データ品質レポートを生成
    python run_crawler.py --report
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Django設定の読み込み
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_search.settings')
django.setup()

# クローラーモジュールのインポート
from exam_crawler import UniversityExamCrawler, YobiSchoolAnswerCrawler
from toshin_crawler import ToshinExamCrawler
from crawler_utils import LinkValidator, DuplicateDetector, DataQualityReporter
from crawler_config import (
    CRAWLER_CONFIGS, TARGET_UNIVERSITIES, TARGET_YEARS, LOGGING_CONFIG
)

# ロギング設定
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['level']),
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.FileHandler(LOGGING_CONFIG['file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CrawlerRunner:
    """
    クローラーの実行を管理するクラス
    """
    
    def __init__(self, dry_run=False):
        """
        Args:
            dry_run (bool): Trueの場合、データベースに保存しない
        """
        self.dry_run = dry_run
        self.stats = {
            'start_time': datetime.now(),
            'universities_processed': 0,
            'exams_saved': 0,
            'answers_saved': 0,
            'errors': 0,
        }
    
    def run_toshin_crawler(self, university_filter=None):
        """
        東進ハイスクールクローラーを実行
        
        Args:
            university_filter (str): 特定の大学名でフィルター
        """
        logger.info("=" * 80)
        logger.info("東進ハイスクールクローラー開始")
        logger.info("=" * 80)
        
        config = CRAWLER_CONFIGS['toshin']
        if not config['enabled']:
            logger.warning("東進クローラーは無効化されています")
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
                logger.info(f"\n処理中: {univ_data['name']}")
                self.stats['universities_processed'] += 1
                
                # 過去問データを取得
                # 注意: 実際のURLは設定ファイルや大学データから取得
                exam_url = f"{config['base_url']}/university/{univ_data['name']}"
                exams_data = crawler.crawl_university_exams(
                    exam_url,
                    univ_data['name']
                )
                
                # データベースに保存（DRY RUNでない場合のみ）
                if not self.dry_run:
                    count = crawler.save_exams_to_db(exams_data)
                    self.stats['exams_saved'] += count
                else:
                    logger.info(f"DRY RUN: {len(exams_data)}件の過去問を取得")
                
            except Exception as e:
                logger.error(f"Error processing {univ_data['name']}: {e}")
                self.stats['errors'] += 1
    
    def run_all_crawlers(self, university_filter=None):
        """
        有効なすべてのクローラーを実行
        
        Args:
            university_filter (str): 特定の大学名でフィルター
        """
        logger.info("=" * 80)
        logger.info("全クローラー実行開始")
        logger.info("=" * 80)
        
        # 各クローラーを実行
        for crawler_id, config in CRAWLER_CONFIGS.items():
            if not config['enabled']:
                logger.info(f"スキップ: {config['name']} (無効)")
                continue
            
            logger.info(f"\n実行中: {config['name']}")
            
            if crawler_id == 'toshin':
                self.run_toshin_crawler(university_filter)
            # 他のクローラーも同様に追加
    
    def validate_all_links(self):
        """
        すべてのリンクを検証
        """
        logger.info("=" * 80)
        logger.info("リンク検証開始")
        logger.info("=" * 80)
        
        validator = LinkValidator()
        
        # 過去問リンクの検証
        logger.info("\n過去問PDFリンクを検証中...")
        exam_result = validator.validate_exams()
        logger.info(
            f"結果: {exam_result['valid']}件有効, "
            f"{exam_result['invalid']}件無効"
        )
        
        # 解答ソースリンクの検証
        logger.info("\n解答ソースリンクを検証中...")
        answer_result = validator.validate_answer_sources()
        logger.info(
            f"結果: {answer_result['active']}件有効, "
            f"{answer_result['inactive']}件無効"
        )
    
    def remove_duplicates(self):
        """
        重複データを削除
        """
        logger.info("=" * 80)
        logger.info("重複データ削除開始")
        logger.info("=" * 80)
        
        deleted = DuplicateDetector.remove_duplicates(dry_run=self.dry_run)
        
        if self.dry_run:
            logger.info(f"DRY RUN: {deleted}件の重複を削除できます")
        else:
            logger.info(f"{deleted}件の重複を削除しました")
    
    def generate_report(self):
        """
        データ品質レポートを生成
        """
        logger.info("=" * 80)
        logger.info("データ品質レポート生成")
        logger.info("=" * 80)
        
        reporter = DataQualityReporter()
        report = reporter.generate_report()
        reporter.print_report(report)
    
    def print_stats(self):
        """
        実行統計を表示
        """
        duration = datetime.now() - self.stats['start_time']
        
        logger.info("\n" + "=" * 80)
        logger.info("実行統計")
        logger.info("=" * 80)
        logger.info(f"開始時刻: {self.stats['start_time']}")
        logger.info(f"実行時間: {duration}")
        logger.info(f"処理大学数: {self.stats['universities_processed']}")
        logger.info(f"保存過去問数: {self.stats['exams_saved']}")
        logger.info(f"保存解答数: {self.stats['answers_saved']}")
        logger.info(f"エラー数: {self.stats['errors']}")
        logger.info("=" * 80)


def main():
    """
    メイン実行関数
    """
    parser = argparse.ArgumentParser(
        description='過去問クローラー実行スクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # すべてのクローラーを実行
  python run_crawler.py --all

  # 特定のクローラーを実行
  python run_crawler.py --crawler toshin

  # 特定の大学のみ
  python run_crawler.py --university "東京大学"

  # DRY RUNモード
  python run_crawler.py --all --dry-run

  # リンク検証のみ
  python run_crawler.py --validate-links

  # レポート生成
  python run_crawler.py --report
        """
    )
    
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
    
    args = parser.parse_args()
    
    # 引数チェック
    if not any([args.all, args.crawler, args.validate_links, 
                args.remove_duplicates, args.report]):
        parser.print_help()
        sys.exit(1)
    
    # クローラー実行
    runner = CrawlerRunner(dry_run=args.dry_run)
    
    try:
        if args.all:
            runner.run_all_crawlers(args.university)
        
        elif args.crawler == 'toshin':
            runner.run_toshin_crawler(args.university)
        
        if args.validate_links:
            runner.validate_all_links()
        
        if args.remove_duplicates:
            runner.remove_duplicates()
        
        if args.report:
            runner.generate_report()
        
        # 統計表示
        runner.print_stats()
    
    except KeyboardInterrupt:
        logger.warning("\n実行が中断されました")
        runner.print_stats()
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        runner.print_stats()
        sys.exit(1)


if __name__ == "__main__":
    main()
