#!/usr/bin/env python3
"""
過去問掲載状況チェック結果をデータベースに登録するスクリプト
"""

import os
import sys
import django
import csv
from datetime import datetime

# Djangoの設定を読み込む
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_search.settings')
django.setup()

from exams.models import University


def import_pastpaper_results(csv_file='pastpaper_check_results.csv'):
    """
    CSVファイルから過去問掲載結果をインポート
    """
    print("=" * 80)
    print("過去問掲載状況結果をインポートします...")
    print("=" * 80)

    if not os.path.exists(csv_file):
        print(f"エラー: CSVファイルが見つかりません: {csv_file}")
        return

    updated_count = 0
    not_found_count = 0

    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            univ_name = row['大学名']
            has_pastpaper = row['過去問ページ発見'] == 'あり'
            pastpaper_url = row['過去問ページURL'] if row['過去問ページURL'] else ''
            pastpaper_years = row['掲載年度'] if row['掲載年度'] else ''
            has_three_years = row['3年分掲載'] == 'あり'
            note = row['備考'] if row['備考'] else ''

            # データベースから大学を検索
            university = University.objects.filter(name=univ_name).first()

            if university:
                # 過去問掲載情報を更新
                university.has_official_pastpaper = has_pastpaper

                # official_urlが空の場合は設定
                if not university.official_url and row['URL']:
                    university.official_url = row['URL']

                university.pastpaper_url = pastpaper_url
                university.pastpaper_years = pastpaper_years
                university.pastpaper_checked_at = datetime.now()

                # 備考を設定
                if has_three_years:
                    university.pastpaper_note = "過去3年分以上掲載"
                elif has_pastpaper and pastpaper_years:
                    year_count = len(pastpaper_years.split(','))
                    university.pastpaper_note = f"{year_count}年分掲載"
                elif has_pastpaper:
                    university.pastpaper_note = "過去問ページあり（年度不明）"
                else:
                    university.pastpaper_note = note if note else "過去問ページ未発見"

                university.save()

                status = "✓" if has_pastpaper else "×"
                years_info = f"({pastpaper_years})" if pastpaper_years else ""
                print(f"{status} {univ_name}: {university.pastpaper_note} {years_info}")
                updated_count += 1
            else:
                print(f"⚠ {univ_name}: データベースに未登録")
                not_found_count += 1

    print("\n" + "=" * 80)
    print(f"インポート完了:")
    print(f"  - 更新: {updated_count}校")
    print(f"  - 未登録: {not_found_count}校")
    print("=" * 80)

    # 統計を表示
    print("\n=== 統計 ===")
    total_with_pastpaper = University.objects.filter(has_official_pastpaper=True).count()
    total_universities = University.objects.count()
    print(f"公式HP過去問掲載: {total_with_pastpaper}校 / {total_universities}校")


if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'pastpaper_check_results.csv'
    import_pastpaper_results(csv_file)
    print("\n✓ データベースへの登録が完了しました！")
