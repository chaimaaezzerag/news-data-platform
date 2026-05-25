import json
import os
import logging
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Mots clés pour analyse de sentiment basique (en arabe)
POSITIVE_WORDS = set([
    "جيد", "ممتاز", "رائع", "إيجابي", "نجح", "تحسن", "تقدم", "سعيد", "فرح",
    "حسن", "جميل", "مفيد", "قوي", "مثالي", "مبشر", "واعد"
])

NEGATIVE_WORDS = set([
    "سيء", "فشل", "مشكلة", "أزمة", "خطر", "سلبي", "ضعف", "فقدان", "حزن",
    "غضب", "خيبة", "فساد", "عنف", "فقر", "مرض", "حرب"
])

STOP_WORDS = set([
    "في", "من", "على", "و", "إلى", "عن", "هذا", "ذلك", "مع", "كان",
    "كما", "لكن", "ل", "ب", "أو", "أي", "ما", "لم", "لن", "قد", "هي", "هو",
    "كانت", "كانوا", "هناك", "أن", "لا", "أنا", "نحن", "أنت", "أنتم", "هم",
    "الذي", "التي", "الذين", "اللذين", "اللائي", "اللواتي", "أنها", "إنها",
    "كيف", "متى", "أين", "لماذا", "ماذا", "منذ", "حتى", "بين", "خلال",
    "le", "la", "les", "de", "du", "des", "et", "à", "un", "une", "dans", "sur",
    "pour", "par", "avec", "sans", "sous", "entre", "chez", "vers", "pendant",
    "depuis", "jusque", "lorsque", "quand", "comme", "si", "que", "qui", "dont",
    "où", "ce", "cette", "ces", "mon", "ton", "son", "notre", "votre", "leur",
    "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "me", "te", "se",
    "y", "en", "au", "aux", "du", "des",
    "the", "and", "for", "with", "that", "this", "from", "not", "are", "but",
    "you", "your", "have", "has", "was", "were", "will", "can", "its", "all",
    "any", "our", "out", "who", "what", "when", "where", "why", "how"
])

def load_silver_data(filepath: str = "data/silver/cleaned_articles.json") -> List[Dict[str, Any]]:
    """
    Charge les données nettoyées depuis Silver.
    """
    if not os.path.exists(filepath):
        logging.error(f"Fichier {filepath} non trouvé")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    logging.info(f"Chargé {len(data)} articles nettoyés depuis {filepath}")
    return data

def analyze_sentiment(article: Dict[str, Any]) -> str:
    """
    Analyse basique du sentiment d'un article.
    Retourne 'positive', 'negative', ou 'neutral'.
    """
    content = article.get('content_cleaned', '').lower()
    words = set(content.split())

    positive_count = len(words & POSITIVE_WORDS)
    negative_count = len(words & NEGATIVE_WORDS)

    if positive_count > negative_count:
        return 'positive'
    elif negative_count > positive_count:
        return 'negative'
    else:
        return 'neutral'

def analyze_trends_by_date(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyse les tendances par date (si disponible).
    """
    date_trends = defaultdict(int)
    word_trends = defaultdict(Counter)

    for article in articles:
        # Utiliser la date de scraping si pas de date d'article
        date_str = article.get('date', '')
        if not date_str:
            # Utiliser scraped_at
            timestamp = article.get('scraped_at', 0)
            date = datetime.fromtimestamp(timestamp).date()
            date_str = date.isoformat()
        else:
            # Parser la date (supposer format YYYY-MM-DD)
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                date_str = date.isoformat()
            except:
                date_str = 'unknown'

        date_trends[date_str] += 1

        # Mots par date
        content = article.get('content_cleaned', '')
        words = content.split()
        word_trends[date_str].update(words)

    # Top mots par date
    top_words_by_date = {}
    for date, counter in word_trends.items():
        top_words_by_date[date] = counter.most_common(5)

    return {
        "articles_by_date": dict(date_trends),
        "top_words_by_date": dict(top_words_by_date)
    }

def analyze_categories(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Classification basique par catégories (basée sur mots-clés).
    """
    categories = {
        "politique": ["حكومة", "وزير", "انتخابات", "سياسة", "رئيس", "حزب", "برلمان"],
        "économie": ["اقتصاد", "مال", "أسعار", "شركة", "عملة", "استثمار", "تجارة"],
        "sport": ["كرة", "مباراة", "لاعب", "فريق", "رياضة", "بطولة", "كأس"],
        "santé": ["مرض", "طبيب", "علاج", "صحة", "وباء", "مستشفى", "دواء"],
        "technologie": ["تكنولوجيا", "إنترنت", "هاتف", "برمجة", "ذكاء", "رقمي"],
        "société": ["مجتمع", "ثقافة", "تعليم", "شباب", "نساء", "أسرة"],
        "international": ["دولي", "خارجي", "أجنبي", "عالمي", "منظمة"]
    }

    categorized_articles = []

    for article in articles:
        content = article.get('content_cleaned', '').lower()
        article_categories = []

        for cat, keywords in categories.items():
            if any(keyword in content for keyword in keywords):
                article_categories.append(cat)

        article_copy = article.copy()
        article_copy['categories'] = article_categories if article_categories else ['général']
        article_copy['sentiment'] = analyze_sentiment(article)
        categorized_articles.append(article_copy)

    return categorized_articles

def analyze_top_words(articles: List[Dict[str, Any]], top_n: int = 20, min_freq: int = 2) -> List[Dict[str, int]]:
    """
    Analyse les mots les plus fréquents avec filtrage avancé.
    """
    all_words = []

    for article in articles:
        content = article.get('content_cleaned', '')
        words = [w.strip() for w in content.split() if w.strip()]
        words = [w for w in words if 4 <= len(w) <= 20]
        words = [w for w in words if w.lower() not in STOP_WORDS and not w.isdigit()]
        all_words.extend(words)

    word_counts = Counter(all_words)
    filtered_counts = {word: count for word, count in word_counts.items() if count >= min_freq}
    top_words = sorted(filtered_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return [{"word": word, "count": count} for word, count in top_words]

def generate_gold_data(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Génère toutes les analyses pour la couche Gold.
    """
    # Articles avec catégories et sentiment
    categorized_articles = analyze_categories(articles)

    # Analyse des mots
    top_words = analyze_top_words(articles)

    # Tendances temporelles
    trends = analyze_trends_by_date(articles)

    # Statistiques générales
    total_words = sum(len(a.get('content_cleaned', '').split()) for a in articles)
    avg_words = round(total_words / len(articles), 2) if articles else 0

    # Répartition par sentiment
    sentiment_counts = Counter(a.get('sentiment', 'neutral') for a in categorized_articles)

    # Répartition par catégories
    category_counts = Counter()
    for article in categorized_articles:
        for cat in article.get('categories', []):
            category_counts[cat] += 1

    gold_data = {
        "summary": {
            "total_articles": len(articles),
            "total_words": total_words,
            "avg_words_per_article": avg_words,
            "sentiment_distribution": dict(sentiment_counts),
            "category_distribution": dict(category_counts)
        },
        "top_words": top_words,
        "trends": trends,
        "categorized_articles": categorized_articles,
        "generated_at": datetime.now().isoformat()
    }

    return gold_data

def save_gold_data(gold_data: Dict[str, Any], filepath: str = "data/gold/analysis.json") -> None:
    """
    Sauvegarde les analyses Gold.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(gold_data, f, ensure_ascii=False, indent=4)
    logging.info(f"Analyses Gold sauvegardées dans {filepath}")

def main():
    """
    Fonction principale pour l'analyse et transformation.
    """
    # Charger les données Silver
    silver_articles = load_silver_data()

    if not silver_articles:
        logging.error("Aucune donnée Silver trouvée")
        return

    # Générer les analyses Gold
    gold_data = generate_gold_data(silver_articles)

    # Sauvegarder
    save_gold_data(gold_data)

    logging.info("Analyses Gold terminées")

if __name__ == "__main__":
    main()