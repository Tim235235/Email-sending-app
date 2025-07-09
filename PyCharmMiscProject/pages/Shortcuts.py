import streamlit as st
import json
import webbrowser
from streamlit.runtime.media_file_storage import MediaFileStorageError
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

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Veuillez d'abord vous connecter.")
    st.stop()

c.execute("""
    CREATE TABLE IF NOT EXISTS app_shortcuts_users
    (
        username     TEXT PRIMARY KEY,
        dvs_dic      TEXT,
        default_view TEXT
    )
""")
conn.commit()

if "username" not in st.session_state or not st.session_state.username:
    st.error("Veuillez vous connecter.")
    st.stop()
else:
    st.session_state.logged_in = True

if "df_view" not in st.session_state:
    st.session_state.df_view = True
    st.rerun()

if "dvs" not in st.session_state:
    st.session_state.dvs = 0

if "current" not in st.session_state:
    st.session_state.current = []

if "saved" not in st.session_state:
    st.session_state.saved = False

def save_to_db():
    c.execute("""
              INSERT INTO app_shortcuts_users (username, dvs_dic, default_view)
              VALUES (%s, %s, %s) ON CONFLICT (username) DO
              UPDATE SET
                  dvs_dic = EXCLUDED.dvs_dic,
                  default_view = EXCLUDED.default_view
              """, (
                  st.session_state.username,
                  json.dumps(st.session_state.dvs_dic),
                  json.dumps(st.session_state.default_view)
              ))
    conn.commit()

def save_changes_df():
    save_to_db()
    st.success("Données enregistrées dans la base de données.")

def save_changes_dvs():
    save_to_db()
    st.success("Données enregistrées dans la base de données.")

def delete_box(key):
    try:
        st.session_state.default_view.pop(str(key))
        st.session_state.dvs_dic.pop(str(key))
        save_changes_dvs()
        st.rerun()
    except KeyError:
        st.error("Rien à supprimer pour cette clé.")

def link_open(url):
    if url:
        st.link_button("Ouvrir l'application", url)
    else:
        st.warning("Aucune URL fournie.")

def dft_view():
    if st.button("Ajouter shortcut ➕"):
        if st.session_state.default_view:
            next_key = str(max(int(k) for k in st.session_state.default_view.keys()) + 1)
        else:
            next_key = "0"
        st.session_state.default_view[next_key] = ""
        st.rerun()

    for key in sorted(st.session_state.default_view.keys(), key=int):
        col = st.columns(1, border=True)
        with col[0]:
            val = st.text_input(
                "| Nom de l'application |",
                value=st.session_state.default_view[key],
                key=f"input_{key}"
            )
            col1, col2 = st.columns([1, 3])
            with col1:
                try:
                    st.image(st.session_state.dvs_dic[key][2], width=200)
                except KeyError:
                    pass
                except MediaFileStorageError:
                    pass
            with col2:
                try:
                    st.text_input("| Description |",
                                  value=st.session_state.dvs_dic[key][0])
                except KeyError:
                    pass
            st.session_state.default_view[key] = val

            col4, col5, col6 = st.columns([3, 11, 2.8])
            with col4:
                try:
                    if st.button("Ouvrir l'application", key=f"open_{key}"):
                        webbrowser.open_new_tab(st.session_state.dvs_dic[key][1])
                except KeyError:
                    st.error("Pas d'URL associée.")
            with col5:
                if st.button("Voir en détail", key=f"detailed_view_{key}"):
                    st.session_state.df_view = False
                    st.session_state.dvs = int(key)
                    st.rerun()
            with col6:
                if st.button("Supprimer 🗑", key=f"delete_{key}"):
                    delete_box(key)

    if st.button("Enregistrer les modifications 📩"):
        save_changes_df()

def dtl_view():
    dvs_key = str(st.session_state.dvs)
    current = st.session_state.dvs_dic.get(dvs_key, ["", "", ""])

    col1, col2, col3 = st.columns([3, 1.5, 1.5], border=True)
    with col1:
        description = st.text_area("Description", value=current[0], key="description")
    with col2:
        link = st.text_area("Lien", value=current[1], key="link")
    with col3:
        url = st.text_area("Image d'affichage (URL ou chemin)", value=current[2], key="url")
        try:
            st.image(url)
        except MediaFileStorageError:
            pass
    st.session_state.dvs_dic[dvs_key] = [description, link, url]
    if st.button("Ouvrir l'application"):
        link_open(link)
    if st.button("Retour"):
        st.session_state.df_view = True
        st.rerun()

st.title("Raccourcis d'applications")

if st.button("Se déconnecter"):
    st.session_state.logged_in = False

else:
    st.write(st.session_state.logged_in)

    if "loaded_from_db" not in st.session_state:
        c.execute("""SELECT dvs_dic, default_view
                     FROM app_shortcuts_users
                     WHERE username = %s""", (st.session_state.username,))
        row = c.fetchone()
        if row:
            dvs_dic_json, default_view_json = row
            st.session_state.dvs_dic = json.loads(dvs_dic_json)
            st.session_state.default_view = json.loads(default_view_json)
        else:
            st.write("Cet utilisateur n'a pas de données.")
            c.execute("""
                INSERT INTO app_shortcuts_users (username, dvs_dic, default_view)
                VALUES (%s, %s, %s);
            """, (st.session_state.username, "{}", "{}"))
            st.session_state.default_view = {}
            st.session_state.dvs_dic = {}
            conn.commit()
        st.session_state.loaded_from_db = True

    if st.toggle("Tip 📌"):
        st.caption("Tip : Créez des raccourcis pour vos applications. "
                   "N'oubliez pas d'enregistrer en utilisant le bouton ENREGISTRER LES MODIFICATIONS. "
                   "Utilisez le bouton SUPPRIMER pour retirer un raccourci. "
                   "Utilisez VOIR EN DÉTAIL pour agrandir et modifier la description, le lien, l'image, etc.")

    if st.session_state.df_view:
        dft_view()
    else:
        dtl_view()

