import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2

# --- 1. CONFIGURATION ÉLÉGANTE ---
st.set_page_config(page_title="News Data Platform Admin", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    h1, h2, h3, p { color: #002244 !important; font-family: 'Segoe UI', sans-serif; }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        padding: 20px;
        border-radius: 5px;
    }
    [data-testid="stSidebar"] { background-color: #F7F9FB; border-right: 1px solid #E0E0E0; }
    .stButton>button {
        background-color: #005088;
        color: white;
        font-weight: bold;
        border-radius: 4px;
        border: none;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FONCTIONS DE BASE DE DONNÉES ---
def run_query(query, params=None, commit=False):
    try:
        conn = psycopg2.connect(
            user="postgres", password="admin123", host="localhost", port="5432", database="news_data_platform"
        )
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit:
            conn.commit()
            result = None
        else:
            result = cursor.fetchall()
        conn.close()
        return result
    except Exception:
        return []

# --- 3. SYSTÈME DE LOGIN DANS LA SIDEBAR ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

with st.sidebar:
    st.markdown("## 🔐 ACCÈS ADMIN")
    if not st.session_state.logged_in:
        user_input = st.text_input("Utilisateur", key="user")
        pwd_input = st.text_input("Mot de passe", type="password", key="pwd")
        if st.button("Se connecter"):
            if user_input == "admin" and pwd_input == "pfa2026":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Identifiants incorrects")
    else:
        st.success("Bienvenue, Admin")
        if st.button("Se déconnecter"):
            st.session_state.logged_in = False
            st.rerun()

# --- 4. AFFICHAGE DU DASHBOARD (PUBLIC) ---
st.title("📊 NEWS DATA PLATFORM")
st.markdown("### Hespress | Architecture Gold Layer")
st.divider()

# Charger les données
data_rows = run_query("SELECT category, article_count FROM news_gold_table ORDER BY article_count DESC")
df = pd.DataFrame(data_rows, columns=['category', 'article_count'])

if not df.empty:
    # Métriques KPI
    col1, col2, col3 = st.columns(3)
    col1.metric("TOTAL ARTICLES", f"{df['article_count'].sum()}")
    col2.metric("THÉMATIQUES", f"{len(df)}")
    col3.metric("QUALITÉ", "100% GOLD")

    # Graphique
    fig = px.bar(df, x='category', y='article_count', 
                 color='category',
                 color_discrete_sequence=px.colors.qualitative.Prism,
                 template="plotly_white", text='article_count')
    st.plotly_chart(fig, use_container_width=True)

    # --- 5. ZONE ADMIN (APPARAÎT SEULEMENT SI CONNECTÉ) ---
    if st.session_state.logged_in:
        st.divider()
        st.subheader("🛠️ ADMINISTRATION DES DONNÉES")
        
        with st.expander("Modifier une catégorie en base de données"):
            with st.form("admin_edit_form"):
                target = st.selectbox("Sélectionner la catégorie", df['category'].tolist())
                new_val = st.number_input("Nouveau volume", min_value=0, value=100)
                
                if st.form_submit_button("Mettre à jour PostgreSQL"):
                    run_query(
                        "UPDATE news_gold_table SET article_count = %s WHERE category = %s", 
                        (new_val, target), 
                        commit=True
                    )
                    st.success(f"Modification enregistrée pour {target} !")
                    st.rerun()
    
    # Tableau brut (toujours visible)
    st.write("### 📋 Données brutes")
    st.table(df)

else:
    st.warning("⚠️ Aucune donnée disponible.")