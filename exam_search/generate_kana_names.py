#!/usr/bin/env python3
"""
大学名からかな名を自動生成するスクリプト
"""

import os
import sys
import django
from pykakasi import kakasi

# Djangoの設定を読み込む
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_search.settings')
django.setup()

from exams.models import University


def generate_kana_name(name):
    """
    大学名からかな名を生成
    """
    kks = kakasi()
    result = kks.convert(name)
    kana = ''.join([item['hira'] for item in result])
    return kana


def update_all_kana_names():
    """
    すべての大学のかな名を更新
    """
    print("=" * 80)
    print("大学名のかな名を自動生成します...")
    print("=" * 80)

    universities = University.objects.all()
    updated_count = 0
    skipped_count = 0

    for univ in universities:
        # 既にかな名がある場合はスキップ
        if univ.name_kana:
            skipped_count += 1
            continue

        # かな名を生成
        kana = generate_kana_name(univ.name)
        univ.name_kana = kana
        univ.save()

        print(f"✓ {univ.name} → {kana}")
        updated_count += 1

    print("\n" + "=" * 80)
    print(f"完了:")
    print(f"  - 更新: {updated_count}校")
    print(f"  - スキップ（既存）: {skipped_count}校")
    print("=" * 80)


if __name__ == '__main__':
    update_all_kana_names()
    print("\n✓ かな名の生成が完了しました！")
