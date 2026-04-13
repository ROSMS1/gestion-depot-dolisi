import streamlit as st
import pandas as pd
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Gestion Dépôt Dolisie", layout="wide")

# 1. Chargement des données (Simulé à partir de votre fichier)
@st.cache_data
def load_data():
    # Ici, nous créons la structure basée sur votre fichier Dolisie
    data = {
        'S/N': ['SN12345', 'SN67890'],
        'Equipement': ['MRFU', 'RTN950'],
        'Marque': ['Huawei', 'Nokia'],
        'Statut': ['Disponible', 'Disponible'],
        'Date_Entree': [datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d")],
        'Localisation': ['Dépôt Dolisie', 'Dépôt Dolisie']
    }
    return pd.DataFrame(data)

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- INTERFACE MOBILE ---
st.title("📦 Hub Logistique - Dolisie")

menu = ["Inventaire", "📥 Entrée / Ajout", "📤 Sortie / Mouvement", "📋 Audit"]
choice = st.sidebar.selectbox("Navigation", menu)

# --- SECTION : INVENTAIRE ---
if choice == "Inventaire":
    st.subheader("État du Stock")
    
    # Filtres rapides
    col1, col2 = st.columns(2)
    with col1:
        filtre_marque = st.selectbox("Marque", ["Toutes"] + list(st.session_state.df['Marque'].unique()))
    
    display_df = st.session_state.df
    if filtre_marque != "Toutes":
        display_df = display_df[display_df['Marque'] == filtre_marque]
    
    st.dataframe(display_df, use_container_width=True)

# --- SECTION : AJOUTER ---
elif choice == "📥 Entrée / Ajout":
    st.subheader("Enregistrer un nouvel équipement")
    with st.form("ajout_form"):
        new_sn = st.text_input("Numéro de Série (S/N)")
        new_item = st.text_input("Nom de l'équipement (ex: MRFU)")
        new_brand = st.selectbox("Marque", ["Huawei", "Nokia", "Eltek", "Ceragon"])
        submit = st.form_submit_button("Ajouter au dépôt")
        
        if submit:
            new_row = {
                'S/N': new_sn, 'Equipement': new_item, 'Marque': new_brand,
                'Statut': 'Disponible', 'Date_Entree': datetime.now().strftime("%Y-%m-%d"),
                'Localisation': 'Dépôt Dolisie'
            }
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Équipement {new_sn} ajouté avec succès !")

# --- SECTION : SORTIE ---
elif choice == "📤 Sortie / Mouvement":
    st.subheader("Sortie de matériel vers site")
    sn_to_move = st.selectbox("Choisir le S/N à sortir", st.session_state.df[st.session_state.df['Statut'] == 'Disponible']['S/N'])
    dest = st.text_input("Destination (Nom du Site)")
    responsable = st.text_input("Technicien responsable")
    
    if st.button("Confirmer la sortie"):
        idx = st.session_state.df.index[st.session_state.df['S/N'] == sn_to_move].tolist()[0]
        st.session_state.df.at[idx, 'Statut'] = 'Sorti / Installé'
        st.session_state.df.at[idx, 'Localisation'] = dest
        st.warning(f"L'équipement {sn_to_move} est maintenant localisé à {dest}")

# --- SECTION : AUDIT ---
elif choice == "📋 Audit":
    st.subheader("Rapport de disponibilité")
    total = len(st.session_state.df)
    dispo = len(st.session_state.df[st.session_state.df['Statut'] == 'Disponible'])
    
    st.metric("Total Équipements", total)
    st.metric("Disponibilité", f"{dispo} unités", delta=f"{(dispo/total)*100:.1f}%")
