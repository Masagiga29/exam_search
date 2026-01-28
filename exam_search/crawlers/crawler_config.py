"""
クローラー設定ファイル

各サイトのクロール設定を一元管理します。
新しいサイトを追加する場合は、このファイルに設定を追加してください。
"""

# クロール対象サイトの設定
CRAWLER_CONFIGS = {
    # 東進ハイスクール
    'toshin': {
        'name': '東進ハイスクール',
        'base_url': 'https://www.toshin-kakomon.com',
        'enabled': True,
        'delay': 3.0,  # リクエスト間隔（秒）
        'provider_type': 'yobi_school',
        'reliability_score': 8,
        'has_detailed_explanation': True,
        'has_video_explanation': True,
    },
    
    # 河合塾
    'kawaijuku': {
        'name': '河合塾',
        'base_url': 'https://www.keinet.ne.jp',
        'enabled': True,
        'delay': 3.0,
        'provider_type': 'yobi_school',
        'reliability_score': 9,
        'has_detailed_explanation': True,
        'has_video_explanation': False,
    },
    
    # 駿台予備校
    'sundai': {
        'name': '駿台予備校',
        'base_url': 'https://www.sundai.ac.jp',
        'enabled': True,
        'delay': 3.0,
        'provider_type': 'yobi_school',
        'reliability_score': 9,
        'has_detailed_explanation': True,
        'has_video_explanation': True,
    },
    
    # 代々木ゼミナール
    'yoyogi': {
        'name': '代々木ゼミナール',
        'base_url': 'https://www.yozemi.ac.jp',
        'enabled': False,  # 現在は無効
        'delay': 3.0,
        'provider_type': 'yobi_school',
        'reliability_score': 8,
    },
    
    # パスナビ（旺文社）
    'passnavi': {
        'name': 'パスナビ',
        'base_url': 'https://passnavi.evidus.com',
        'enabled': True,
        'delay': 3.0,
        'provider_type': 'archive',
        'reliability_score': 7,
    },
}

# 対象大学のリスト（優先度順）
TARGET_UNIVERSITIES = [
    # 国公立大学
    {
        'name': '東京大学',
        'priority': 1,
        'official_url': 'https://www.u-tokyo.ac.jp',
    },
    {
        'name': '京都大学',
        'priority': 1,
        'official_url': 'https://www.kyoto-u.ac.jp',
    },
    {
        'name': '大阪大学',
        'priority': 2,
        'official_url': 'https://www.osaka-u.ac.jp',
    },
    {
        'name': '東北大学',
        'priority': 2,
        'official_url': 'https://www.tohoku.ac.jp',
    },
    {
        'name': '名古屋大学',
        'priority': 2,
        'official_url': 'https://www.nagoya-u.ac.jp',
    },
    {
        'name': '九州大学',
        'priority': 2,
        'official_url': 'https://www.kyushu-u.ac.jp',
    },
    {
        'name': '北海道大学',
        'priority': 2,
        'official_url': 'https://www.hokudai.ac.jp',
    },
    
    # 私立大学
    {
        'name': '早稲田大学',
        'priority': 1,
        'official_url': 'https://www.waseda.jp',
    },
    {
        'name': '慶應義塾大学',
        'priority': 1,
        'official_url': 'https://www.keio.ac.jp',
    },
    {
        'name': '上智大学',
        'priority': 2,
        'official_url': 'https://www.sophia.ac.jp',
    },
    {
        'name': '明治大学',
        'priority': 2,
        'official_url': 'https://www.meiji.ac.jp',
    },
    {
        'name': '青山学院大学',
        'priority': 2,
        'official_url': 'https://www.aoyama.ac.jp',
    },
    {
        'name': '立教大学',
        'priority': 2,
        'official_url': 'https://www.rikkyo.ac.jp',
    },
    {
        'name': '中央大学',
        'priority': 2,
        'official_url': 'https://www.chuo-u.ac.jp',
    },
    {
        'name': '法政大学',
        'priority': 2,
        'official_url': 'https://www.hosei.ac.jp',
    },
]

# 対象年度の範囲
TARGET_YEARS = {
    'start': 2020,  # 開始年度
    'end': 2025,    # 終了年度
}

# クロールスケジュール設定
SCHEDULE_CONFIG = {
    'daily': {
        'enabled': False,
        'time': '03:00',  # 午前3時
        'tasks': ['validate_links'],
    },
    'weekly': {
        'enabled': True,
        'day': 'sunday',  # 日曜日
        'time': '02:00',  # 午前2時
        'tasks': ['full_crawl', 'validate_links', 'remove_duplicates'],
    },
    'monthly': {
        'enabled': True,
        'day': 1,  # 毎月1日
        'time': '01:00',  # 午前1時
        'tasks': ['full_crawl', 'validate_links', 'generate_report'],
    },
}

# エラー処理設定
ERROR_HANDLING = {
    'max_retries': 3,  # 最大リトライ回数
    'retry_delay': 5,  # リトライ間隔（秒）
    'timeout': 15,     # タイムアウト（秒）
    'log_file': 'crawler_errors.log',
}

# データベース設定
DATABASE_CONFIG = {
    'batch_size': 100,  # バッチ処理のサイズ
    'commit_interval': 50,  # コミット間隔
}

# ロギング設定
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'crawler.log',
    'max_bytes': 10485760,  # 10MB
    'backup_count': 5,
}

# 除外パターン（クロールしないURLパターン）
EXCLUDE_PATTERNS = [
    r'.*login.*',
    r'.*signup.*',
    r'.*admin.*',
    r'.*payment.*',
    r'.*cart.*',
]

# User-Agent設定
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# robots.txtの遵守
RESPECT_ROBOTS_TXT = True

# 同時接続数の制限
MAX_CONCURRENT_REQUESTS = 1  # 1つずつ順番に処理（サーバー負荷軽減）

# キャッシュ設定
CACHE_CONFIG = {
    'enabled': True,
    'ttl': 3600,  # キャッシュ有効期間（秒）
    'directory': '.crawler_cache',
}
