受験生のための過去問検索アプリ 

大学受験の過去問を一括検索し、複数の予備校が公開している解答・解説を横並びで比較できるプラットフォームです。

## 主な機能

### 実装済み機能
- **ユーザー認証**: 新規登録、ログイン、ログアウト
- **過去問検索**: 学校名、年度、科目、キーワードでの絞り込み検索
- **詳細表示**: PDFプレビューと予備校別解答の横並び比較
- **お気に入り機能**: 気になる過去問を保存・管理
- **検索履歴**: 過去の検索を確認
- **レスポンシブデザイン**: スマホ・タブレットにも対応


### ディレクトリ構成

exam_search/
├── exam_search/          # プロジェクト設定
│   ├── settings.py       # 設定ファイル
│   ├── urls.py          # メインURLルーティング
│   └── wsgi.py
├── exams/               # メインアプリケーション
│   ├── models.py        # データモデル
│   ├── views.py         # ビュー
│   ├── urls.py          # URLルーティング
│   ├── forms.py         # フォーム定義
│   ├── admin.py         # 管理画面設定
│   └── migrations/      # マイグレーションファイル
├── accounts/            # 認証アプリ
│   └── views.py
├── templates/           # HTMLテンプレート
│   ├── base.html        # ベーステンプレート
│   ├── exams/
│   │   ├── home.html
│   │   ├── search_results.html
│   │   ├── exam_detail.html
│   │   └── mypage.html
│   └── registration/
│       ├── login.html
│       └── signup.html
├── manage.py
└── requirements.txt
```
