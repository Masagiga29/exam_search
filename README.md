# 受験生のための過去問検索アプリ 

大学受験の過去問を一括検索し、複数の予備校が公開している解答・解説を横並びで比較できるプラットフォームです。

## 主な機能

### 実装済み機能
- **ユーザー認証**: 新規登録、ログイン、ログアウト
- **過去問検索**: 学校名、年度、科目、キーワードでの絞り込み検索
- **詳細表示**: PDFプレビューと予備校別解答の横並び比較
- **お気に入り機能**: 気になる過去問を保存・管理
- **検索履歴**: 過去の検索を確認
- **レスポンシブデザイン**: スマホ・タブレットにも対応

## 技術スタック

- **Backend**: Django 5.x (Python)
- **Database**: SQLite（開発用）/ PostgreSQL（本番用）
- **Frontend**: Django Templates + Bootstrap 5
- **Authentication**: Django標準認証システム

## ディレクトリ構成

```
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

## セットアップ手順

### 1. 仮想環境の作成とアクティベート

```bash
# 仮想環境の作成
python -m venv venv

# アクティベート（Windows）
venv\Scripts\activate

# アクティベート（Mac/Linux）
source venv/bin/activate
```

### 2. 依存パッケージのインストール

```bash
pip install django==5.0
pip install pillow  # 画像処理用（オプション）
```

### 3. データベースのマイグレーション

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. スーパーユーザーの作成

```bash
python manage.py createsuperuser
```

ユーザー名、メールアドレス、パスワードを入力します。

### 5. 開発サーバーの起動

```bash
python manage.py runserver
```

ブラウザで `http://127.0.0.1:8000/` にアクセスします。

### 6. 管理画面へのアクセス

`http://127.0.0.1:8000/admin/` にアクセスし、作成したスーパーユーザーでログインします。

## 初期データの登録

### 管理画面から登録する方法

1. 管理画面にログイン
2. 「学校」セクションで大学を追加
3. 「過去問」セクションで過去問を追加
4. 「解答ソース」セクションで各予備校の解答リンクを追加

### サンプルデータ（フィクスチャ）の作成例

```python
# exams/fixtures/sample_data.json を作成
# 以下のコマンドでロード可能
python manage.py loaddata sample_data.json
```

## データモデル概要

### University（大学・高校）
- 学校名、かな表記
- 学校種別（大学/高校）
- 公式サイトURL

### Exam（過去問）
- 大学への外部キー
- 年度、科目、試験種別
- 問題PDF URL
- ソース種別、検証状態

### AnswerSource（解答ソース）
- 過去問への外部キー
- 予備校名、解答URL
- 詳細解説の有無、動画解説の有無
- 信頼度スコア

### その他
- SearchHistory: ユーザーの検索履歴
- Favorite: お気に入り管理

## 使用方法

### 検索
1. トップページの検索バーにキーワードを入力
2. または検索ページで詳細な絞り込み条件を設定

### 詳細表示
1. 検索結果から気になる過去問をクリック
2. 問題PDFのプレビューを確認
3. 下部の比較テーブルで複数の予備校の解答を比較

### お気に入り
1. ログイン後、詳細ページで「お気に入りに追加」ボタンをクリック
2. マイページで保存した過去問を確認

## 著作権について

- 問題PDFは直接ホスティングせず、オリジナルのURLを参照する設計
- 各大学・予備校の著作権に配慮した実装
- ユーザーには適切な著作権表示と注意書きを提供

## 今後の拡張案

- [ ] スクレイピング機能の実装
- [ ] AIによる解答の自動比較・分析
- [ ] ユーザー間でのノート共有
- [ ] 学習進捗管理機能
- [ ] モバイルアプリ版の開発

## トラブルシューティング

### マイグレーションエラー
```bash
# データベースをリセット
python manage.py flush
python manage.py migrate
```

### 静的ファイルが表示されない
```bash
python manage.py collectstatic
```

### テンプレートが見つからない
- `settings.py` の `TEMPLATES` の `DIRS` 設定を確認
- テンプレートディレクトリの配置を確認

## ライセンス

MIT License

## 開発者向けメモ

### PostgreSQL への切り替え（本番環境）

`settings.py` のデータベース設定を変更:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'exam_search_db',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

psycopg2 のインストール:
```bash
pip install psycopg2-binary
```

### 本番環境への展開

1. `DEBUG = False` に設定
2. `SECRET_KEY` を環境変数から読み込む
3. `ALLOWED_HOSTS` を適切に設定
4. 静的ファイルの設定を確認
5. HTTPS を有効化

---

**お問い合わせ**: masataka0629@gmail.com

# exam_search




