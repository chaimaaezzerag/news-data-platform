-- Initialisation de la base de données pour news-data-platform

-- Création des tables si elles n'existent pas
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

CREATE TABLE IF NOT EXISTS word_frequencies (
    id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    frequency INTEGER NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(word, date)
);

CREATE TABLE IF NOT EXISTS article_categories (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id),
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date);
CREATE INDEX IF NOT EXISTS idx_articles_sentiment ON articles(sentiment);
CREATE INDEX IF NOT EXISTS idx_word_frequencies_word ON word_frequencies(word);
CREATE INDEX IF NOT EXISTS idx_word_frequencies_date ON word_frequencies(date);