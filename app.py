import os
import sys
import pandas as pd
import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.exc import IntegrityError

# --- CONFIGURATION DE LA BASE DE DONNÉES ---
DB_URL = "sqlite:///depot_dolisie.db"
engine = create_engine(DB_URL, echo=False)

class Base(DeclarativeBase):
    pass

class Equipement(Base):
    __tablename__ = "equipements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    serial_no = Column(String(100), nullable=False)
    materia_no = Column(String(100))
    materia_name = Column(String(255))
    materia_status = Column(String(50))
    warehouse_no = Column(String(100))
    warehouse_name = Column(String(100))
    location_name = Column(String(100))
    material_belong = Column(String(50))
    material_type = Column(String(50))
    material_manufacture = Column(String(100))
    quantity = Column(Integer)
    unit = Column(String(20))
    domain = Column(String(100))
    sub_domain = Column(String(100))
    fault_phenomen = Column(String(255))
    ot_number = Column(String(100))
    inserted_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("serial_no", name="uq_serial"),)

# Création de la table si elle n'existe pas
Base.metadata.create_all(engine)

# --- FONCTIONS UTILES ---
def normalize_str(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    return s if s not in ("nan", "", "NaN") else None

def load_data_into_db(filepath):
    """Importe les données du fichier Excel/CSV vers la base SQL"""
    if not os.path.exists(filepath):
        return False
    
    df = pd.read_csv(filepath) if filepath.endswith('.csv') else pd.read_excel(filepath)
    df.columns = [c.strip() for c in df.columns]
    
    with Session(engine) as session:
        for _, row in df.iterrows():
            sn = normalize_str(row.get("Serial No"))
            if not sn: continue
            
            equip = Equipement(
                serial_no=sn,
                materia_name=normalize_str(row.get("Materia Name")),
                material_manufacture=normalize_str(row.get("Material Manufacture")),
                materia_status="Disponible",
                location_name="Dépôt Dolisie"
            )
            try:
                session.add(equip)
                session.commit()
            except IntegrityError:
                session.rollback()
    return True

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="MTN Dolisie Hub", layout="wide")
st.title("📦 Gestion Dépôt Dolisie")

# Charger les données initiales une seule fois
if st.button("Initialiser / Synchroniser avec le fichier DOLISIE"):
    if load_data_into_db("DOLISIE.xlsx - Sheet1.csv"):
        st.success("Données synchronisées !")
    else:
        st.error("Fichier source introuvable.")

menu = ["Inventaire", "📥 Entrée", "📤 Sortie"]
choice = st.sidebar.selectbox("Actions", menu)

with Session(engine) as session:
    if choice == "Inventaire":
        st.subheader("État du Stock Réel")
        items = session.query(Equipement).all()
        if items:
            df_display = pd.DataFrame([vars(i) for i in items]).drop('_sa_instance_state', axis=1)
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("La base de données est vide.")

    elif choice == "📥 Entrée":
        st.subheader("Ajouter un équipement")
        # Formulaire d'ajout ici...
        st.write("Fonctionnalité prête pour saisie manuelle.")

    elif choice == "📤 Sortie":
        st.subheader("Enregistrer un mouvement")
        # Logique de sortie ici...
        st.write("Sélectionnez un S/N pour changement de site.")
