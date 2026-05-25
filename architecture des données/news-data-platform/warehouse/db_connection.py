import sqlite3
import psycopg2
import psycopg2.extras
import json
import logging
import os
from datetime import datetime
from config.settings import DB_CONFIG

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseConnection:
    """
    Classe pour gérer la connexion à la base de données (SQLite ou PostgreSQL).
    """

    def __init__(self, config=None):
        self.config = config or DB_CONFIG
        self.connection = None
        self.is_sqlite = self.config.get('engine') == 'sqlite'

    def connect(self):
        """
        Établit la connexion à la base de données.
        """
        try:
            if self.is_sqlite:
                db_path = self.config['database']
                os.makedirs(os.path.dirname(db_path), exist_ok=True)
                self.connection = sqlite3.connect(db_path)
                self.connection.execute("PRAGMA foreign_keys = ON")  # Activer les clés étrangères
                logging.info(f"Connexion SQLite établie : {db_path}")
            else:
                self.connection = psycopg2.connect(**self.config)
                self.connection.autocommit = True  # Pour les opérations DDL
                logging.info("Connexion à PostgreSQL établie")
        except Exception as e:
            logging.error(f"Erreur de connexion : {e}")
            raise

    def disconnect(self):
        """
        Ferme la connexion.
        """
        if self.connection:
            self.connection.close()
            logging.info("Connexion fermée")

    def execute_query(self, query, params=None, fetch=False):
        """
        Exécute une requête SQL.
        """
        if not self.connection:
            self.connect()

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())

            if fetch:
                results = cursor.fetchall()
                cursor.close()
                return results
            else:
                self.connection.commit()
                rowcount = cursor.rowcount
                cursor.close()
                return rowcount
        except Exception as e:
            logging.error(f"Erreur lors de l'exécution de la requête : {e}")
            raise

    def create_tables(self):
        """
        Crée les tables nécessaires.
        """
        if self.is_sqlite:
            queries = [
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    content_cleaned TEXT,
                    url TEXT UNIQUE,
                    date DATE,
                    scraped_at REAL,
                    processed_at TEXT,
                    word_count INTEGER,
                    sentiment TEXT,
                    categories TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS word_frequencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    frequency INTEGER NOT NULL,
                    date DATE DEFAULT CURRENT_DATE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(word, date)
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS article_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER REFERENCES articles(id),
                    category TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            ]
        else:
            queries = [
                """
                CREATE TABLE IF NOT EXISTS articles (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT,
                    content_cleaned TEXT,
                    url TEXT UNIQUE,
                    date DATE,
                    scraped_at TIMESTAMP,
                    processed_at TIMESTAMP,
                    word_count INTEGER,
                    sentiment VARCHAR(20),
                    categories TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS word_frequencies (
                    id SERIAL PRIMARY KEY,
                    word TEXT NOT NULL,
                    frequency INTEGER NOT NULL,
                    date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(word, date)
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS article_categories (
                    id SERIAL PRIMARY KEY,
                    article_id INTEGER REFERENCES articles(id),
                    category VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            ]

        for query in queries:
            self.execute_query(query)
        logging.info("Tables créées ou déjà existantes")

    def insert_article(self, article):
        """
        Insère un article dans la base de données.
        """
        if self.is_sqlite:
            query = """
            INSERT OR IGNORE INTO articles (title, content, content_cleaned, url, date, scraped_at,
                                         processed_at, word_count, sentiment, categories)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            params = (
                article.get('title'),
                article.get('content'),
                article.get('content_cleaned'),
                article.get('url'),
                article.get('date'),
                article.get('scraped_at'),
                article.get('processed_at'),
                article.get('word_count'),
                article.get('sentiment'),
                ','.join(article.get('categories', [])) if article.get('categories') else None
            )
        else:
            query = """
            INSERT INTO articles (title, content, content_cleaned, url, date, scraped_at,
                                 processed_at, word_count, sentiment, categories)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING;
            """
            params = (
                article.get('title'),
                article.get('content'),
                article.get('content_cleaned'),
                article.get('url'),
                article.get('date') or None,
                datetime.fromtimestamp(article.get('scraped_at', 0)) if article.get('scraped_at') else None,
                article.get('processed_at'),
                article.get('word_count'),
                article.get('sentiment'),
                article.get('categories')
            )

        return self.execute_query(query, params)

    def insert_word_frequencies(self, word_data, date=None):
        """
        Insère les fréquences de mots.
        """
        target_date = date or datetime.now().date().isoformat()

        if self.is_sqlite:
            query = """
            INSERT OR REPLACE INTO word_frequencies (word, frequency, date)
            VALUES (?, ?, ?);
            """
            for item in word_data:
                freq = item.get('count', item.get('frequency', 0))
                params = (item['word'], freq, target_date)
                self.execute_query(query, params)
        else:
            query = """
            INSERT INTO word_frequencies (word, frequency, date)
            VALUES (%s, %s, %s)
            ON CONFLICT (word, date) DO UPDATE SET frequency = EXCLUDED.frequency;
            """
            for item in word_data:
                freq = item.get('count', item.get('frequency', 0))
                params = (item['word'], freq, target_date)
                self.execute_query(query, params)

    def load_json(self, filepath: str):
        """Charge un fichier JSON si disponible."""
        if not os.path.exists(filepath):
            logging.warning(f"Fichier JSON non trouvé: {filepath}")
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def ingest_gold_data(self, silver_path: str = 'data/silver/cleaned_articles.json', gold_path: str = 'data/gold/analysis.json'):
        """Ingestion des articles nettoyés et des fréquences en base."""
        self.create_tables()

        silver_articles = self.load_json(silver_path) or []
        if not silver_articles:
            logging.warning(f"Aucune donnée Silver trouvée à {silver_path}")

        inserted_articles = 0
        for article in silver_articles:
            try:
                self.insert_article(article)
                inserted_articles += 1
            except Exception as e:
                logging.error(f"Erreur insertion article {article.get('url')}: {e}")

        logging.info(f"{inserted_articles} articles insérés en base")

        gold_data = self.load_json(gold_path) or {}
        top_words = gold_data.get('top_words', [])
        if top_words:
            self.insert_word_frequencies(top_words)
            logging.info(f"{len(top_words)} mots fréquents insérés en base")
        else:
            logging.warning(f"Aucune donnée Gold trouvée à {gold_path} ou top_words vide")

    def get_articles_count(self):
        """
        Retourne le nombre total d'articles.
        """
        result = self.execute_query("SELECT COUNT(*) FROM articles;", fetch=True)
        return result[0][0] if result else 0

    def get_top_words(self, limit=10):
        """
        Retourne les mots les plus fréquents.
        """
        query = """
        SELECT word, SUM(frequency) as total_freq
        FROM word_frequencies
        GROUP BY word
        ORDER BY total_freq DESC
        LIMIT ?;
        """ if self.is_sqlite else """
        SELECT word, SUM(frequency) as total_freq
        FROM word_frequencies
        GROUP BY word
        ORDER BY total_freq DESC
        LIMIT %s;
        """
        return self.execute_query(query, (limit,), fetch=True)

def get_db_connection():
    """
    Fonction utilitaire pour obtenir une connexion DB.
    """
    db = DatabaseConnection()
    db.connect()
    return db

# Contexte manager pour la connexion
class DatabaseContext:
    def __enter__(self):
        self.db = DatabaseConnection()
        self.db.connect()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.disconnect()