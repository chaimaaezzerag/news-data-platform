import json
import logging
import os
from warehouse.db_connection import DatabaseContext
from config.settings import DATA_PATHS

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_json_data(filepath):
    """
    Charge les données depuis un fichier JSON.
    """
    if not os.path.exists(filepath):
        logging.error(f"Fichier {filepath} non trouvé")
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    logging.info(f"Données chargées depuis {filepath}")
    return data

def ingest_articles_to_db():
    """
    Charge les articles nettoyés (Silver) dans PostgreSQL.
    """
    # Charger les données Silver
    silver_data = load_json_data(DATA_PATHS['silver'])
    if not silver_data:
        return

    with DatabaseContext() as db:
        # Créer les tables si nécessaire
        db.create_tables()

        # Insérer les articles
        inserted_count = 0
        for article in silver_data:
            try:
                result = db.insert_article(article)
                if result > 0:
                    inserted_count += 1
            except Exception as e:
                logging.error(f"Erreur lors de l'insertion de l'article {article.get('title')}: {e}")

        logging.info(f"Inséré {inserted_count} articles dans la base de données")

def ingest_gold_data_to_db():
    """
    Charge les analyses Gold dans la base de données.
    """
    # Charger les données Gold
    gold_data = load_json_data(DATA_PATHS['gold'])
    if not gold_data:
        return

    with DatabaseContext() as db:
        # Insérer les fréquences de mots
        top_words = gold_data.get('top_words', [])
        if top_words:
            db.insert_word_frequencies(top_words)

        logging.info("Données Gold insérées dans la base de données")

def run_batch_ingestion():
    """
    Exécute l'ingestion complète des données.
    """
    logging.info("Début de l'ingestion batch")

    try:
        ingest_articles_to_db()
        ingest_gold_data_to_db()
        logging.info("Ingestion batch terminée avec succès")
    except Exception as e:
        logging.error(f"Erreur lors de l'ingestion batch : {e}")
        raise

if __name__ == "__main__":
    run_batch_ingestion()