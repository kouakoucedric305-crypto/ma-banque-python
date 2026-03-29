import streamlit as st
import pandas as pd
from datetime import datetime
import random # Pour générer des numéros de compte fictifs

# --- CONFIGURATION ET STYLE (DESIGN AMÉLIORÉ) ---
st.set_page_config(page_title="Cedric Bank Pro", page_icon="💳", layout="wide")

# Injection CSS (Style sombre, cloche, photo)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stMetricValue"] { color: #00FFA3 !important; font-size: 30px; }
    div.stButton > button:first-child {
        background-color: #6200EA; color: white; border-radius: 8px; border: none;
        transition: 0.3s; width: 100%;
    }
    div.stButton > button:first-child:hover { background-color: #00FFA3; color: black; }
    .stSidebar { background-color: #161B22; }
    /* Style de la cloche */
    .notification-bell {
        font-size: 24px; position: absolute; top: 10px; right: 30px; cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

BANQUE_NOM = "Banque Cedric"
# Photo de profil par défaut (silhouete)
DEFAULT_AVATAR = "https://www.w3schools.com/howto/img_avatar.png"

# --- INITIALISATION DE L'ÉTAT (BDD + SESSION) ---
# 1. Base de données simulée (persistent entre les runs)
if "db_comptes" not in st.session_state:
    st.session_state.db_comptes = {
        "cedric": {"password": "abcd", "avatar": DEFAULT_AVATAR},
        "alice": {"password": "1234", "avatar": DEFAULT_AVATAR}
    }
if "db_soldes" not in st.session_state:
    st.session_state.db_soldes = {
        "cedric": {"Courant": 500.0, "Épargne": 1000.0},
        "alice": {"Courant": 300.0, "Épargne": 5000.0}
    }
if "db_transactions" not in st.session_state:
    st.session_state.db_transactions = {
        "cedric": {"Courant": [], "Épargne": []},
        "alice": {"Courant": [], "Épargne": []}
    }

# 2. État de la session actuelle
if "session" not in st.session_state:
    st.session_state.session = {
        "connecte": False, "utilisateur": None, "notifications": []
    }

# --- FONCTIONS ---
def salutation(nom):
    heure = datetime.now().hour
    if heure < 12: return f"🌞 Bonjour {nom.capitalize()}"
    elif heure < 18: return f"🌤️ Bon après-midi {nom.capitalize()}"
    else: return f"🌙 Bonsoir {nom.capitalize()}"

def deconnexion():
    st.session_state.session["connecte"] = False
    st.session_state.session["utilisateur"] = None
    st.session_state.session["notifications"] = []
    st.rerun()

def ajouter_notification(msg):
    st.session_state.session["notifications"].append({
        "time": datetime.now().strftime("%H:%M"), "message": msg
    })

# --- INTERFACE ---

# --- PAGE DE CONNEXION / CRÉATION ---
if not st.session_state.session["connecte"]:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🏦 Banque Cedric</h1>", unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔐 Connexion", "📝 Créer un compte"])
        
        # Onglet 1 : Connexion
        with tab_login:
            st.subheader("Accédez à votre espace")
            login_user = st.text_input("Identifiant", key="l_user").lower()
            login_pw = st.text_input("Mot de passe", type="password", key="l_pw")
            if st.button("Se connecter", key="btn_login"):
                if login_user in st.session_state.db_comptes and st.session_state.db_comptes[login_user]["password"] == login_pw:
                    st.session_state.session["connecte"] = True
                    st.session_state.session["utilisateur"] = login_user
                    st.rerun()
                else:
                    st.error("Identifiants incorrects ❌")
        
        # Onglet 2 : Création
        with tab_register:
            st.subheader("Rejoignez Banque Cedric")
            reg_user = st.text_input("Choisissez un identifiant", key="r_user").lower()
            reg_pw = st.text_input("Définissez un mot de passe", type="password", key="r_pw")
            reg_pw2 = st.text_input("Confirmez le mot de passe", type="password", key="r_pw2")
            reg_avatar = st.text_input("URL de votre photo de profil (optionnel)", DEFAULT_AVATAR, key="r_av")
            
            if st.button("Créer mon compte", key="btn_reg"):
                if reg_user == "" or reg_pw == "":
                    st.warning("Veuillez remplir tous les champs.")
                elif reg_pw != reg_pw2:
                    st.error("Les mots de passe ne correspondent pas.")
                elif reg_user in st.session_state.db_comptes:
                    st.error("Cet identifiant est déjà utilisé.")
                else:
                    # Création réussie
                    num_compte = random.randint(100000, 999999)
                    st.session_state.db_comptes[reg_user] = {"password": reg_pw, "avatar": reg_avatar}
                    st.session_state.db_soldes[reg_user] = {"Courant": 50.0, "Épargne": 0.0} # Bonus de bienvenue
                    st.session_state.db_transactions[reg_user] = {"Courant": [], "Épargne": []}
                    st.session_state.db_transactions[reg_user]["Courant"].append({"Date": datetime.now().strftime("%d/%m"), "Type": "Bonus", "Montant": 50.0, "Solde après": 50.0})
                    st.success(f"Compte créé avec succès ! Numéro de compte : **{num_compte}** 🎉")
                    st.info("Vous pouvez maintenant vous connecter.")
                    st.rerun()

# --- ESPACE CLIENT ---
else:
    user = st.session_state.session["utilisateur"]
    notifications = st.session_state.session["notifications"]
    
    # 1. Barre latérale (avec photo)
    with st.sidebar:
        user_data = st.session_state.db_comptes[user]
        st.image(user_data["avatar"], width=80)
        st.write(f"### {user.capitalize()}")
        menu = st.radio("Menu", ["🏠 Tableau de bord", "💸 Virement", "📊 Historique"])
        st.divider()
        if st.button("Se déconnecter"):
            deconnexion()

    # 2. En-tête (Salutation + Cloche)
    col_salut, col_notif = st.columns([4, 1])
    with col_salut:
        st.write(f"### {salutation(user)}")
    with col_notif:
        # Cloche de notification (unicode)
        label_cloche = f"🔔 ({len(notifications)})" if notifications else "🔔"
        with st.popover(label_cloche):
            st.write("#### Vos Notifications")
            if not notifications:
                st.write("Aucune notification pour le moment.")
            else:
                for n in reversed(notifications):
                    st.write(f"**[{n['time']}]** - {n['message']}")

    # --- CONTENU DES PAGES ---
    soldes = st.session_state.db_soldes[user]
    transactions = st.session_state.db_transactions[user]

    # --- PAGE 1 : DASHBOARD ---
    if menu == "🏠 Tableau de bord":
        st.title("💼 Vos Comptes")
        c1, c2 = st.columns(2)
        c1.metric("Compte Courant", f"{soldes['Courant']:,.2f} €")
        c2.metric("Compte Épargne", f"{soldes['Épargne']:,.2f} €")

        st.divider()

        # Opérations
        col_op, col_side = st.columns([2, 1])
        with col_op:
            st.subheader("⚡ Opération rapide")
            with st.container(border=True):
                compte_choisi = st.selectbox("Sélectionnez le compte :", ["Courant", "Épargne"])
                choix = st.segmented_control("📌 Action :", ["Déposer", "Retirer"])
                montant = st.number_input("Montant (€) :", min_value=1.0, step=10.0)

                if st.button("Valider l'opération"):
                    if non_montant := (montant <= 0):
                        st.warning("Montant invalide.")
                    elif not choix:
                        st.warning("Sélectionnez une action.")
                    else:
                        solde_actuel = soldes[compte_choisi]
                        if choix == "Retirer" and montant > solde_actuel:
                            st.error("❌ Solde insuffisant !")
                            ajouter_notification(f"Tentative de retrait de {montant}€ refusée sur {compte_choisi}.")
                        else:
                            # Mise à jour
                            val = montant if choix == "Déposer" else -montant
                            soldes[compte_choisi] += val
                            transactions[compte_choisi].append({
                                "Date": datetime.now().strftime("%d/%m"),
                                "Type": choix, "Montant": montant, "Solde après": soldes[compte_choisi]
                            })
                            # Notif
                            emoji = "✅" if choix == "Déposer" else "💸"
                            msg_notif = f"{choix} de {montant}€ effectué sur {compte_choisi}."
                            st.toast(f"{emoji} {msg_notif}")
                            ajouter_notification(msg_notif)
                            st.rerun()

    # --- PAGE 2 : VIREMENT ---
    elif menu == "💸 Virement":
        st.title("💸 Virement interne")
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1: source = st.selectbox("De :", ["Courant", "Épargne"])
            with col2: 
                dest = "Épargne" if source == "Courant" else "Courant"
                st.info(f"Vers : **{dest}**")
            
            m_vir = st.number_input("Montant à transférer (€)", min_value=1.0)
            if st.button("🚀 Confirmer le virement"):
                if soldes[source] >= m_vir:
                    soldes[source] -= m_vir
                    soldes[dest] += m_vir
                    # Log
                    transactions[source].append({"Date": "Virement", "Type": f"Vers {dest}", "Montant": m_vir, "Solde après": soldes[source]})
                    transactions[dest].append({"Date": "Virement", "Type": f"Depuis {source}", "Montant": m_vir, "Solde après": soldes[dest]})
                    # Notif
                    ajouter_notification(f"Transfert de {m_vir}€ de {source} vers {dest} réussi.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Fonds insuffisants.")

    # --- PAGE 3 : HISTORIQUE ---
    elif menu == "📊 Historique":
        st.title("📜 Historique détaillé")
        tab1, tab2 = st.tabs(["Compte Courant", "Compte Épargne"])
        with tab1:
            if transactions["Courant"]:
                st.dataframe(pd.DataFrame(transactions["Courant"]), use_container_width=True)
            else: st.info("Aucune transaction.")
        with tab2:
            if transactions["Épargne"]:
                st.dataframe(pd.DataFrame(transactions["Épargne"]), use_container_width=True)
            else: st.info("Aucune transaction.")