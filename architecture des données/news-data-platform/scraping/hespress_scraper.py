import requests
from bs4 import BeautifulSoup
import json
import os
import re
import logging
from collections import Counter
from urllib.parse import urljoin
import time

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Stop words en arabe (pour Hespress)
STOP_WORDS = [
    "في", "من", "على", "و", "إلى", "عن", "هذا", "ذلك", "مع", "كان",
    "كما", "لكن", "ل", "ب", "أو", "أي", "ما", "لم", "لن", "قد", "هي", "هو",
    "كانت", "كانوا", "هناك", "أن", "لا", "أنا", "نحن", "أنت", "أنتم", "هم"
]

def clean_text(text):
    """
    Nettoie le texte : minuscule, enlève ponctuation, chiffres, espaces multiples.
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)  # ponctuation
    text = re.sub(r"\d+", "", text)       # chiffres
    text = re.sub(r"\s+", " ", text)      # espaces multiples
    return text.strip()

def get_articles(url, max_articles=10):
    """
    Récupère les liens d'articles depuis la page d'accueil.
    Utilise des sélecteurs plus précis pour Hespress.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        articles = []
        # Sélecteurs plus précis pour Hespress
        article_links = soup.select('a[href*=".html"]')  # Liens vers articles

        for a in article_links[:max_articles]:
            title = a.get_text(strip=True)
            link = a.get("href")
            if link:
                full_link = urljoin(url, link)
                if title and len(title) > 10:  # Éviter les liens trop courts
                    articles.append({
                        "title": title,
                        "url": full_link
                    })

        logging.info(f"Récupéré {len(articles)} articles depuis {url}")
        return articles

    except requests.RequestException as e:
        logging.error(f"Erreur lors de la récupération des articles : {e}")
        return []

def scrape_article(url):
    """
    Scrape le contenu d'un article.
    Utilise des sélecteurs plus précis pour Hespress.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Sélecteurs plus précis pour Hespress
        title_elem = soup.find("h1", class_="post-title") or soup.find("h1")
        title = title_elem.get_text(strip=True) if title_elem else "Titre non trouvé"

        # Contenu de l'article
        content_elem = soup.find("div", class_="post-content") or soup.find("div", {"id": "article-content"})
        if not content_elem:
            # Essayer d'autres sélecteurs courants
            content_elem = soup.find("article") or soup.find("div", class_="content")

        content = content_elem.get_text(strip=True) if content_elem else "Contenu non trouvé"

        # Date de publication (si disponible)
        date_elem = soup.find("time") or soup.find("span", class_="date")
        date = date_elem.get_text(strip=True) if date_elem else ""

        return {
            "title": title,
            "content": content,
            "url": url,
            "date": date,
            "scraped_at": time.time()
        }

    except requests.RequestException as e:
        logging.error(f"Erreur lors du scraping de {url} : {e}")
        return None
    except Exception as e:
        logging.error(f"Erreur inattendue lors du scraping de {url} : {e}")
        return None

def analyze_top_words(articles, top_n=10):
    """
    Analyse les mots les plus fréquents dans les articles.
    """
    all_text = ""
    for article in articles:
        if article and article.get("content"):
            all_text += clean_text(article["content"]) + " "

    words = [
        w for w in all_text.split()
        if w not in STOP_WORDS and len(w) > 3
    ]

    word_counts = Counter(words)
    top_words = word_counts.most_common(top_n)

    return top_words

def save_to_json(data, filepath):
    """
    Sauvegarde les données en JSON.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logging.info(f"Données sauvegardées dans {filepath}")

if __name__ == "__main__":
    # Configuration
    BASE_URL = "https://www.hespress.com/"
    MAX_ARTICLES = 5  # Pour test, augmenter pour production

    # 1. Récupération des liens d'articles
    articles_links = get_articles(BASE_URL, MAX_ARTICLES)

    # 2. Scraping détaillé des articles
    full_articles = []
    for link in articles_links:
        article_data = scrape_article(link["url"])
        if article_data:
            article_data["content"] = clean_text(article_data["content"])
            full_articles.append(article_data)
        time.sleep(1)  # Respecter le site web

    # 3. Sauvegarde en Bronze (données brutes)
    bronze_path = "data/bronze/articles.json"
    save_to_json(full_articles, bronze_path)

    # 4. Analyse et sauvegarde en Gold
    top_words = analyze_top_words(full_articles)
    gold_path = "data/gold/top_words.json"
    save_to_json(top_words, gold_path)

    logging.info("✅ Scraping et analyse terminés")