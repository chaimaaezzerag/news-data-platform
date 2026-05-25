import json

INPUT_FILE = "data/bronze/articles.json"
OUTPUT_FILE = "data/silver/valid_articles.json"


def validate_article(article):

    if not article.get("title"):
        return False

    if not article.get("content"):
        return False

    if len(article["content"]) < 50:
        return False

    return True


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    articles = json.load(f)

valid_articles = [a for a in articles if validate_article(a)]

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(valid_articles, f, ensure_ascii=False, indent=4)

print(f"{len(valid_articles)} articles valides sauvegardés")