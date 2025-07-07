import streamlit as st
import psycopg2

# Connexion à la base de données
conn = psycopg2.connect(
    host=st.secrets["db"]["host"],
    database=st.secrets["db"]["database"],
    user=st.secrets["db"]["user"],
    password=st.secrets["db"]["password"],
    port=st.secrets["db"]["port"],
    sslmode="require"
)
c = conn.cursor()

# Créer la table si elle n'existe pas
c.execute("""
CREATE TABLE IF NOT EXISTS email_credentials (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")
conn.commit()

# Initialisation session_state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

st.title("Inscription")

username_input = st.text_input("Choisissez un nom d'utilisateur").strip()
password_input = st.text_input("Choisissez un mot de passe", type="password").strip()

if st.button("S'inscrire"):
    if username_input and password_input:
        with st.spinner("Création de votre compte..."):
            try:
                c.execute("""
                    INSERT INTO email_credentials (username, password)
                    VALUES (%s, %s)
                    ON CONFLICT (username) DO NOTHING
                """, (username_input, password_input))
                conn.commit()
                if c.rowcount == 0:
                    st.warning("Ce nom d'utilisateur existe déjà. Veuillez en choisir un autre.")
                else:
                    st.success("Inscription réussie ! Vous pouvez maintenant vous connecter.")
            except Exception as e:
                st.error(f"Erreur : {e}")
    else:
        st.warning("Veuillez saisir un nom d'utilisateur et un mot de passe.")
