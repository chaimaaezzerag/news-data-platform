#!/usr/bin/env python3
"""Génère un dashboard de visualisation et un fichier Excel pour le projet.

Ce script produit :
- un classeur Excel `visualization/news_dashboard.xlsx`
- des graphiques PNG dans `visualization/output/`
- un support de visualisation pour Power BI / Excel / Python
"""

import json
import os
import sqlite3
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
VIS_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = VIS_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

from config.settings import DATA_PATHS, DB_CONFIG


def load_gold_analysis() -> dict:
    gold_path = BASE_DIR / DATA_PATHS.get("gold", "data/gold/analysis.json")
    if gold_path.exists():
        with open(gold_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def query_sqlite_metrics() -> dict:
    db_path = DB_CONFIG.get("database")
    if not db_path or not Path(db_path).exists():
        return {}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM articles;")
    article_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT word, frequency FROM word_frequencies ORDER BY frequency DESC LIMIT 20;"
    )
    top_words = [{"word": row[0], "count": row[1]} for row in cursor.fetchall()]

    cursor.execute(
        "SELECT date, COUNT(*) FROM articles GROUP BY date ORDER BY date;"
    )
    trends = {row[0] or "unknown": row[1] for row in cursor.fetchall()}

    cursor.close()
    conn.close()

    return {
        "summary": {"total_articles": article_count},
        "top_words": top_words,
        "trends": {"articles_by_date": trends},
    }


def format_summary(summary: dict) -> pd.DataFrame:
    rows = []
    for key, value in summary.items():
        if isinstance(value, dict):
            continue
        rows.append({"metric": key, "value": value})
    return pd.DataFrame(rows)


def build_dashboard_data(analysis: dict) -> dict:
    if analysis:
        summary = analysis.get("summary", {})
        top_words = analysis.get("top_words", [])
        trends = analysis.get("trends", {}).get("articles_by_date", {})
    else:
        db_metrics = query_sqlite_metrics()
        summary = db_metrics.get("summary", {})
        top_words = db_metrics.get("top_words", [])
        trends = db_metrics.get("trends", {}).get("articles_by_date", {})

    # Fallback values
    summary.setdefault("total_articles", 0)
    top_words = top_words[:20]
    trends = {k: v for k, v in trends.items() if v is not None}

    return {
        "summary": summary,
        "top_words": top_words,
        "articles_by_date": trends,
    }


def save_excel(dashboard_data: dict) -> Path:
    excel_path = VIS_DIR / "news_dashboard.xlsx"
    summary_df = format_summary(dashboard_data["summary"])
    top_words_df = pd.DataFrame(dashboard_data["top_words"])
    trends_df = pd.DataFrame(
        sorted(dashboard_data["articles_by_date"].items()),
        columns=["date", "articles_count"],
    )

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        top_words_df.to_excel(writer, sheet_name="Top Words", index=False)
        trends_df.to_excel(writer, sheet_name="Evolution", index=False)

    return excel_path


def plot_charts(dashboard_data: dict) -> None:
    plt.style.use("seaborn-v0_8")

    # Evolution du nombre d'articles
    dates = list(dashboard_data["articles_by_date"].keys())
    counts = list(dashboard_data["articles_by_date"].values())
    if dates and counts:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(dates, counts, marker="o", linestyle="-", color="#2a7ae2")
        ax.set_title("Évolution du nombre d'articles")
        ax.set_xlabel("Date")
        ax.set_ylabel("Nombre d'articles")
        ax.grid(True, alpha=0.4)
        fig.autofmt_xdate(rotation=45)
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / "articles_evolution.png")
        plt.close(fig)

    # Top mots
    if dashboard_data["top_words"]:
        top_words = dashboard_data["top_words"][:15]
        df = pd.DataFrame(top_words)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(df["word"][::-1], df["count"][::-1], color="#17a2b8")
        ax.set_title("Top mots")
        ax.set_xlabel("Fréquence")
        ax.set_ylabel("Mot")
        fig.tight_layout()
        fig.savefig(OUTPUT_DIR / "top_words.png")
        plt.close(fig)

    # Résumé des métriques
    if dashboard_data["summary"]:
        summary = dashboard_data["summary"]
        labels = []
        values = []
        if summary.get("positive") is not None or summary.get("negative") is not None:
            sentiment = {
                "positive": summary.get("positive", 0),
                "neutral": summary.get("neutral", 0),
                "negative": summary.get("negative", 0),
            }
            labels = [k for k, v in sentiment.items() if v > 0]
            values = [v for v in sentiment.values() if v > 0]
        elif summary.get("total_articles") is not None:
            labels = ["Articles"]
            values = [summary["total_articles"]]

        if labels and values:
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.pie(values, labels=labels, autopct="%1.0f%%", startangle=140)
            ax.set_title("Résumé des métriques")
            fig.tight_layout()
            fig.savefig(OUTPUT_DIR / "summary_pie.png")
            plt.close(fig)


def main() -> None:
    analysis = load_gold_analysis()
    dashboard_data = build_dashboard_data(analysis)

    excel_path = save_excel(dashboard_data)
    plot_charts(dashboard_data)

    print("Dashboard créé avec succès !")
    print(f"• Fichier Excel : {excel_path}")
    print(f"• Graphiques : {OUTPUT_DIR}")
    print("• Ouvrez `visualization/dashboard.pbix` pour Power BI ou utilisez le fichier Excel dans Power BI / Excel.")


if __name__ == "__main__":
    main()
