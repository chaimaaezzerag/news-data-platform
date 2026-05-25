import os

import os

# Configuration de la base de données
# Pour développement simple, on utilise SQLite
USE_SQLITE = os.getenv('USE_SQLITE', 'true').lower() == 'true'

if USE_SQLITE:
    DB_CONFIG = {
        'engine': 'sqlite',
        'database': os.path.join(os.path.dirname(__file__), '..', 'data', 'news_data_platform.db')
    }
else:
    # Configuration PostgreSQL
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'news_data_platform'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'password'),
        'port': os.getenv('DB_PORT', '5432')
    }

# Configuration du scraping
SCRAPING_CONFIG = {
    'max_articles': int(os.getenv('MAX_ARTICLES', '10')),
    'delay_between_requests': float(os.getenv('REQUEST_DELAY', '1.0')),
    'timeout': int(os.getenv('REQUEST_TIMEOUT', '10')),
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Chemins des données
DATA_PATHS = {
    'bronze': 'data/bronze/articles.json',
    'silver': 'data/silver/cleaned_articles.json',
    'gold': 'data/gold/analysis.json'
}

# Sources de news (extensible)
NEWS_SOURCES = {
    'hespress': {
        'url': 'https://www.hespress.com/',
        'language': 'ar',
        'selectors': {
            'article_links': 'a[href*=".html"]',
            'title': 'h1.post-title, h1',
            'content': 'div.post-content, div#article-content, article, div.content',
            'date': 'time, span.date'
        }
    },
    'cnn': {
        'url': 'https://www.cnn.com/',
        'language': 'en',
        'selectors': {
            'article_links': 'a[href*="/2024/"]',
            'title': 'h1',
            'content': 'div.article-body, div.content',
            'date': 'time, span.date'
        }
    }
}

# Configuration Airflow (si utilisé)
AIRFLOW_CONFIG = {
    'dag_id': 'news_data_pipeline',
    'schedule_interval': '@daily',
    'start_date': '2024-01-01'
}