#!/usr/bin/env python3
"""
Scraper amélioré pour Hespress.com
Récupère les articles avec titre, contenu, date et auteur.
Code propre, robuste et professionnel.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
import logging
import time
from collections import Counter
from urllib.parse import urljoin
from datetime import datetime
import random
from typing import List, Dict, Optional, Any

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

# Stop words en arabe et français
STOP_WORDS = set([
    # Arabe
    "في", "من", "على", "و", "إلى", "عن", "هذا", "ذلك", "مع", "كان",
    "كما", "لكن", "ل", "ب", "أو", "أي", "ما", "لم", "لن", "قد", "هي", "هو",
    "كانت", "كانوا", "هناك", "أن", "لا", "أنا", "نحن", "أنت", "أنتم", "هم",
    "فى", "من", "على", "و", "إلى", "عن", "هذا", "ذلك", "مع", "كان",
    "كما", "لكن", "ل", "ب", "أو", "أي", "ما", "لم", "لن", "قد", "هي", "هو",
    # Français
    "le", "la", "les", "de", "du", "des", "et", "à", "un", "une", "dans", "sur",
    "pour", "par", "avec", "sans", "sous", "entre", "chez", "vers", "pendant",
    "depuis", "jusque", "lorsque", "quand", "comme", "si", "que", "qui", "dont",
    "où", "ce", "cette", "ces", "mon", "ton", "son", "notre", "votre", "leur",
    "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "me", "te", "se",
    "nous", "vous", "leur", "y", "en", "au", "aux", "du", "des"
])

class HespressScraper:
    """Scraper pour Hespress.com"""

    def __init__(self, max_retries: int = 3, timeout: int = 15, delay: float = 2.0):
        self.max_retries = max_retries
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def make_request(self, url: str, retries: Optional[int] = None) -> Optional[requests.Response]:
        """Fait une requête HTTP avec retry automatique"""
        if retries is None:
            retries = self.max_retries

        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logging.warning(f"Tentative {attempt + 1}/{retries} echouee pour {url}: {e}")
                if attempt < retries - 1:
                    sleep_time = self.delay * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(sleep_time)
                else:
                    logging.error(f"Echec definitif pour {url}: {e}")
                    return None

    def extract_content_from_soup(self, soup: BeautifulSoup) -> str:
        """Extrait le contenu textuel de l'article depuis le DOM."""
        content_selectors = [
            'div.post-content',
            'div.entry-content',
            'div.article-content',
            'article .content',
            'div.the-content',
            '.post-content p',
            '.entry-content p'
        ]

        content = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                paragraphs = content_elem.find_all('p')
                if paragraphs:
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                else:
                    content = content_elem.get_text(strip=True)
                if content:
                    return content

        # Fallback: chercher les paragraphes dans l'article ou sur la page
        article_tag = soup.find('article')
        if article_tag:
            paragraphs = [p.get_text(strip=True) for p in article_tag.find_all('p') if len(p.get_text(strip=True)) > 20]
            if paragraphs:
                return ' '.join(paragraphs)

        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p') if len(p.get_text(strip=True)) > 20]
        if paragraphs:
            return ' '.join(paragraphs)

        # Dernier recours, récupérer tout le texte visible
        body_text = soup.get_text(' ', strip=True)
        return body_text if len(body_text) > 100 else ""

    def get_articles_links(self, url: str, max_articles: int = 10) -> List[Dict[str, str]]:
        """Récupère les liens d'articles depuis la page d'accueil"""
        logging.info(f"Recuperation des liens depuis {url}")

        try:
            response = self.make_request(url)
            if not response:
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            articles = []

            selectors = [
                'article a[href*=".html"]',
                '.post-title a[href*=".html"]',
                '.entry-title a[href*=".html"]',
                'h2 a[href*=".html"]',
                'h3 a[href*=".html"]'
            ]

            found_links = set()

            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href and '.html' in href and href not in found_links:
                        full_url = urljoin(url, href)
                        title = link.get_text(strip=True)

                        if title and len(title) > 10:
                            articles.append({'title': title, 'url': full_url})
                            found_links.add(href)

                            if len(articles) >= max_articles:
                                break
                if len(articles) >= max_articles:
                    break

            logging.info(f"{len(articles)} liens d'articles recuperes")
            return articles[:max_articles]
        except Exception as e:
            logging.error(f"Erreur lors de la recuperation des liens: {e}")
            return []

    def scrape_article(self, article_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Scrape le contenu détaillé d'un article"""
        url = article_info['url']
        logging.info(f"Scraping: {article_info['title'][:50]}...")

        try:
            response = self.make_request(url)
            if not response:
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Extraction du titre
            title_selectors = [
                'h1.post-title',
                'h1.entry-title',
                'h1',
                '.post-title',
                '.entry-title'
            ]

            title = ""
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break

            if not title:
                title = article_info.get('title', 'Titre non trouvé')

            # Extraction du contenu
            content = self.extract_content_from_soup(soup)
            content = self.clean_content(content)

            # Si le contenu est encore vide, on essaye un dernier retour sur le body entier
            if not content:
                body_text = soup.get_text(' ', strip=True)
                content = self.clean_content(body_text)

            if not content:
                logging.warning(f"Contenu vide pour l'article: {url}")
                return None

            # Extraction de la date
            date_selectors = [
                'time',
                '.post-date',
                '.entry-date',
                '.published',
                'span.date'
            ]

            date = ""
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date = date_elem.get_text(strip=True)
                    break

            # Extraction de l'auteur
            author_selectors = [
                '.author-name',
                '.post-author',
                '.entry-author',
                'a[rel="author"]',
                '.byline'
            ]

            author = ""
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    break

            article_data = {
                'title': title,
                'content': content,
                'url': url,
                'date': date,
                'author': author,
                'scraped_at': time.time(),
                'word_count': len(content.split())
            }

            logging.info(f"Article scrape: {len(content)} caracteres, {article_data['word_count']} mots")
            return article_data
        except Exception as e:
            logging.error(f"Erreur lors du scraping de {url}: {e}")
            return None

    def clean_content(self, content: str) -> str:
        """Nettoie le contenu de l'article"""
        if not content:
            return ""

        # Supprimer les espaces multiples et les sauts de ligne
        content = re.sub(r'\s+', ' ', content)

        # Supprimer les éléments HTML restants
        content = re.sub(r'<[^>]+>', '', content)

        # Supprimer les caractères spéciaux inutiles mais garder la ponctuation arabe
        content = re.sub(r'[^\w\s\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF.,;:!?()«»""''-]', ' ', content)

        # Supprimer les espaces multiples à nouveau
        content = re.sub(r'\s+', ' ', content)

        return content.strip()

    def clean_text_advanced(self, text: str) -> str:
        """Nettoyage avancé du texte pour l'analyse"""
        if not text:
            return ""

        # Convertir en minuscules
        text = text.lower()

        # Supprimer la ponctuation
        text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)

        # Supprimer les chiffres
        text = re.sub(r'\d+', '', text)

        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)

        # Séparer les mots et filtrer
        words = text.split()
        words = [w for w in words if len(w) > 2]  # Mots de plus de 2 caractères
        words = [w for w in words if w not in STOP_WORDS]  # Supprimer stop words

        return ' '.join(words).strip()

    def analyze_top_words(self, articles: List[Dict[str, Any]], top_n: int = 20, min_freq: int = 2) -> List[Dict[str, int]]:
        """Analyse les mots les plus fréquents"""
        all_words = []

        for article in articles:
            content = article.get('content', '')
            cleaned_content = self.clean_text_advanced(content)
            words = cleaned_content.split()
            all_words.extend(words)

        # Compter les fréquences
        word_counts = Counter(all_words)

        # Filtrer par fréquence minimale
        filtered_counts = {word: count for word, count in word_counts.items() if count >= min_freq}

        # Trier et prendre top N
        top_words = sorted(filtered_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

        return [{"word": word, "count": count} for word, count in top_words]

def create_directories():
    """Crée les répertoires nécessaires"""
    directories = [
        "data",
        "data/bronze",
        "data/silver",
        "data/gold",
        "logs"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Repertoire cree: {directory}")

def save_to_json(data: Any, filepath: str) -> None:
    """Sauvegarde les données en JSON"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logging.info(f"Donnees sauvegardees dans {filepath}")

def main():
    """Fonction principale"""
    logging.info("Demarrage du scraper Hespress ameliore")

    # Créer les répertoires
    create_directories()

    # Configuration
    BASE_URL = "https://www.hespress.com/"
    MAX_ARTICLES = 5  # À augmenter pour la production

    # Initialiser le scraper
    scraper = HespressScraper()

    # 1. Récupérer les liens d'articles
    articles_links = scraper.get_articles_links(BASE_URL, MAX_ARTICLES)

    if not articles_links:
        logging.error("Aucun lien d'article trouve")
        return

    # 2. Scraper chaque article
    articles_data = []
    for i, link_info in enumerate(articles_links, 1):
        logging.info(f"Article {i}/{len(articles_links)}")
        article_data = scraper.scrape_article(link_info)

        if article_data:
            articles_data.append(article_data)

        # Délai entre les requêtes pour respecter le site
        time.sleep(scraper.delay)

    # 3. Sauvegarde en Bronze
    bronze_path = "data/bronze/articles.json"
    save_to_json(articles_data, bronze_path)

    logging.info(f"{len(articles_data)} articles sauvegardes en Bronze")

    # 4. Analyse et sauvegarde en Gold
    if articles_data:
        top_words = scraper.analyze_top_words(articles_data)

        gold_data = {
            "summary": {
                "total_articles": len(articles_data),
                "total_words": sum(a.get('word_count', 0) for a in articles_data),
                "avg_words_per_article": round(sum(a.get('word_count', 0) for a in articles_data) / len(articles_data), 2)
            },
            "top_words": top_words,
            "generated_at": datetime.now().isoformat()
        }

        gold_path = "data/gold/analysis.json"
        save_to_json(gold_data, gold_path)

        logging.info(f"Analyse terminee: {len(top_words)} mots frequents identifies")

    logging.info("Scraping termine avec succes")

if __name__ == "__main__":
    main()