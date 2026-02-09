#!/usr/bin/env python3
"""
河合塾の解答速報データをDjangoデータベースに登録するスクリプト
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

from exams.models import University, Exam, AnswerSource

# 大学名とコードのマッピング
UNIVERSITY_MAPPING = {
    't01': '東京大学',
    'k01': '京都大学',
    'n01': '名古屋大学',
    'hr1': '広島大学',
    'ky1': '九州大学',
    'ho1': '北海道大学',
    'th1': '東北大学',
    'gk1': '東京科学大学',  # 医歯学系
    'gk2': '東京科学大学',  # 理工学系
    'ht1': '一橋大学',
    'ha1': '大阪大学',
    'kb1': '神戸大学',
    'k11': '慶應義塾大学',  # 文学部
    'k12': '慶應義塾大学',  # 法学部
    'k14': '慶應義塾大学',  # 経済学部
    'k15': '慶應義塾大学',  # 商学部
    'k16': '慶應義塾大学',  # 理工学部
    'k17': '慶應義塾大学',  # 医学部
    'w01': '早稲田大学',  # 文学部
    'w02': '早稲田大学',  # 文科構想学部
    'w06': '早稲田大学',  # 法学部
    'w09': '早稲田大学',  # 理工学部
    'd01': '同志社大学',
    'd02': '同志社大学',
    'rt1': '立命館大学',
    'ks1': '関西大学',
    'kg1': '関西学院大学',
}

# 学部・学科のマッピング
DEPARTMENT_MAPPING = {
    'gk1': '医歯学系',
    'gk2': '理工学系',
    'k11': '文学部',
    'k12': '法学部',
    'k14': '経済学部',
    'k15': '商学部',
    'k16': '理工学部',
    'k17': '医学部',
    'w01': '文学部',
    'w02': '文科構想学部',
    'w06': '法学部',
    'w09': '基幹理工・創造理工・先進理工学部',
    'd01': '全学部日程（文系）',
    'd02': '全学部日程（理系）',
    'rt1': '全学統一方式',
    'ks1': '全学部日程',
    'kg1': '全学部日程',
}

# PDFファイル名から科目を推測（簡易版）
SUBJECT_CODE_MAPPING = {
    '11': 'english',  # 英語
    '21': 'math',     # 数学（文系）
    '22': 'math',     # 数学（理系）
    '31': 'japanese', # 国語
    '32': 'japanese', # 国語（第二問）
    '41': 'history',  # 世界史
    '42': 'history',  # 日本史
    '43': 'geography',# 地理
    '51': 'physics',  # 物理
    '52': 'chemistry',# 化学
    '53': 'biology',  # 生物
}


def get_or_create_university(code):
    """
    大学を取得または作成
    """
    univ_name = UNIVERSITY_MAPPING.get(code, f'Unknown ({code})')
    university, created = University.objects.get_or_create(
        name=univ_name,
        defaults={
            'school_type': 'university',
            'official_url': f'https://www.kawai-juku.ac.jp/nyushi/honshi/25/{code}/'
        }
    )
    if created:
        print(f"✓ 大学を登録: {univ_name}")
    return university


def extract_subject_from_filename(pdf_url, code):
    """
    PDFファイル名から科目を推測
    """
    # ファイル名から科目コードを抽出（例: t01-11c.pdf -> 11）
    import re
    match = re.search(r'[-/](\d{2})[ac]\.pdf', pdf_url)
    if match:
        subject_code = match.group(1)
        return SUBJECT_CODE_MAPPING.get(subject_code, 'other')
    return 'other'


def import_pdf_links(csv_file):
    """
    CSVファイルからPDFリンクをインポート
    """
    print("=" * 80)
    print("河合塾 解答速報データをインポートします...")
    print("=" * 80)

    # CSVファイルを読み込む
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # 大学コードごとにグループ化
    by_university = {}
    for row in rows:
        code = row['code']
        if code not in by_university:
            by_university[code] = []
        by_university[code].append(row)

    total_exams = 0
    total_links = 0

    for code, links in by_university.items():
        university = get_or_create_university(code)
        department = DEPARTMENT_MAPPING.get(code, '')

        # 科目ごとにグループ化
        by_subject = {}
        for link in links:
            subject = extract_subject_from_filename(link['pdf_url'], code)
            if subject not in by_subject:
                by_subject[subject] = []
            by_subject[subject].append(link)

        # 各科目ごとにExamレコードを作成
        for subject, subject_links in by_subject.items():
            # Examレコードを取得または作成
            exam, created = Exam.objects.get_or_create(
                university=university,
                year=2025,
                subject=subject,
                exam_type='一般入試',
                department=department,
                defaults={
                    'source_type': 'yobi_school',
                    'is_verified': True,
                    'scraped_at': datetime.now(),
                    'description': '河合塾 解答速報より',
                }
            )

            if created:
                total_exams += 1
                print(f"  ✓ 過去問登録: {university.name} {department} {subject}")

            # 各リンクをAnswerSourceとして登録
            for link in subject_links:
                link_text = link['link_text']
                pdf_url = link['pdf_url']

                # 解答例か分析かを判定
                is_answer = '解答' in link_text
                has_analysis = '分析' in link_text

                answer_source, created = AnswerSource.objects.get_or_create(
                    exam=exam,
                    answer_url=pdf_url,
                    defaults={
                        'provider_name': '河合塾',
                        'has_detailed_explanation': has_analysis,
                        'reliability_score': 9,
                        'notes': link_text,
                        'is_active': True,
                        'last_checked_at': datetime.now(),
                    }
                )

                if created:
                    total_links += 1

    print("\n" + "=" * 80)
    print(f"インポート完了:")
    print(f"  - {len(by_university)} 大学")
    print(f"  - {total_exams} 過去問")
    print(f"  - {total_links} PDFリンク")
    print("=" * 80)


if __name__ == '__main__':
    csv_file = '/Users/mf/Downloads/outputs/pdf_links.csv'

    if not os.path.exists(csv_file):
        print(f"エラー: CSVファイルが見つかりません: {csv_file}")
        sys.exit(1)

    import_pdf_links(csv_file)
    print("\n✓ データベースへの登録が完了しました！")
