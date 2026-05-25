#!/usr/bin/env python3
"""
Point d'entrée principal pour la plateforme Big Data de collecte d'articles de presse.

Ce script orchestre l'ensemble du pipeline :
1. Scraping des données (Bronze)
2. Nettoyage des données (Silver)
3. Analyse et transformation (Gold)
4. Ingestion dans SQLite
"""

import logging
import sys
import os
from datetime import datetime
import subprocess

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_pipeline():
    """
    Exécute le pipeline complet de données.
    """
    start_time = datetime.now()
    logging.info("Demarrage du pipeline de donnees news-data-platform")

    try:
        # Étape 1: Scraping des données
        logging.info("Etape 1: Scraping des articles...")
        result = subprocess.run([sys.executable, "scraping/hespress_scraper_v2.py"],
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode != 0:
            raise Exception(f"Erreur scraping: {result.stderr}")
        logging.info("Scraping termine")

        # Étape 2: Nettoyage des données (Bronze -> Silver)
        logging.info("Etape 2: Nettoyage des donnees...")
        result = subprocess.run([sys.executable, "processing/clean_data.py"],
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode != 0:
            raise Exception(f"Erreur nettoyage: {result.stderr}")
        logging.info("Nettoyage termine")

        # Étape 3: Analyse et transformation (Silver -> Gold)
        logging.info("Etape 3: Analyse et transformation...")
        result = subprocess.run([sys.executable, "processing/transform.py"],
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode != 0:
            raise Exception(f"Erreur analyse: {result.stderr}")
        logging.info("Analyse terminee")

        # Étape 4: Ingestion dans la base de données
        logging.info("Etape 4: Ingestion dans la base de donnees...")
        from warehouse.db_connection import DatabaseConnection
        db = DatabaseConnection()
        db.connect()
        db.ingest_gold_data()
        db.disconnect()
        logging.info("Ingestion terminee")

        end_time = datetime.now()
        duration = end_time - start_time
        logging.info(f"Pipeline termine avec succes en {duration}")

    except Exception as e:
        logging.error(f"Erreur dans le pipeline : {e}")
        sys.exit(1)

def setup_database():
    """
    Initialise la base de données (crée les tables).
    """
    logging.info("Initialisation de la base de donnees...")
    try:
        from warehouse.db_connection import DatabaseConnection
        db = DatabaseConnection()
        db.connect()
        db.create_tables()
        db.disconnect()
        logging.info("Base de donnees initialisee")
    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation de la BD : {e}")
        sys.exit(1)

def show_stats():
    """
    Affiche les statistiques de la plateforme.
    """
    try:
        from warehouse.db_connection import DatabaseConnection
        db = DatabaseConnection()
        db.connect()

        article_count = db.get_articles_count()
        top_words = db.get_top_words(5)

        db.disconnect()

        print("\nStatistiques de la plateforme:")
        print(f"   • Articles collectes: {article_count}")
        print("   • Top 5 mots-cles:")
        for word, freq in top_words:
            print(f"     - {word}: {freq}")

    except Exception as e:
        logging.error(f"Erreur lors de l'affichage des stats : {e}")

def show_help():
    """
    Affiche l'aide pour les commandes disponibles.
    """
    print("""
News Data Platform - Plateforme Big Data pour articles de presse

COMMANDES DISPONIBLES:

Pipeline complet:
  python main.py                    # Execute tout le pipeline (scrape + clean + analyze + ingest)

Etapes individuelles:
  python main.py scrape            # Scraping des articles uniquement
  python main.py clean             # Nettoyage des donnees uniquement
  python main.py analyze           # Analyse et transformation uniquement
  python main.py ingest            # Ingestion en base uniquement
  python main.py dashboard         # Génère le dashboard de visualisation

Administration:
  python main.py setup             # Initialisation de la base de donnees
  python main.py stats             # Affichage des statistiques

EXEMPLES:
  # Premiere utilisation
  python main.py setup
  python main.py

  # Mise a jour des donnees
  python main.py scrape
  python main.py clean
  python main.py analyze
  python main.py ingest

ARCHITECTURE:
  Bronze (data/bronze/)  : Donnees brutes JSON
  Silver (data/silver/)  : Donnees nettoyees
  Gold (data/gold/)      : Analyses et metriques
  Warehouse              : Base de donnees SQLite

LOGS:
  • pipeline.log         : Logs du pipeline principal
  • scraper.log          : Logs du scraping
  • logs/                : Dossier des logs detailles
""")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "setup":
            setup_database()
        elif command == "stats":
            show_stats()
        elif command == "scrape":
            result = subprocess.run([sys.executable, "scraping/hespress_scraper_v2.py"],
                                  cwd=os.path.dirname(__file__))
            sys.exit(result.returncode)
        elif command == "clean":
            result = subprocess.run([sys.executable, "processing/clean_data.py"],
                                  cwd=os.path.dirname(__file__))
            sys.exit(result.returncode)
        elif command == "analyze":
            result = subprocess.run([sys.executable, "processing/transform.py"],
                                  cwd=os.path.dirname(__file__))
            sys.exit(result.returncode)
        elif command == "ingest":
            from warehouse.db_connection import DatabaseConnection
            db = DatabaseConnection()
            db.connect()
            db.ingest_gold_data()
            db.disconnect()
        elif command == "dashboard":
            result = subprocess.run([sys.executable, "visualization/dashboard.py"],
                                  cwd=os.path.dirname(__file__))
            sys.exit(result.returncode)
        elif command in ["help", "-h", "--help"]:
            show_help()
        else:
            print(f"Commande inconnue: {command}")
            show_help()
            sys.exit(1)
    else:
        run_pipeline()