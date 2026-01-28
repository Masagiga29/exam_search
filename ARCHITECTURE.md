# プロジェクト構成とアーキテクチャ

## システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                        ユーザー                               │
│                   (Web Browser / Mobile)                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Django Application                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              URL Routing (urls.py)                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │               Views (views.py)                         │ │
│  │  • HomeView          • ExamDetailView                  │ │
│  │  • ExamSearchView    • MyPageView                      │ │
│  │  • UniversityDetailView                                │ │
│  └────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │             Models (models.py)                         │ │
│  │  • University    • Exam                                │ │
│  │  • AnswerSource  • SearchHistory  • Favorite           │ │
│  └────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │          Templates (Django Templates)                  │ │
│  │  • base.html                                           │ │
│  │  • home.html                                           │ │
│  │  • search_results.html                                 │ │
│  │  • exam_detail.html                                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database (SQLite/PostgreSQL)               │
│  • auth_user           • exams_university                    │
│  • exams_exam          • exams_answersource                  │
│  • exams_searchhistory • exams_favorite                      │
└─────────────────────────────────────────────────────────────┘
```

## データベース ER図

```
┌──────────────────┐         ┌──────────────────┐
│   University     │         │      User        │
├──────────────────┤         │  (Django Auth)   │
│ • id (PK)        │         ├──────────────────┤
│ • name           │         │ • id (PK)        │
│ • name_kana      │         │ • username       │
│ • school_type    │         │ • email          │
│ • official_url   │         │ • password       │
└──────────────────┘         └──────────────────┘
         │                            │
         │ 1                          │ 1
         │                            │
         │ *                          │ *
         ▼                            ▼
┌──────────────────┐         ┌──────────────────┐
│      Exam        │         │  SearchHistory   │
├──────────────────┤         ├──────────────────┤
│ • id (PK)        │         │ • id (PK)        │
│ • university_id  │────┐    │ • user_id (FK)   │
│ • year           │    │    │ • query          │
│ • subject        │    │    │ • filters (JSON) │
│ • exam_type      │    │    │ • searched_at    │
│ • problem_url    │    │    └──────────────────┘
│ • description    │    │
│ • source_type    │    │    ┌──────────────────┐
│ • is_verified    │    │    │    Favorite      │
└──────────────────┘    │    ├──────────────────┤
         │              │    │ • id (PK)        │
         │ 1            │    │ • user_id (FK)   │
         │              │    │ • exam_id (FK)   │
         │ *            │    │ • note           │
         ▼              │    │ • created_at     │
┌──────────────────┐   │    └──────────────────┘
│  AnswerSource    │   │             │
├──────────────────┤   │             │
│ • id (PK)        │   └─────────────┘
│ • exam_id (FK)   │────
│ • provider_name  │
│ • answer_url     │
│ • has_detailed   │
│ • has_video      │
│ • reliability    │
│ • is_active      │
└──────────────────┘
```

## 主要機能フロー

### 1. 検索フロー

```
ユーザー入力
    │
    ▼
検索フォーム (ExamSearchForm)
    │
    ▼
ExamSearchView
    │
    ├─ キーワード検索 (Q objects)
    ├─ 大学フィルター
    ├─ 年度フィルター
    └─ 科目フィルター
    │
    ▼
検索結果一覧 (search_results.html)
    │
    └─ ページネーション（12件/ページ）
```

### 2. 詳細表示・比較フロー

```
検索結果からクリック
    │
    ▼
ExamDetailView
    │
    ├─ 過去問情報の取得
    ├─ 解答ソースの取得（信頼度順）
    └─ 関連過去問の取得
    │
    ▼
詳細画面 (exam_detail.html)
    │
    ├─ 問題PDFプレビュー (iframe)
    └─ 予備校別解答比較テーブル
        │
        ├─ 河合塾
        ├─ 駿台予備校
        ├─ 東進ハイスクール
        └─ その他
```

### 3. お気に入り機能フロー

```
詳細画面で「お気に入りに追加」
    │
    ▼
add_favorite() 関数
    │
    ├─ ログイン確認
    ├─ Favorite.objects.get_or_create()
    └─ メッセージ表示
    │
    ▼
マイページで確認 (MyPageView)
    │
    └─ Favorite一覧表示
```

## セキュリティ考慮事項

### 実装済み
- ✅ CSRF保護（Djangoデフォルト）
- ✅ パスワードハッシュ化（Django標準）
- ✅ XSS対策（テンプレート自動エスケープ）
- ✅ SQL インジェクション対策（ORM使用）
- ✅ ログイン必須ページの保護（LoginRequiredMixin）

### 本番環境で必要な設定
- ⚠️ `DEBUG = False` の設定
- ⚠️ `SECRET_KEY` の環境変数化
- ⚠️ `ALLOWED_HOSTS` の適切な設定
- ⚠️ HTTPS の有効化
- ⚠️ セキュリティヘッダーの設定

## パフォーマンス最適化

### 実装済み
- ✅ `select_related()` による N+1 問題の回避
- ✅ `prefetch_related()` による関連データの効率的な取得
- ✅ データベースインデックス（自動生成）
- ✅ ページネーション（12件/ページ）

### 今後の改善案
- [ ] キャッシュの導入（Redis）
- [ ] 静的ファイルのCDN配信
- [ ] データベースクエリの最適化
- [ ] 非同期処理の導入（Celery）

## テスト戦略

```python
# tests/test_models.py
# モデルのテスト

# tests/test_views.py
# ビューのテスト（検索、詳細、お気に入り）

# tests/test_forms.py
# フォームのバリデーションテスト

# tests/test_integration.py
# 統合テスト
```

実行コマンド:
```bash
python manage.py test
```

## デプロイメント

### 推奨環境
- **Webサーバー**: Nginx + Gunicorn
- **データベース**: PostgreSQL 13+
- **キャッシュ**: Redis
- **ホスティング**: AWS / Heroku / DigitalOcean

### デプロイ手順（簡略版）
1. 環境変数の設定
2. 依存パッケージのインストール
3. データベースマイグレーション
4. 静的ファイルの収集
5. Gunicornの起動
6. Nginxの設定

## 拡張機能のアイデア

### Phase 2
- [ ] API の実装（REST API / GraphQL）
- [ ] 自動スクレイピング機能
- [ ] 通知機能（新しい過去問の追加時）
- [ ] ソーシャル機能（コメント、共有）

### Phase 3
- [ ] AI による解答分析
- [ ] 学習進捗管理
- [ ] 推薦システム
- [ ] モバイルアプリ（React Native / Flutter）

## ライセンスと著作権

- プラットフォーム自体: MIT License
- 過去問データ: 各大学・予備校に著作権帰属
- スクレイピング: robots.txt の遵守必須
- 利用規約の整備が必要
