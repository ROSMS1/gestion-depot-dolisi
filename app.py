import os
import pandas as pd
import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base, Session
from sqlalchemy.exc import IntegrityError

# ═══════════════════════════════════════════════════════════════
# CONFIG PAGE
# ═══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Gestion Dépôt Dolisie",
    page_icon="📦",
    layout="wide",
)

# ═══════════════════════════════════════════════════════════════
# BASE DE DONNÉES SQLITE
# ═══════════════════════════════════════════════════════════════
DB_URL = "sqlite:////tmp/depot_dolisie.db"
engine = create_engine(DB_URL, echo=False, connect_args={"check_same_thread": False})
Base   = declarative_base()


class Equipement(Base):
    __tablename__ = "equipements"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    serial_no            = Column(String(100), nullable=False)
    materia_no           = Column(String(100))
    materia_name         = Column(String(255))
    materia_status       = Column(String(50))
    warehouse_no         = Column(String(100))
    warehouse_name       = Column(String(100))
    location_name        = Column(String(100))
    material_belong      = Column(String(50))
    material_type        = Column(String(50))
    material_manufacture = Column(String(100))
    quantity             = Column(Integer)
    unit                 = Column(String(20))
    domain               = Column(String(100))
    sub_domain           = Column(String(100))
    fault_phenomen       = Column(String(255))
    ot_number            = Column(String(100))
    inserted_at          = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("serial_no", name="uq_serial"),)


Base.metadata.create_all(engine)

# ═══════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════
EMPLACEMENTS = [
    "R1_P1_E1","R1_P1_E2","R1_P1_E3","R1_P1_E4",
    "R1_P2_E1","R1_P2_E2","R1_P2_E3","R1_P2_E4",
    "R2_P1_E1","R2_P1_E2","R2_P1_E3","R2_P1_E4","R2_P1_E5",
    "R2_P2_E1","R2_P2_E2","R2_P2_E3","R2_P2_E4","R2_P2_E5",
    "Consumable01","Consumable02","Consumable03","Consumable04","Consumable05",
    "Ground_Spare","Ground_Consumable","0Faulty","Site_Externe",
]
FABRICANTS = ["ZTE","HUAWEI","PERKINS","AVIAT","Autre"]
TYPES      = ["Active","Consumable","Passive"]
STATUTS    = ["available","broken"]

# ═══════════════════════════════════════════════════════════════
# FONCTIONS BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════
def normalize_str(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    return s if s not in ("nan","","NaN") else None


def get_all() -> pd.DataFrame:
    with Session(engine) as s:
        items = s.query(Equipement).order_by(Equipement.id).all()
        if not items:
            return pd.DataFrame()
        return pd.DataFrame([{
            "ID":          i.id,
            "Serial No":   i.serial_no,
            "Materia No":  i.materia_no,
            "Equipement":  i.materia_name,
            "Statut":      i.materia_status,
            "Type":        i.material_type,
            "Fabricant":   i.material_manufacture,
            "Emplacement": i.location_name,
            "Qté":         i.quantity,
            "Unité":       i.unit,
            "Entrepôt":    i.warehouse_name,
            "Panne":       i.fault_phenomen,
            "OT Number":   i.ot_number,
            "Inséré le":   i.inserted_at,
        } for i in items])


def insert_one(data: dict) -> tuple:
    with Session(engine) as s:
        try:
            s.add(Equipement(**data))
            s.commit()
            return True, "OK"
        except IntegrityError:
            s.rollback()
            return False, "doublon"
        except Exception as e:
            s.rollback()
            return False, str(e)


def update_equipement(serial_no: str, location: str, status: str, fault) -> bool:
    with Session(engine) as s:
        eq = s.query(Equipement).filter_by(serial_no=serial_no).first()
        if not eq:
            return False
        eq.location_name  = location
        eq.materia_status = status
        if fault:
            eq.fault_phenomen = fault
        s.commit()
        return True


def delete_one(serial_no: str) -> bool:
    with Session(engine) as s:
        eq = s.query(Equipement).filter_by(serial_no=serial_no).first()
        if not eq:
            return False
        s.delete(eq)
        s.commit()
        return True


def load_from_excel(filepath: str) -> dict:
    if not os.path.exists(filepath):
        return {"ok": False, "msg": f"Fichier introuvable : {filepath}"}
    df = pd.read_excel(filepath, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    inserted = duplicates = errors = 0
    with Session(engine) as s:
        for _, row in df.iterrows():
            sn = normalize_str(row.get("Serial No"))
            if not sn:
                continue
            try:
                qty = int(float(normalize_str(row.get("Quantity")) or 1))
            except Exception:
                qty = 1
            fab = normalize_str(row.get("Material Manufacture"))
            eq = Equipement(
                serial_no            = sn,
                materia_no           = normalize_str(row.get("Materia No")),
                materia_name         = normalize_str(row.get("Materia Name")),
                materia_status       = normalize_str(row.get("Materia Status")) or "available",
                warehouse_no         = normalize_str(row.get("Warehouse No")),
                warehouse_name       = normalize_str(row.get("Warehouse Name")),
                location_name        = normalize_str(row.get("Location Name")),
                material_belong      = normalize_str(row.get("Material Belong")),
                material_type        = normalize_str(row.get("Material Type")),
                material_manufacture = fab.strip().upper() if fab else None,
                quantity             = qty,
                unit                 = normalize_str(row.get("Unit")),
                domain               = normalize_str(row.get("Domain")),
                sub_domain           = normalize_str(row.get("Sub Domain")),
                fault_phenomen       = normalize_str(row.get("Fault Phenomen")),
                ot_number            = normalize_str(row.get("OT Number")),
            )
            try:
                s.add(eq)
                s.flush()
                inserted += 1
            except IntegrityError:
                s.rollback()
                duplicates += 1
            except Exception:
                s.rollback()
                errors += 1
        s.commit()
    return {"ok":True,"inserted":inserted,"duplicates":duplicates,"errors":errors,"total":len(df)}


# ═══════════════════════════════════════════════════════════════
# CHARGEMENT AUTO AU DÉMARRAGE (si DOLISIE.xlsx présent dans le repo)
# ═══════════════════════════════════════════════════════════════
if "initialized" not in st.session_state:
    if os.path.exists("DOLISIE.xlsx"):
        load_from_excel("DOLISIE.xlsx")
    st.session_state.initialized = True


# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════
st.sidebar.title("📦 Dépôt Dolisie")
st.sidebar.caption("MTN Congo · DIGIR02Dolisie")

menu = st.sidebar.radio("Navigation", [
    "📊 Inventaire",
    "🗺️ Emplacements",
    "📥 Entrée équipement",
    "📤 Sortie / Mouvement",
    "📋 Audit",
    "🔄 Importer Excel",
])

# KPIs dans la sidebar
df = get_all()
total     = len(df)
available = len(df[df["Statut"] == "available"]) if total else 0
broken    = len(df[df["Statut"] == "broken"])    if total else 0

st.sidebar.divider()
st.sidebar.metric("Total",          total)
st.sidebar.metric("✅ Disponibles", available)
st.sidebar.metric("❌ En panne",    broken)


# ═══════════════════════════════════════════════════════════════
# PAGE : INVENTAIRE
# ═══════════════════════════════════════════════════════════════
if menu == "📊 Inventaire":
    st.title("📊 Inventaire du dépôt")

    if df.empty:
        st.warning("⚠️ Base vide. Allez dans **🔄 Importer Excel** pour charger DOLISIE.xlsx.")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        f_type = st.selectbox("Type", ["Tous"] + sorted(df["Type"].dropna().unique().tolist()))
    with c2:
        f_fab  = st.selectbox("Fabricant", ["Tous"] + sorted(df["Fabricant"].dropna().unique().tolist()))
    with c3:
        f_stat = st.selectbox("Statut", ["Tous","available","broken"])
    with c4:
        f_loc  = st.selectbox("Emplacement", ["Tous"] + sorted(df["Emplacement"].dropna().unique().tolist()))

    df_f = df.copy()
    if f_type != "Tous": df_f = df_f[df_f["Type"]        == f_type]
    if f_fab  != "Tous": df_f = df_f[df_f["Fabricant"]   == f_fab]
    if f_stat != "Tous": df_f = df_f[df_f["Statut"]      == f_stat]
    if f_loc  != "Tous": df_f = df_f[df_f["Emplacement"] == f_loc]

    search = st.text_input("🔍 Rechercher par S/N, nom ou N° OT")
    if search:
        mask = (
            df_f["Serial No"].str.contains(search, case=False, na=False) |
            df_f["Equipement"].str.contains(search, case=False, na=False) |
            df_f["OT Number"].str.contains(search, case=False, na=False)
        )
        df_f = df_f[mask]

    st.caption(f"**{len(df_f)}** équipements affichés sur {total}")
    st.dataframe(df_f, use_container_width=True, hide_index=True)

    csv = df_f.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Exporter en CSV", csv, "inventaire_dolisie.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════
# PAGE : EMPLACEMENTS
# ═══════════════════════════════════════════════════════════════
elif menu == "🗺️ Emplacements":
    st.title("🗺️ Vue Emplacements – Magasin")

    if df.empty:
        st.warning("Base vide. Importez d'abord le fichier Excel.")
        st.stop()

    loc_map = df.groupby("Emplacement").size().to_dict()

    # ── RACKS ────────────────────────────────────────────────
    st.subheader("🗄️ Racks")
    for rangee in ["R1", "R2"]:
        st.markdown(f"**Rangée {rangee}**")
        locs = [l for l in EMPLACEMENTS if l.startswith(rangee)]
        cols = st.columns(len(locs))
        for col, loc in zip(cols, locs):
            nb    = loc_map.get(loc, 0)
            icone = "🟢" if nb > 0 else "⬜"
            col.metric(f"{icone} {loc}", nb)

    st.divider()

    # ── CONSOMMABLES ─────────────────────────────────────────
    st.subheader("📦 Zones Consommables")
    cons = [l for l in EMPLACEMENTS if "Consumable" in l or "Ground" in l]
    cols = st.columns(len(cons))
    for col, loc in zip(cols, cons):
        col.metric(f"🟡 {loc}", loc_map.get(loc, 0))

    st.divider()

    # ── ZONE PANNE ───────────────────────────────────────────
    st.subheader("🔴 Zone Panne (0Faulty)")
    nb_f = loc_map.get("0Faulty", 0)
    if nb_f > 0:
        st.error(f"**{nb_f} équipement(s) en panne**")
        df_f = df[df["Emplacement"] == "0Faulty"][["Serial No","Equipement","Fabricant","Panne","OT Number"]]
        st.dataframe(df_f, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Aucun équipement en zone panne.")

    st.divider()

    # ── DÉTAIL PAR EMPLACEMENT ───────────────────────────────
    st.subheader("🔎 Détail par emplacement")
    loc_sel = st.selectbox("Choisir un emplacement", ["—"] + sorted(df["Emplacement"].dropna().unique().tolist()))
    if loc_sel != "—":
        df_loc = df[df["Emplacement"] == loc_sel]
        st.caption(f"{len(df_loc)} équipement(s) à **{loc_sel}**")
        st.dataframe(
            df_loc[["Serial No","Equipement","Type","Fabricant","Statut","Qté","Unité","Panne"]],
            use_container_width=True, hide_index=True
        )


# ═══════════════════════════════════════════════════════════════
# PAGE : ENTRÉE
# ═══════════════════════════════════════════════════════════════
elif menu == "📥 Entrée équipement":
    st.title("📥 Entrée d'un équipement")

    with st.form("form_entree", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            serial_no    = st.text_input("Numéro de Série (S/N) *", placeholder="Ex: 052621000244")
            materia_no   = st.text_input("Materia No",              placeholder="Ex: RRU-B3-ZTE")
            materia_name = st.text_input("Désignation *",           placeholder="Ex: RRU 3.2 Band 3")
            mat_type     = st.selectbox("Type",       TYPES)
            fabricant    = st.selectbox("Fabricant",  FABRICANTS)
        with c2:
            location  = st.selectbox("Emplacement",  EMPLACEMENTS)
            statut    = st.selectbox("Statut",        STATUTS)
            qty       = st.number_input("Quantité", min_value=1, value=1)
            unit      = st.selectbox("Unité",         ["PCS","ROLL","SET","UNIT"])
            ot_number = st.text_input("N° OT",        placeholder="Ex: ZTE202301100001")
            fault     = st.text_input("Phénomène panne (si applicable)")

        submitted = st.form_submit_button("✅ Enregistrer l'entrée", use_container_width=True)

    if submitted:
        if not serial_no.strip() or not materia_name.strip():
            st.error("❌ S/N et Désignation sont obligatoires.")
        else:
            ok, msg = insert_one({
                "serial_no":            serial_no.strip(),
                "materia_no":           materia_no.strip() or None,
                "materia_name":         materia_name.strip(),
                "materia_status":       statut,
                "warehouse_no":         "DIGIR02Dolisie",
                "warehouse_name":       "DOP_DIGI_Dolisie",
                "location_name":        location,
                "material_belong":      "MTN",
                "material_type":        mat_type,
                "material_manufacture": fabricant,
                "quantity":             qty,
                "unit":                 unit,
                "ot_number":            ot_number.strip() or None,
                "fault_phenomen":       fault.strip() or None,
            })
            if ok:
                st.success(f"✅ **{serial_no}** ajouté à **{location}** !")
                st.rerun()
            elif msg == "doublon":
                st.error(f"⚠️ S/N **{serial_no}** déjà existant en base.")
            else:
                st.error(f"❌ Erreur : {msg}")


# ═══════════════════════════════════════════════════════════════
# PAGE : SORTIE / MOUVEMENT
# ═══════════════════════════════════════════════════════════════
elif menu == "📤 Sortie / Mouvement":
    st.title("📤 Sortie / Mouvement d'équipement")

    if df.empty:
        st.warning("Base vide. Importez d'abord le fichier Excel.")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["📤 Sortie vers site", "🔄 Déplacement interne", "🗑️ Supprimer"])

    with tab1:
        st.subheader("Envoyer un équipement sur site")
        dispos = df[df["Statut"] == "available"]["Serial No"].tolist()
        if not dispos:
            st.info("Aucun équipement disponible.")
        else:
            sn   = st.selectbox("S/N à sortir", dispos)
            row  = df[df["Serial No"] == sn].iloc[0]
            st.info(f"**{row['Equipement']}** · {row['Fabricant']} · Emplacement : `{row['Emplacement']}`")
            dest = st.text_input("Site de destination *", placeholder="Ex: Site_Kimba")
            tech = st.text_input("Technicien responsable")
            if st.button("✅ Confirmer la sortie", use_container_width=True):
                if not dest.strip():
                    st.error("Destination obligatoire.")
                else:
                    update_equipement(sn, dest.strip(), "available", None)
                    st.success(f"✅ **{sn}** envoyé vers **{dest}**" + (f" par {tech}" if tech else ""))
                    st.rerun()

    with tab2:
        st.subheader("Déplacer un équipement dans le dépôt")
        sn2  = st.selectbox("S/N à déplacer", df["Serial No"].tolist())
        row2 = df[df["Serial No"] == sn2].iloc[0]
        st.info(f"**{row2['Equipement']}** · Emplacement actuel : `{row2['Emplacement']}` · Statut : `{row2['Statut']}`")
        c1, c2   = st.columns(2)
        new_loc  = c1.selectbox("Nouvel emplacement", EMPLACEMENTS)
        new_stat = c2.selectbox("Nouveau statut",     STATUTS)
        new_fault= st.text_input("Phénomène panne (si applicable)")
        if st.button("✅ Enregistrer le déplacement", use_container_width=True):
            update_equipement(sn2, new_loc, new_stat, new_fault or None)
            st.success(f"✅ **{sn2}** → `{new_loc}` · statut `{new_stat}`")
            st.rerun()

    with tab3:
        st.subheader("Supprimer un équipement")
        st.warning("⚠️ Action irréversible.")
        sn3  = st.selectbox("S/N à supprimer", df["Serial No"].tolist())
        row3 = df[df["Serial No"] == sn3].iloc[0]
        st.error(f"Suppression de : **{row3['Equipement']}** (S/N: {sn3})")
        if st.checkbox("Je confirme la suppression"):
            if st.button("🗑️ Supprimer définitivement", use_container_width=True):
                delete_one(sn3)
                st.success(f"✅ {sn3} supprimé.")
                st.rerun()


# ═══════════════════════════════════════════════════════════════
# PAGE : AUDIT
# ═══════════════════════════════════════════════════════════════
elif menu == "📋 Audit":
    st.title("📋 Rapport d'Audit – DOP_DIGI_Dolisie")
    st.caption(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")

    if df.empty:
        st.warning("Base vide.")
        st.stop()

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total équipements",     total)
    c2.metric("✅ Disponibles",        available)
    c3.metric("❌ En panne",           broken)
    taux = round((available / total) * 100, 1) if total else 0
    c4.metric("📈 Taux disponibilité", f"{taux} %")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 Par type")
        st.dataframe(
            df.groupby("Type").size().reset_index(name="Quantité").sort_values("Quantité", ascending=False),
            use_container_width=True, hide_index=True
        )
    with col2:
        st.subheader("🏭 Par fabricant")
        st.dataframe(
            df.groupby("Fabricant").size().reset_index(name="Quantité").sort_values("Quantité", ascending=False),
            use_container_width=True, hide_index=True
        )

    st.divider()
    st.subheader("📍 Répartition par emplacement")
    st.dataframe(
        df.groupby("Emplacement").size().reset_index(name="Nb").sort_values("Nb", ascending=False),
        use_container_width=True, hide_index=True
    )

    st.divider()
    st.subheader("🔴 Équipements en panne")
    df_broken = df[df["Statut"] == "broken"][["Serial No","Equipement","Fabricant","Emplacement","Panne","OT Number"]]
    if df_broken.empty:
        st.success("✅ Aucun équipement en panne.")
    else:
        st.dataframe(df_broken, use_container_width=True, hide_index=True)

    st.divider()
    csv_audit = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Télécharger le rapport complet (CSV)", csv_audit, "audit_dolisie.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════
# PAGE : IMPORTER EXCEL
# ═══════════════════════════════════════════════════════════════
elif menu == "🔄 Importer Excel":
    st.title("🔄 Importer / Synchroniser DOLISIE.xlsx")

    st.subheader("Option 1 — Fichier dans le repo GitHub")
    st.info("Placez `DOLISIE.xlsx` à la racine de votre repo puis cliquez.")
    if st.button("🔄 Synchroniser depuis le repo", use_container_width=True):
        r = load_from_excel("DOLISIE.xlsx")
        if r["ok"]:
            st.success(f"✅ {r['inserted']} insérés · {r['duplicates']} doublons · {r['errors']} erreurs · {r['total']} lignes")
            st.rerun()
        else:
            st.error(r["msg"])

    st.divider()

    st.subheader("Option 2 — Uploader manuellement")
    uploaded = st.file_uploader("Choisir un fichier .xlsx", type=["xlsx"])
    if uploaded:
        tmp = f"/tmp/{uploaded.name}"
        with open(tmp, "wb") as f:
            f.write(uploaded.getbuffer())
        r = load_from_excel(tmp)
        if r["ok"]:
            st.success(f"✅ {r['inserted']} insérés · {r['duplicates']} doublons · {r['errors']} erreurs")
            st.rerun()
        else:
            st.error(r["msg"])

    st.divider()

    st.subheader("⚠️ Réinitialiser la base de données")
    st.warning("Ceci supprimera **tous** les équipements.")
    if st.checkbox("Je confirme la réinitialisation complète"):
        if st.button("🗑️ Vider la base", use_container_width=True):
            with Session(engine) as s:
                s.query(Equipement).delete()
                s.commit()
            st.success("✅ Base vidée. Importez à nouveau le fichier Excel.")
            st.rerun()
