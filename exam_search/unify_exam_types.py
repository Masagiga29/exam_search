#!/usr/bin/env python3
"""
試験種別を統一するスクリプト
「一般入試（前期）」「一般入試前期」「general」などを「一般入試」に統一
"""

import os
import sys
import django

# Djangoの設定を読み込む
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_search.settings')
django.setup()

from exams.models import Exam


def unify_exam_types():
    """
    試験種別を統一
    """
    print("=" * 80)
    print("試験種別を統一します...")
    print("=" * 80)

    # 統一するマッピング
    unify_mapping = {
        '一般入試（前期）': '一般入試',
        '一般入試前期': '一般入試',
        '一般入試(前期)': '一般入試',
        'general': '一般入試',
        '前期': '一般入試',
        '前期日程': '一般入試',
    }

    total_updated = 0

    for old_type, new_type in unify_mapping.items():
        exams = Exam.objects.filter(exam_type=old_type)
        count = exams.count()

        if count > 0:
            exams.update(exam_type=new_type)
            print(f"✓ '{old_type}' → '{new_type}': {count}件")
            total_updated += count

    print("\n" + "=" * 80)
    print(f"統一完了: {total_updated}件を更新しました")
    print("=" * 80)

    # 更新後の統計を表示
    print("\n=== 更新後の試験種別 ===")
    from django.db.models import Count
    exam_types = Exam.objects.values('exam_type').annotate(count=Count('id')).order_by('-count')

    for et in exam_types:
        print(f"  {et['exam_type']:30s}: {et['count']}件")


if __name__ == '__main__':
    unify_exam_types()
    print("\n✓ 試験種別の統一が完了しました！")
