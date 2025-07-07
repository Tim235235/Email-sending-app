import streamlit as st

st.title("Page principale")
st.subheader("| À propos |")

st.write("Ce site web est un outil de productivité conçu pour gérer les e-mails "
         "et organiser des raccourcis vers vos applications.")

col1, col2 = st.columns([4, 4], border=True)

with col1:
    st.subheader("Gestion des e-mails 📧")
    st.write("Les utilisateurs peuvent saisir et gérer les informations des e-mails pour plusieurs destinataires, "
             "y compris les données personnelles (nom, e-mail, entreprise), le contenu du message et son statut. "
             "Les e-mails peuvent être ajoutés, modifiés et enregistrés dans un tableau dynamique. "
             "Une fois prêts, ils peuvent être envoyés en masse, et les champs ou l’aperçu complet peuvent être vidés. "
             "L’application propose des fonctionnalités telles que l’ajout de CC/BCC, l’édition du contenu, "
             "et le suivi de l’état d’envoi.")

with col2:
    st.subheader("Raccourcis d'applications 🚪")
    st.write("Cette section permet de créer, gérer et personnaliser des raccourcis vers vos applications. "
             "Vous pouvez ajouter de nouveaux raccourcis, modifier leurs descriptions, liens et images, "
             "et même ouvrir les applications directement depuis le site. "
             "La vue détaillée offre un aperçu plus complet de chaque raccourci pour des modifications spécifiques, "
             "et les changements sont sauvegardés pour une utilisation future. "
             "Ensemble, le site aide à optimiser à la fois la communication par e-mail et la gestion des applications, "
             "offrant une interface simple pour traiter ces deux tâches efficacement.")
