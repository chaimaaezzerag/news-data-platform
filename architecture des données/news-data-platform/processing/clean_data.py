import json
import os
import re
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Stop words étendues
STOP_WORDS = set([
    # Arabe
    "في", "من", "على", "و", "إلى", "عن", "هذا", "ذلك", "مع", "كان",
    "كما", "لكن", "ل", "ب", "أو", "أي", "ما", "لم", "لن", "قد", "هي", "هو",
    "كانت", "كانوا", "هناك", "أن", "لا", "أنا", "نحن", "أنت", "أنتم", "هم",
    "الذي", "التي", "الذين", "اللذين", "اللائي", "اللواتي", "أنها", "إنها",
    "كيف", "متى", "أين", "لماذا", "ماذا", "منذ", "حتى", "بين", "خلال",
    # Français
    "le", "la", "les", "de", "du", "des", "et", "à", "un", "une", "dans", "sur",
    "pour", "par", "avec", "sans", "sous", "entre", "chez", "vers", "pendant",
    "depuis", "jusque", "lorsque", "quand", "comme", "si", "que", "qui", "dont",
    "où", "ce", "cette", "ces", "mon", "ton", "son", "notre", "votre", "leur",
    "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "me", "te", "se",
    "y", "en", "au", "aux", "du", "des",
    # Anglais
    "the", "and", "for", "with", "that", "this", "from", "not", "are", "but",
    "you", "your", "have", "has", "was", "were", "will", "can", "its", "all",
    "any", "our", "out", "who", "what", "when", "where", "why", "how"
])

def load_bronze_data(filepath="data/bronze/articles.json"):
    """
    Charge les données brutes depuis le fichier JSON.
    """
    if not os.path.exists(filepath):
        logging.error(f"Fichier {filepath} non trouvé")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    logging.info(f"Chargé {len(data)} articles depuis {filepath}")
    return data

def clean_article_content(content):
    """
    Nettoyage avancé du contenu de l'article.
    """
    if not content:
        return ""

    content = content.lower()
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', content)
    content = re.sub(r'\d+', ' ', content)
    content = re.sub(r'\s+', ' ', content)

    words = content.split()
    words = [w for w in words if len(w) > 2 and w.lower() not in STOP_WORDS and not w.isdigit()]

    return ' '.join(words).strip()

def remove_duplicates(articles):
    """
    Supprime les articles dupliqués basés sur le titre et l'URL.
    """
    seen = set()
    unique_articles = []

    for article in articles:
        key = (article.get('title', '').strip().lower(), article.get('url', ''))
        if key not in seen:
            seen.add(key)
            unique_articles.append(article)

    logging.info(f"Supprimé {len(articles) - len(unique_articles)} duplicatas")
    return unique_articles

def validate_article(article):
    """
    Valide qu'un article a les champs requis et du contenu valide.
    """
    required_fields = ['title', 'content', 'url']
    for field in required_fields:
        if not article.get(field) or not article[field].strip():
            return False

    # Vérifier que le contenu n'est pas trop court
    if len(article['content'].split()) < 10:
        return False

    return True

def clean_articles(articles):
    """
    Nettoie tous les articles : contenu, validation, suppression duplicatas.
    """
    cleaned_articles = []

    for article in articles:
        # Nettoyer le contenu
        article['content_cleaned'] = clean_article_content(article.get('content', ''))

        # Ajouter des métadonnées
        article['word_count'] = len(article['content_cleaned'].split())
        article['processed_at'] = datetime.now().isoformat()

        # Valider
        if validate_article(article):
            cleaned_articles.append(article)
        else:
            logging.warning(f"Article invalide ignoré : {article.get('title', 'Sans titre')}")

    # Supprimer duplicatas
    cleaned_articles = remove_duplicates(cleaned_articles)

    logging.info(f"Articles nettoyés : {len(cleaned_articles)} valides sur {len(articles)} originaux")
    return cleaned_articles

def save_silver_data(articles, filepath="data/silver/cleaned_articles.json"):
    """
    Sauvegarde les données nettoyées en Silver.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    logging.info(f"Données Silver sauvegardées dans {filepath}")

def main():
    """
    Fonction principale pour le nettoyage des données.
    """
    # Charger les données Bronze
    bronze_articles = load_bronze_data()

    if not bronze_articles:
        logging.error("Aucune donnée Bronze trouvée")
        return

    # Nettoyer les données
    silver_articles = clean_articles(bronze_articles)

    # Sauvegarder en Silver
    save_silver_data(silver_articles)

    logging.info("Nettoyage des données terminé")

if __name__ == "__main__":
    main()