import os
import streamlit as st
import pandas as pd
import json
import smtplib
import ssl
from email.message import EmailMessage
import psycopg2

# Database connection using secrets
conn = psycopg2.connect(
    host=st.secrets["db"]["host"],
    database=st.secrets["db"]["database"],
    user=st.secrets["db"]["user"],
    password=st.secrets["db"]["password"],
    port=st.secrets["db"]["port"],
    sslmode="require"
)
c = conn.cursor()

# Check login session
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in first.")

else:
    st.session_state.logged_in = True

if st.button("Log out"):
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.warning("No username provided.")
    st.stop()

# Create table if not exists
c.execute("""
CREATE TABLE IF NOT EXISTS email_user_info (
    username TEXT PRIMARY KEY,
    email_info TEXT,
    app_password TEXT,
    email TEXT
)
""")
conn.commit()

# Hardcoded email credentials - **use your own valid app password here**
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "timofeysona@gmail.com"
SENDER_PASSWORD = "hxptuxcbawossrek"  # Your real app password here


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
    if result:
        loaded_data = json.loads(result[0])
        st.session_state.df = pd.DataFrame(loaded_data)
        st.success("Data loaded successfully!")
    else:
        st.warning("No saved data found. Using defaults.")
        initialize_default_dataframe()


def initialize_default_dataframe():
    st.session_state.df = pd.DataFrame({
        "Row Number": [""],
        "First Name": [""],
        "Last Name": [""],
        "Email": [""],
        "Company": [""],
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
                st.session_state.name_input,
                st.session_state.last_name_input,
                st.session_state.email_address_input,
                st.session_state.company_input,
                st.session_state.send_status_input,
                st.session_state.cc_input,
                st.session_state.bcc_input,
                st.session_state.subject_input,
                st.session_state.email_input,
            ]
            for col, value in zip(st.session_state.df.columns[1:], data):
                st.session_state.df.at[row_idx, col] = value
            save_data()
            st.success(f"Updated row {row_idx} content.")
        else:
            st.error("Row index out of range.")
    except ValueError:
        st.error("Please enter a valid row number.")


def email_construct(server, to_email, sbj, body, cc, bcc):
    msg = EmailMessage()
    msg["Subject"] = sbj
    msg["From"] = SENDER_EMAIL
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
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            for i, row in enumerate(list_list):
                if len(row) < 9:
                    st.warning(f"Skipping row {i}: expected 9 fields, got {len(row)}")
                    continue
                prenom, nom, email_addr, company, send_stat, cc_field, bcc_field, sujet, body = row
                if str(send_stat).strip().lower() == "yes":
                    try:
                        email_construct(server, email_addr, sujet, body, cc=cc_field, bcc=bcc_field)
                        st.success(f"Email sent to {email_addr}")
                    except Exception as e:
                        st.error(f"Failed to send email to {email_addr}: {e}")
                else:
                    st.info(f"Skipping {email_addr} because Send Status is '{send_stat}'")
    except Exception as error:
        st.error(f"An error occurred: {error}")


def clear_text():
    for key in ["name_input", "last_name_input", "email_address_input", "company_input",
                "send_status_input", "cc_input", "bcc_input", "subject_input", "email_input", "row_input"]:
        st.session_state[key] = ""


def clear_table():
    initialize_default_dataframe()
    save_data()
    load_data()


def delete_row():
    if del_index >= 0:
        for heading in headings:
            del st.session_state.df[heading][del_index]
        save_data()
        load_data()


if st.session_state.logged_in:

    if "df" not in st.session_state:
        load_data()

    for i in range(len(st.session_state.df)):
        st.session_state.df.at[i, "Row Number"] = i

    if "toggled" not in st.session_state:
        st.session_state.toggled = False

    headings = st.session_state.df.columns.tolist()

    # Removed all email/app password input fields here

    st.title("Fill out the email info:")
    if st.toggle("Tip hints 📌"):
        st.session_state.toggled = True
    else:
        st.session_state.toggled = False

    if st.session_state.toggled:
        st.caption(
            "TIP HINT: Fill out the information below and click ADD EMAIL to update the overview table. "
            "You can clear inputs with CLEAR TEXT. Editing directly in the table does NOT autosave."
        )

    list_length = len(st.session_state.df)
    st.text_input("Enter receiver's first name", key="name_input")
    st.text_input("Enter receiver's last name", key="last_name_input")
    st.text_input("Enter receiver's email address", key="email_address_input")
    st.text_input("Enter company", key="company_input")
    st.selectbox("Send status", options=["No", "Yes"], index=0, key="send_status_input")
    st.text_input("Enter CC (optional)", key="cc_input")
    st.text_input("Enter BCC (optional)", key="bcc_input")
    st.text_input("Enter subject", key="subject_input")
    st.text_area("Enter email content", key="email_input")
    st.selectbox("Enter row number to paste the info", options=range(0, list_length), key="row_input")

    st.button("Add Email ➕", on_click=add_info)
    st.button("Clear text 🗑", on_click=clear_text)

    st.title("Emails overview")
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
            "TIP HINT: Press SEND EMAILS to send all emails or CLEAR OVERVIEW to reset."
            "\nSelect a row below and press CONFIRM DELETE to remove it."
        )

    if st.button("Send Emails 📨"):
        email_send()

    st.button("Clear Overview 🗑", on_click=clear_table)
    del_index = st.selectbox("Delete row", options=range(0, list_length))
    st.button("Confirm Delete", on_click=delete_row)
