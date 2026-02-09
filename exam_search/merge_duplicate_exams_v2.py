#!/usr/bin/env python3
"""
重複する過去問を統合するスクリプト（改良版）
学部フィールドの違いも考慮して統合
"""

import os
import sys
import django
from collections import defaultdict

# Djangoの設定を読み込む
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_search.settings')
django.setup()

from exams.models import University, Exam, AnswerSource


def merge_duplicate_exams_v2():
    """
    重複する過去問を統合（学部の違いも統合）
    """
    print("=" * 80)
    print("重複する過去問を統合します（学部違いも含む）...")
    print("=" * 80)

    # 大学・年度・科目・試験種別ごとにグループ化（学部は無視）
    exam_groups = defaultdict(list)

    for exam in Exam.objects.all():
        # グループ化のキー（学部を除外）
        key = (
            exam.university_id,
            exam.year,
            exam.subject,
            exam.exam_type
        )
        exam_groups[key].append(exam)

    merged_count = 0
    deleted_count = 0
    total_groups = 0

    for key, exams in exam_groups.items():
        if len(exams) <= 1:
            continue  # 重複なし

        total_groups += 1
        university_id, year, subject, exam_type = key

        # 学部フィールドが最も充実しているExamをマスターとして選択
        # 優先順位: 学部名あり > 空文字列
        master_exam = None
        for exam in exams:
            if exam.department and exam.department.strip():
                master_exam = exam
                break

        # 学部名がない場合は最初のExamをマスター
        if not master_exam:
            master_exam = exams[0]

        print(f"\n統合: {master_exam.university.name} {year}年度 {master_exam.get_subject_display()}")
        print(f"  マスター: Exam ID {master_exam.pk} (学部: \"{master_exam.department}\")")

        # 他のExamのAnswerSourceとデータをマスターに移動
        for exam in exams:
            if exam.pk == master_exam.pk:
                continue

            print(f"  統合元: Exam ID {exam.pk} (学部: \"{exam.department}\")")

            # AnswerSourceを移動
            for answer_source in exam.answer_sources.all():
                # 同じURLのAnswerSourceが既に存在するか確認
                existing = master_exam.answer_sources.filter(
                    answer_url=answer_source.answer_url
                ).first()

                if existing:
                    print(f"    - スキップ（重複）: {answer_source.provider_name}")
                    answer_source.delete()
                else:
                    answer_source.exam = master_exam
                    answer_source.save()
                    print(f"    - 移動: {answer_source.provider_name}")

            # problem_urlをマスターに統合（マスターにない場合）
            if exam.problem_url and not master_exam.problem_url:
                master_exam.problem_url = exam.problem_url
                master_exam.save()
                print(f"    - 問題URL追加")

            # お気に入りを移動
            for favorite in exam.favorited_by.all():
                # 同じユーザーのお気に入りが既に存在するか確認
                existing_fav = master_exam.favorited_by.filter(user=favorite.user).first()
                if not existing_fav:
                    favorite.exam = master_exam
                    favorite.save()
                    print(f"    - お気に入り移動")
                else:
                    favorite.delete()

            # 重複Examを削除
            exam.delete()
            deleted_count += 1

        merged_count += 1

        # 統合後の解答ソース数を表示
        total_sources = master_exam.answer_sources.count()
        providers = ', '.join(set([s.provider_name for s in master_exam.answer_sources.all()]))
        print(f"  → 統合後の解答ソース数: {total_sources} ({providers})")

    print("\n" + "=" * 80)
    print(f"統合完了:")
    print(f"  - 統合されたグループ: {merged_count}")
    print(f"  - 削除されたExam: {deleted_count}")
    print("=" * 80)


def show_statistics():
    """
    統合後の統計を表示
    """
    from django.db.models import Count

    print("\n=== 統合後の統計 ===")

    total_exams = Exam.objects.count()
    total_sources = AnswerSource.objects.count()

    print(f'総過去問数: {total_exams}')
    print(f'総解答ソース数: {total_sources}')
    print(f'平均解答ソース数: {total_sources / total_exams:.2f}')
    print()

    # 複数の解答ソースを持つ過去問
    multi_source = Exam.objects.annotate(
        source_count=Count('answer_sources')
    ).filter(source_count__gte=2)

    print(f'複数の解答ソースを持つ過去問: {multi_source.count()}件 ({multi_source.count() / total_exams * 100:.1f}%)')
    print()

    # 重複チェック
    exam_groups = defaultdict(list)
    for exam in Exam.objects.all():
        key = (exam.university.name, exam.year, exam.subject)
        exam_groups[key].append(exam)

    duplicates = {k: v for k, v in exam_groups.items() if len(v) > 1}

    if duplicates:
        print(f'\n⚠️  まだ重複あり: {len(duplicates)}グループ')
    else:
        print('\n✓ 重複なし')


if __name__ == '__main__':
    merge_duplicate_exams_v2()
    show_statistics()
    print("\n✓ 過去問の統合が完了しました！")
