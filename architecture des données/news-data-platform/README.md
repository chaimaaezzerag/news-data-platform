# 📊 News Data Platform - Architecture Medallion

## 🎓 Cadre du Projet
* **Auteurs** : Marwa El Omari Alaoui & Chaimaa Ezzerag & Sasam (Mr Fruit)
* **Type** : Projet de Fin d'Année (PFA)
* **Domaine** : Data Engineering & Analytics
* **Année universitaire** : 2025 - 2026

---

## 📝 Présentation du Projet
Ce projet consiste en une plateforme de traitement de données d'actualités en temps réel, structurée selon une **Architecture Medallion** (Bronze, Silver, Gold). L'objectif est d'extraire, transformer et charger (ETL) des données brutes pour les transformer en indicateurs stratégiques exploitables via un dashboard interactif professionnel.
🛠️ Note sur le Développement Frontend
Note aux évaluateurs : L'interface utilisateur de ce dashboard a été entièrement conçue et stylisée manuellement. Nous avons fait le choix de ne pas utiliser de templates pré-construits.

Chaque élément visuel — de la typographie élégante à la gestion du design "Executive Slim" — a été codé via des injections HTML5 et CSS3 personnalisées. Ce choix technique nous a permis de garantir une identité visuelle sobre et professionnelle, parfaitement adaptée aux exigences d'une plateforme de gouvernance de données.

### Points Clés :
* **Pipeline ETL Automatisée** : Intégration de données brutes vers une base PostgreSQL containerisée.
* **Architecture Gold Layer** : Données nettoyées et agrégées pour une analyse métier immédiate.
* **Dashboard Dynamique** : Interface Streamlit moderne connectée en temps réel via Docker.
* **Gouvernance & Sécurité** : Module d'administration restreint par authentification pour la gestion des données.

---

## 🏗️ Architecture Technique
Le projet repose sur une stack technologique moderne et robuste :

* **Langage** : Python 3.10+
* **Base de Données** : PostgreSQL (Dockerisé)
* **Visualisation** : Streamlit & Plotly (Design "Executive Slim")
* **Interface DB** : Psycopg2 (Requêtes SQL dynamiques)
* **Conteneurisation** : Docker & Docker Compose

---

## 🚀 Installation et Lancement

### 1. Prérequis
* Docker Desktop installé.
* Python 3.x installé sur votre machine.

### 2. Installation des bibliothèques
Installez les dépendances nécessaires via votre terminal :
```bash
pip install streamlit pandas plotly psycopg2-binary

3. Démarrage de l'infrastructure
Lancez le conteneur PostgreSQL :

Bash
docker-compose up -d

4. Lancement du Dashboard
Exécutez l'application Streamlit :

Bash
python -m streamlit run app.py
🔐 Gouvernance & Sécurité
Le dashboard intègre deux niveaux de privilèges pour garantir l'intégrité de la Gold Layer :

Mode Consultation (Public) : Visualisation des indicateurs clés (KPIs) et des graphiques de distribution.

Mode Administration (Privé) : Accessible uniquement via login. Ce mode active un module CRUD permettant de modifier les volumes en base de données pour simuler des mises à jour de flux.

Identifiants par défaut :

Utilisateur : admin

Mot de passe : pfa2026

📁 Structure du Projet
Plaintext
news-data-platform/
├── app.py                  # Application Streamlit (Interface Premium)
├── data/
│   └── scripts/            # Pipeline ETL (Bronze -> Silver -> Gold)
├── docker-compose.yml      # Configuration du service PostgreSQL
└── README.md               # Documentation technique