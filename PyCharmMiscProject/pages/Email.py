import streamlit as st
import pandas as pd
import json
import smtplib
import ssl
from email.message import EmailMessage
import psycopg2

conn = psycopg2.connect(
    host=st.secrets["db"]["host"],
    database=st.secrets["db"]["database"],
    user=st.secrets["db"]["user"],
    password=st.secrets["db"]["password"],
    port=st.secrets["db"]["port"],
    sslmode="require"
)
c = conn.cursor()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = "demo_user"

c.execute("""
CREATE TABLE IF NOT EXISTS email_user_info (
    username TEXT PRIMARY KEY,
    email_info TEXT,
    app_password TEXT,
    email TEXT
)
""")
conn.commit()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

def save_data():
    data_to_save = st.session_state.df.to_dict(orient="list")
    c.execute("""
        INSERT INTO email_user_info (username, email_info)
        VALUES (%s, %s) ON CONFLICT (username) DO
        UPDATE SET email_info = EXCLUDED.email_info
    """, (st.session_state.username, json.dumps(data_to_save)))
    conn.commit()

def load_data():
    c.execute("SELECT email_info FROM email_user_info WHERE username = %s", (st.session_state.username,))
    result = c.fetchone()
    if result and result[0]:
        loaded_data = json.loads(result[0])
        st.session_state.df = pd.DataFrame(loaded_data)
        st.success("Données chargées avec succès !")
    else:
        st.warning("Aucune donnée sauvegardée trouvée. Utilisation des valeurs par défaut.")
        initialize_default_dataframe()

def initialize_default_dataframe():
    st.session_state.df = pd.DataFrame({
        "Row Number": [0],
        "Email": [""],
        "Send Status": [""],
        "CC": [""],
        "BCC": [""],
        "Subject": [""],
        "Content": [""],
    })

def add_info():
    try:
        row_idx = int(st.session_state.row_input)
        if 0 <= row_idx < len(st.session_state.df):
            data = [
                st.session_state.email_address_input,
                st.session_state.send_status_input,
                st.session_state.cc_input,
                st.session_state.bcc_input,
                st.session_state.subject_input,
                st.session_state.email_input,
            ]
            for col, value in zip(st.session_state.df.columns[1:], data):
                st.session_state.df.at[row_idx, col] = value
            save_data()
            st.success(f"Ligne {row_idx} mise à jour.")
        else:
            st.error("Index de ligne hors plage.")
    except ValueError:
        st.error("Veuillez entrer un numéro de ligne valide.")

def clear_text():
    for key in ["email_address_input", "send_status_input", "cc_input",
                "bcc_input", "subject_input", "email_input", "row_input"]:
        st.session_state[key] = ""

def email_construct(server, to_email, sbj, body, cc, bcc):
    msg = EmailMessage()
    msg["Subject"] = sbj
    msg["From"] = st.session_state.username
    msg["To"] = to_email
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    msg.set_content(body)
    server.send_message(msg)

def email_send():
    list_list = st.session_state.df.values.tolist()
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(st.session_state.user_mail, st.session_state.app_password)
            for i, row in enumerate(list_list):
                if len(row) < 7:
                    st.warning(f"Ligne {i} ignorée : attendu 7 champs, reçu {len(row)}")
                    continue
                _, email_addr, send_stat, cc_field, bcc_field, sujet, body = row
                if str(send_stat).strip().lower() == "yes":
                    try:
                        email_construct(server, email_addr, sujet, body, cc=cc_field, bcc=bcc_field)
                        st.success(f"Email envoyé à {email_addr}")
                    except Exception as e:
                        st.error(f"Échec de l'envoi à {email_addr} : {e}")
                else:
                    st.info(f"{email_addr} ignoré car statut d'envoi = '{send_stat}'")
    except Exception as error:
        st.error(f"Une erreur est survenue : {error}")


def clear_table():
    initialize_default_dataframe()
    save_data()
    load_data()

def delete_row(del_index, headings):
    if 0 <= del_index < len(st.session_state.df):
        st.session_state.df = st.session_state.df.drop(index=del_index).reset_index(drop=True)
        for i in range(len(st.session_state.df)):
            st.session_state.df.at[i, "Row Number"] = i
        save_data()
        load_data()

if st.session_state.logged_in:
    if st.button("Se déconnecter"):
    st.session_state.logged_in = False
    st.rerun()

    if "df" not in st.session_state:
        load_data()

    for i in range(len(st.session_state.df)):
        st.session_state.df.at[i, "Row Number"] = i

    if "toggled" not in st.session_state:
        st.session_state.toggled = False

    if "user_mail" not in st.session_state:
        st.session_state.user_mail = ""

    if "app_password" not in st.session_state:
        st.session_state.app_password = ""

    headings = st.session_state.df.columns.tolist()

    st.session_state.user_mail = st.text_input("Saisir l'adresse électronique de l'utilisateur", value=st.session_state.user_mail)
    st.session_state.app_password = st.text_input("Saisir le mot de passe de l'application", value=st.session_state.app_password, type="password")
    st.caption("Comment obtenir un MOT DE PASSE APP : https://support.google.com/accounts/answer/185833?hl=en")

    st.title("Remplissez les informations de l'email :")
    if st.toggle("Tip 📌"):
        st.session_state.toggled = True
    else:
        st.session_state.toggled = False

    if st.session_state.toggled:
        st.caption(
            "Tip : Remplissez les champs ci-dessous et cliquez sur AJOUTER L'EMAIL pour mettre à jour le tableau."
            " Vous pouvez effacer les champs avec EFFACER LE TEXTE."
            " Modifier directement dans le tableau n'enregistre PAS automatiquement."
        )

    list_length = len(st.session_state.df)
    st.text_input("Adresse email du destinataire", key="email_address_input")
    st.selectbox("Statut d'envoi", options=["No", "Yes"], index=0, key="send_status_input")
    st.text_input("CC (optionnel)", key="cc_input")
    st.text_input("BCC (optionnel)", key="bcc_input")
    st.text_input("Objet", key="subject_input")
    st.text_area("Contenu de l'email", key="email_input")
    st.selectbox("Numéro de ligne pour coller les infos", options=range(0, list_length), key="row_input")

    st.button("Ajouter l'email ➕", on_click=add_info)
    st.button("Effacer le texte 🗑", on_click=clear_text)

    st.title("Aperçu des emails")
    edited_df = st.data_editor(
        st.session_state.df,
        num_rows="dynamic",
        key="editor_df",
        width=1000,
        disabled=["Row Number"]
    )
    st.session_state.df = edited_df

    if st.session_state.toggled:
        st.caption(
            "Tip : Cliquez sur ENVOYER LES EMAILS pour envoyer tous les emails ou EFFACER L'APERÇU pour tout réinitialiser."
            "\nSélectionnez une ligne et cliquez sur CONFIRMER LA SUPPRESSION pour la retirer."
        )

    if st.button("Envoyer les emails 📨"):
        email_send()

    st.button("Effacer l'aperçu 🗑", on_click=clear_table)
    del_index = st.selectbox("Supprimer la ligne", options=range(0, list_length))
    st.button("Confirmer la suppression", on_click=delete_row, args=(del_index, headings))
else:
    st.warning(""Veuillez d'abord vous connecter.")
