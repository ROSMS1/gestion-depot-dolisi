import os
import sys
import argparse
import logging
from datetime import datetime

import pandas as pd
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime,
    UniqueConstraint, text
)
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.exc import IntegrityError

# ---------------------------------------------------------------------------
# Configuration logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("insert_dolisie.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Modèle ORM (Version moderne)
# ---------------------------------------------------------------------------
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

    __table_args__ = (
        UniqueConstraint("serial_no", name="uq_equipements_serial_no"),
    )

# ---------------------------------------------------------------------------
# Fonctions de nettoyage
# ---------------------------------------------------------------------------
def normalize_str(value) -> str or None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    return s if s not in ("nan", "", "NaN") else None

def load_data_file(filepath: str) -> pd.DataFrame:
    """Charge Excel ou CSV selon l'extension."""
    if not os.path.isfile(filepath):
        log.error(f"Fichier introuvable : {filepath}")
        sys.exit(1)
    
    log.info(f"Lecture du fichier : {filepath}")
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath, dtype=str)
    else:
        df = pd.read_excel(filepath, header=0, dtype=str)
    
    df.columns = [c.strip() for c in df.columns]
    
    rename_map = {
        "Serial No": "serial_no",
        "Materia No": "materia_no",
        "Materia Name": "materia_name",
        "Materia Status": "materia_status",
        "Warehouse No": "warehouse_no",
        "Warehouse Name": "warehouse_name",
        "Location Name": "location_name",
        "Material Belong": "material_belong",
        "Material Type": "material_type",
        "Material Manufacture": "material_manufacture",
        "Quantity": "quantity",
        "Unit": "unit",
        "Domain": "domain",
        "Sub Domain": "sub_domain",
        "Fault Phenomen": "fault_phenomen",
        "OT Number": "ot_number",
    }
    df.rename(columns=rename_map, inplace=True)
    return df

# ... (Le reste des fonctions build_engine et insert_equipements reste similaire mais sans espaces invalides)
