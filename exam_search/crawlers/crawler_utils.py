"""
クローラーユーティリティ

このモジュールは、クローリング後のデータメンテナンス機能を提供します:
- PDFリンクの有効性チェック
- 重複データの検出と削除
- データ品質レポートの生成
"""

import os
import sys
import requests
from datetime import datetime, timedelta
import logging

# Django設定の読み込み（管理コマンドから呼ばれる場合は不要）
try:
    from exams.models import University, Exam, AnswerSource
    from django.db.models import Count
    from django.utils import timezone
except:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_search.settings')
    django.setup()
    from exams.models import University, Exam, AnswerSource
    from django.db.models import Count
    from django.utils import timezone

logger = logging.getLogger(__name__)


class LinkValidator:
    """
    PDFリンクやWebページの有効性をチェック
    """
    
    def __init__(self, timeout=10):
        """
        Args:
            timeout (int): リクエストタイムアウト（秒）
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; LinkChecker/1.0)'
        })
    
    def check_url(self, url):
        """
        URLの有効性をチェック
        
        Args:
            url (str): チェック対象のURL
            
        Returns:
            dict: {
                'is_valid': bool,
                'status_code': int,
                'error': str or None
            }
        """
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            
            return {
                'is_valid': response.status_code == 200,
                'status_code': response.status_code,
                'error': None
            }
        
        except requests.RequestException as e:
            logger.warning(f"Link check failed for {url}: {e}")
            return {
                'is_valid': False,
                'status_code': None,
                'error': str(e)
            }
    
    def validate_exams(self, batch_size=50):
        """
        データベース内のすべてのExamのPDFリンクを検証
        
        Args:
            batch_size (int): 一度にチェックする件数
            
        Returns:
            dict: 検証結果の統計
        """
        logger.info("Validating exam PDF links...")
        
        exams = Exam.objects.filter(problem_url__isnull=False)
        total = exams.count()
        
        valid_count = 0
        invalid_count = 0
        invalid_exams = []
        
        for i, exam in enumerate(exams, 1):
            result = self.check_url(exam.problem_url)
            
            if result['is_valid']:
                valid_count += 1
                exam.is_verified = True
                exam.save(update_fields=['is_verified'])
            else:
                invalid_count += 1
                invalid_exams.append({
                    'exam': exam,
                    'error': result['error'],
                    'status_code': result['status_code']
                })
                exam.is_verified = False
                exam.save(update_fields=['is_verified'])
            
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{total} ({i/total*100:.1f}%)")
        
        logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid")
        
        return {
            'total': total,
            'valid': valid_count,
            'invalid': invalid_count,
            'invalid_exams': invalid_exams
        }
    
    def validate_answer_sources(self):
        """
        AnswerSourceのリンクを検証
        """
        logger.info("Validating answer source links...")
        
        sources = AnswerSource.objects.filter(is_active=True)
        total = sources.count()
        
        active_count = 0
        inactive_count = 0
        
        for i, source in enumerate(sources, 1):
            result = self.check_url(source.answer_url)
            
            if result['is_valid']:
                active_count += 1
                source.is_active = True
                source.last_checked_at = timezone.now()
            else:
                inactive_count += 1
                source.is_active = False
                source.last_checked_at = timezone.now()
            
            source.save(update_fields=['is_active', 'last_checked_at'])
            
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{total} ({i/total*100:.1f}%)")
        
        logger.info(f"Validation complete: {active_count} active, {inactive_count} inactive")
        
        return {
            'total': total,
            'active': active_count,
            'inactive': inactive_count
        }


class DuplicateDetector:
    """
    重複データの検出と削除
    """
    
    @staticmethod
    def find_duplicate_exams():
        """
        重複している過去問を検出
        
        Returns:
            list: 重複しているExamのリスト
        """
        logger.info("Detecting duplicate exams...")
        
        # 同じ大学・年度・科目・試験種別の組み合わせでグループ化
        duplicates = Exam.objects.values(
            'university', 'year', 'subject', 'exam_type'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        duplicate_groups = []
        
        for dup in duplicates:
            exams = Exam.objects.filter(
                university_id=dup['university'],
                year=dup['year'],
                subject=dup['subject'],
                exam_type=dup['exam_type']
            ).order_by('created_at')
            
            duplicate_groups.append(list(exams))
            logger.warning(f"Found {dup['count']} duplicates: {exams.first()}")
        
        logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups
    
    @staticmethod
    def remove_duplicates(dry_run=True):
        """
        重複データを削除（最も古いものを残す）
        
        Args:
            dry_run (bool): Trueの場合は実際には削除しない
            
        Returns:
            int: 削除された件数
        """
        duplicate_groups = DuplicateDetector.find_duplicate_exams()
        
        deleted_count = 0
        
        for group in duplicate_groups:
            # 最初（最も古い）のものを残して、残りを削除
            to_keep = group[0]
            to_delete = group[1:]
            
            logger.info(f"Keeping: {to_keep} (created: {to_keep.created_at})")
            
            for exam in to_delete:
                logger.info(f"  Deleting: {exam} (created: {exam.created_at})")
                
                if not dry_run:
                    exam.delete()
                    deleted_count += 1
        
        if dry_run:
            logger.info(f"DRY RUN: Would delete {len(to_delete)} duplicates")
        else:
            logger.info(f"Deleted {deleted_count} duplicates")
        
        return deleted_count


class DataQualityReporter:
    """
    データ品質レポートを生成
    """
    
    @staticmethod
    def generate_report():
        """
        データ品質レポートを生成
        
        Returns:
            dict: レポートデータ
        """
        logger.info("Generating data quality report...")
        
        report = {
            'timestamp': datetime.now(),
            'universities': {},
            'exams': {},
            'answer_sources': {},
        }
        
        # 大学の統計
        universities = University.objects.all()
        report['universities'] = {
            'total': universities.count(),
            'with_exams': universities.annotate(
                exam_count=Count('exams')
            ).filter(exam_count__gt=0).count(),
        }
        
        # 過去問の統計
        exams = Exam.objects.all()
        report['exams'] = {
            'total': exams.count(),
            'verified': exams.filter(is_verified=True).count(),
            'with_pdf': exams.exclude(problem_url='').count(),
            'with_answers': exams.annotate(
                answer_count=Count('answer_sources')
            ).filter(answer_count__gt=0).count(),
            'by_year': {},
            'by_subject': {},
        }
        
        # 年度別統計
        for year in range(2020, 2026):
            count = exams.filter(year=year).count()
            if count > 0:
                report['exams']['by_year'][year] = count
        
        # 科目別統計
        for subject_code, subject_name in Exam.SUBJECT_CHOICES:
            count = exams.filter(subject=subject_code).count()
            if count > 0:
                report['exams']['by_subject'][subject_name] = count
        
        # 解答ソースの統計
        answer_sources = AnswerSource.objects.all()
        report['answer_sources'] = {
            'total': answer_sources.count(),
            'active': answer_sources.filter(is_active=True).count(),
            'with_detailed_explanation': answer_sources.filter(
                has_detailed_explanation=True
            ).count(),
            'with_video': answer_sources.filter(
                has_video_explanation=True
            ).count(),
            'by_provider': {},
        }
        
        # 予備校別統計
        for provider in answer_sources.values('provider_name').distinct():
            count = answer_sources.filter(
                provider_name=provider['provider_name']
            ).count()
            report['answer_sources']['by_provider'][provider['provider_name']] = count
        
        return report
    
    @staticmethod
    def print_report(report):
        """
        レポートをコンソールに出力
        
        Args:
            report (dict): generate_report()の戻り値
        """
        print("\n" + "=" * 80)
        print("データ品質レポート")
        print("=" * 80)
        print(f"生成日時: {report['timestamp']}")
        print()
        
        print("【大学】")
        print(f"  総数: {report['universities']['total']}")
        print(f"  過去問あり: {report['universities']['with_exams']}")
        print()
        
        print("【過去問】")
        print(f"  総数: {report['exams']['total']}")
        print(f"  検証済み: {report['exams']['verified']}")
        print(f"  PDF有り: {report['exams']['with_pdf']}")
        print(f"  解答有り: {report['exams']['with_answers']}")
        print()
        
        print("  年度別:")
        for year, count in sorted(report['exams']['by_year'].items()):
            print(f"    {year}年: {count}件")
        print()
        
        print("  科目別:")
        for subject, count in sorted(report['exams']['by_subject'].items()):
            print(f"    {subject}: {count}件")
        print()
        
        print("【解答ソース】")
        print(f"  総数: {report['answer_sources']['total']}")
        print(f"  有効: {report['answer_sources']['active']}")
        print(f"  詳細解説あり: {report['answer_sources']['with_detailed_explanation']}")
        print(f"  動画解説あり: {report['answer_sources']['with_video']}")
        print()
        
        print("  予備校別:")
        for provider, count in sorted(report['answer_sources']['by_provider'].items()):
            print(f"    {provider}: {count}件")
        
        print("=" * 80)


def main():
    """
    メイン実行関数 - 各種メンテナンスタスクを実行
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("\n過去問データベースメンテナンスツール")
    print("=" * 80)
    print("1. リンク検証")
    print("2. 重複検出")
    print("3. 重複削除（DRY RUN）")
    print("4. データ品質レポート")
    print("0. 終了")
    print("=" * 80)
    
    choice = input("\n選択してください: ")
    
    if choice == "1":
        # リンク検証
        validator = LinkValidator()
        
        print("\n過去問PDFリンクを検証中...")
        exam_result = validator.validate_exams()
        print(f"結果: {exam_result['valid']}件有効, {exam_result['invalid']}件無効")
        
        print("\n解答ソースリンクを検証中...")
        answer_result = validator.validate_answer_sources()
        print(f"結果: {answer_result['active']}件有効, {answer_result['inactive']}件無効")
    
    elif choice == "2":
        # 重複検出
        duplicates = DuplicateDetector.find_duplicate_exams()
        print(f"\n{len(duplicates)}グループの重複が見つかりました")
    
    elif choice == "3":
        # 重複削除（DRY RUN）
        deleted = DuplicateDetector.remove_duplicates(dry_run=True)
        print(f"\n{deleted}件の重複を削除できます（DRY RUN）")
        
        confirm = input("\n実際に削除しますか？ (yes/no): ")
        if confirm.lower() == "yes":
            deleted = DuplicateDetector.remove_duplicates(dry_run=False)
            print(f"{deleted}件の重複を削除しました")
    
    elif choice == "4":
        # データ品質レポート
        reporter = DataQualityReporter()
        report = reporter.generate_report()
        reporter.print_report(report)
    
    else:
        print("終了します")


if __name__ == "__main__":
    main()
