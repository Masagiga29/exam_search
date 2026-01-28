# ログイン認証が必要なサイトのクローラー使用ガイド

ログインが必要なWebサイト（東進ハイスクール会員サイトなど）から過去問データを取得するためのDjango管理コマンドです。

## 目次

1. [概要](#概要)
2. [必要な環境](#必要な環境)
3. [インストール](#インストール)
4. [使用方法](#使用方法)
5. [セキュリティ設定](#セキュリティ設定)
6. [トラブルシューティング](#トラブルシューティング)
7. [カスタマイズ](#カスタマイズ)

## 概要

このクローラーは以下の2つの実装を提供します:

### 1. Playwright版（推奨）
- **ファイル**: `exams/management/commands/crawl_login_site.py`
- **特徴**: モダンで高速、メンテナンスが容易
- **推奨用途**: 新規プロジェクトや定期的なクローリング

### 2. Selenium版
- **ファイル**: `exams/management/commands/crawl_login_site_selenium.py`
- **特徴**: 広く普及しており、情報が豊富
- **推奨用途**: Seleniumに慣れている場合や既存環境との統合

どちらを使用しても同じ機能を実現できます。

## 必要な環境

- Python 3.8以上
- Django 3.2以上
- Chrome/Chromiumブラウザ

## インストール

### Playwright版を使用する場合

```bash
# 仮想環境をアクティベート（既にアクティブな場合は不要）
cd exam_search
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# Playwrightをインストール
pip install playwright

# ブラウザをインストール（Chromiumを推奨）
playwright install chromium
```

### Selenium版を使用する場合

```bash
# 仮想環境をアクティベート
cd exam_search
source venv/bin/activate

# Seleniumとwebdriver-managerをインストール
pip install selenium webdriver-manager
```

## 使用方法

### 基本的な使用方法

#### Playwright版

```bash
# ヘッドレスモードで実行（デフォルト）
python manage.py crawl_login_site

# ブラウザを表示して実行（デバッグ用）
python manage.py crawl_login_site --no-headless

# 特定の年度のみ取得
python manage.py crawl_login_site --year 2024

# DRY RUNモード（データベースに保存しない）
python manage.py crawl_login_site --dry-run

# 特定の大学を指定
python manage.py crawl_login_site --university "京都大学"
```

#### Selenium版

```bash
# ヘッドレスモードで実行
python manage.py crawl_login_site_selenium

# ブラウザを表示して実行
python manage.py crawl_login_site_selenium --no-headless

# その他のオプションはPlaywright版と同じ
python manage.py crawl_login_site_selenium --year 2024 --dry-run
```

### オプション一覧

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--headless` | ブラウザをヘッドレスモードで実行 | True |
| `--no-headless` | ブラウザを表示して実行（デバッグ用） | False |
| `--year YYYY` | 特定の年度のみをクローリング | 全年度 |
| `--university "大学名"` | 対象大学を指定 | 東京大学 |
| `--dry-run` | データベースに保存せず表示のみ | False |

## セキュリティ設定

### 認証情報の管理

**重要**: ユーザー名とパスワードをコードに直接書くのは危険です。環境変数を使用してください。

#### 環境変数の設定方法

##### macOS/Linux

```bash
# ~/.bashrc または ~/.zshrc に追加
export TOSHIN_USERNAME="masa.f.0629@gmail.com"
export TOSHIN_PASSWORD="Masa1009"

# 設定を反映
source ~/.bashrc  # または source ~/.zshrc
```

##### Windows

```cmd
# コマンドプロンプト
set TOSHIN_USERNAME=your_email@example.com
set TOSHIN_PASSWORD=your_password

# PowerShell
$env:TOSHIN_USERNAME="your_email@example.com"
$env:TOSHIN_PASSWORD="your_password"
```

##### .envファイルを使用する場合（推奨）

1. `python-dotenv`をインストール:
```bash
pip install python-dotenv
```

2. プロジェクトルートに`.env`ファイルを作成:
```
TOSHIN_USERNAME=your_email@example.com
TOSHIN_PASSWORD=your_password
```

3. `.gitignore`に`.env`を追加（重要！）:
```
.env
```

4. クローラーファイルの先頭に追加:
```python
from dotenv import load_dotenv
load_dotenv()
```

## トラブルシューティング

### 1. ブラウザが起動しない

**Playwright版の場合:**
```bash
# ブラウザを再インストール
playwright install chromium --force
```

**Selenium版の場合:**
```bash
# webdriver-managerを更新
pip install --upgrade webdriver-manager

# または手動でChromeDriverをダウンロード
# https://chromedriver.chromium.org/
```

### 2. ログインに失敗する

1. `--no-headless`オプションでブラウザを表示して確認
2. スクリーンショットを確認（`login_page.png`、`after_login.png`）
3. 認証情報が正しいか確認
4. サイトのHTMLセレクタが変更されていないか確認

```bash
# デバッグモードで実行
python manage.py crawl_login_site --no-headless --dry-run
```

### 3. 要素が見つからない

サイトのHTML構造が変わっている可能性があります。

1. ブラウザの開発者ツール（F12）でHTML構造を確認
2. クローラーファイルのセレクタを更新:

```python
# crawl_login_site.py または crawl_login_site_selenium.py の該当箇所を編集
email_selectors = [
    'input[name="email"]',
    'input[name="new_email_field_name"]',  # 新しいセレクタを追加
    # ...
]
```

### 4. タイムアウトエラー

ネットワークが遅い場合はタイムアウト時間を延長:

```python
# crawl_login_site.py の該当箇所
page.goto(self.login_url, wait_until='networkidle', timeout=60000)  # 30000 → 60000
```

### 5. ヘッドレスモードで動作しない

一部のサイトはヘッドレスブラウザを検出してブロックします。

```bash
# ヘッドレスモードを無効化
python manage.py crawl_login_site --no-headless
```

## カスタマイズ

### 1. 対象サイトのURLを変更

```python
# crawl_login_site.py の __init__ メソッド
self.login_url = "https://your-target-site.com/login"
```

### 2. データ抽出ロジックのカスタマイズ

`_extract_exam_data()` メソッドを編集して、実際のサイト構造に合わせます:

```python
def _extract_exam_data(self, page):
    """実際のサイトのHTML構造に合わせて編集"""
    exams_data = []

    # 例: クラス名が "exam-card" の要素を取得
    exam_items = page.query_selector_all('.exam-card')

    for item in exam_items:
        year = item.query_selector('.year-text').text_content()
        subject = item.query_selector('.subject-name').text_content()
        pdf_link = item.query_selector('a.pdf-download').get_attribute('href')

        exams_data.append({
            'year': int(year),
            'subject': self._map_subject(subject),
            'exam_type': '一般入試',
            'problem_url': pdf_link,
            'description': f"{year}年度 {subject}",
            'source_type': 'yobi_school'
        })

    return exams_data
```

### 3. 複数ページの処理

```python
# ページネーションがある場合
for page_num in range(1, 6):  # 1〜5ページ
    url = f"https://example.com/exams?page={page_num}"
    page.goto(url)
    exams_data.extend(self._extract_exam_data(page))
```

### 4. 待機時間の調整

サイトの読み込み速度に合わせて調整:

```python
# 短くする（高速なサイト）
time.sleep(1)

# 長くする（遅いサイト）
time.sleep(5)

# 特定の要素が表示されるまで待機
page.wait_for_selector('.exam-list', timeout=10000)
```

## ベストプラクティス

### 1. サーバーに負荷をかけない

```python
# リクエスト間に適切な待機時間を設定
time.sleep(2)  # 2秒待機
```

### 2. エラーハンドリング

```python
try:
    exam_data = self._extract_exam_data(page)
except Exception as e:
    self.log(f"エラー: {e}")
    # フォールバック処理
```

### 3. ログの活用

```bash
# 詳細なログを出力
python manage.py crawl_login_site --no-headless
```

### 4. 定期実行

cronやスケジューラーで定期実行する場合:

```bash
# crontab -e
# 毎日午前3時に実行
0 3 * * * cd /path/to/exam_search && source venv/bin/activate && python manage.py crawl_login_site
```

## 参考資料

- [Playwright公式ドキュメント](https://playwright.dev/python/)
- [Selenium公式ドキュメント](https://selenium-python.readthedocs.io/)
- [Django管理コマンド](https://docs.djangoproject.com/en/stable/howto/custom-management-commands/)

## サポート

問題が発生した場合は、以下を確認してください:

1. エラーメッセージの内容
2. スクリーンショット（`--no-headless`で実行時）
3. 対象サイトのHTML構造の変更有無
4. ブラウザとドライバーのバージョン互換性
