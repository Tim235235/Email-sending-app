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

st.title("Connexion")

username_input = st.text_input("Nom d'utilisateur")
password_input = st.text_input("Mot de passe", type="password")

if st.button("Se connecter"):
    c.execute("SELECT password FROM email_credentials WHERE username = %s", (username_input,))
    result = c.fetchone()
    if result and result[0] == password_input:
        st.session_state.logged_in = True
        st.session_state.username = username_input
        st.success("Connexion réussie !")
    else:
        st.error("Nom d'utilisateur ou mot de passe incorrect.")
