import streamlit as st
import sqlite3
import bcrypt
import random
import pandas as pd
import time
import io
from datetime import datetime, date
from cryptography.fernet import Fernet
from PIL import Image

# --- 1. CONFIGURATION & SÉCURITÉ ---
st.set_page_config(page_title="Elite Bank Pro", page_icon="🏢", layout="wide")

if "cipher_key" not in st.session_state:
    st.session_state.cipher_key = Fernet.generate_key()
cipher_suite = Fernet(st.session_state.cipher_key)

def encrypt_data(data: str) -> str:
    return cipher_suite.encrypt(str(data).encode()).decode()

def decrypt_data(token: str) -> str:
    try: return cipher_suite.decrypt(token.encode()).decode()
    except: return "Donnée protégée"

# --- 2. STYLE AVANCÉ ---
st.markdown("""
<style>
    .stApp { background: radial-gradient(circle at top right, #1e293b, #0f172a); color: #f8fafc; }
    .bank-card { background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px; margin-bottom: 20px; }
    
    .virtual-card { 
        width: 400px; height: 250px; 
        background: linear-gradient(135deg, #0f172a 0%, #334155 100%); 
        border-radius: 20px; padding: 25px; color: white; 
        border: 1px solid rgba(255, 255, 255, 0.2); 
        box-shadow: 0 20px 40px rgba(0,0,0,0.6);
        position: relative; overflow: hidden;
    }
    .card-logo { position: absolute; top: 20px; right: 25px; font-weight: 800; font-size: 18px; letter-spacing: 1px; }
    .card-chip { width: 50px; height: 38px; background: linear-gradient(135deg, #ffd700, #b8860b); border-radius: 8px; margin-top: 30px; margin-bottom: 15px; }
    .card-number { font-family: 'Courier New', monospace; font-size: 20px; letter-spacing: 2px; margin-bottom: 10px; text-shadow: 1px 1px 2px black; }
    .card-iban { font-family: 'Courier New', monospace; font-size: 11px; opacity: 0.9; margin-bottom: 15px; }
    .card-details { display: flex; justify-content: space-between; align-items: flex-end; }
    .card-label { font-size: 8px; text-transform: uppercase; opacity: 0.7; margin-bottom: 2px; }
    .card-val { font-size: 13px; text-transform: uppercase; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# --- 3. BASE DE DONNÉES ---
DB_NAME = "banque_master_v1.db"
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users 
            (username TEXT PRIMARY KEY, password BLOB, phone TEXT, iban TEXT, bic TEXT, 
             nom TEXT, prenom TEXT, date_naiss TEXT, solde_courant REAL, solde_epargne REAL, 
             status TEXT DEFAULT 'Actif', gel_avoirs INTEGER DEFAULT 0, photo_profil BLOB, piece_id BLOB)''')
        c.execute('''CREATE TABLE IF NOT EXISTS transactions 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, type TEXT, montant REAL, 
             detail TEXT, date TEXT, statut TEXT, iban_dest TEXT, compte_cible TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS notifications 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, message TEXT, date TEXT, lu INTEGER DEFAULT 0)''')
init_db()

def add_notif(username, message):
    with sqlite3.connect(DB_NAME) as conn:
        conn.cursor().execute("INSERT INTO notifications (username, message, date) VALUES (?,?,?)",
                            (username, message, datetime.now().strftime("%d/%m/%Y %H:%M")))

# --- 4. LOGIQUE AUTH ---
if "user" not in st.session_state: st.session_state.user = None
if "reg_step" not in st.session_state: st.session_state.reg_step = 1
if "forgot_mode" not in st.session_state: st.session_state.forgot_mode = False

if not st.session_state.user:
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("<h1 style='text-align:center;'>🏢 ELITE BANK PRO</h1>", unsafe_allow_html=True)
        
        if not st.session_state.forgot_mode:
            t_login, t_reg = st.tabs(["🔒 Connexion Client", "📝 Ouvrir un compte"])
            
            with t_login:
                u_in = st.text_input("Identifiant", key="l_u").lower().strip()
                p_in = st.text_input("Mot de passe", type="password", key="l_p")
                if st.button("Connexion Sécurisée", type="primary", use_container_width=True):
                    if u_in == "admin" and p_in == "admin123":
                        st.session_state.user = "admin"; st.rerun()
                    with sqlite3.connect(DB_NAME) as conn:
                        res = conn.cursor().execute("SELECT password, status FROM users WHERE username=?", (u_in,)).fetchone()
                        if res:
                            if res[1] == "Bloqué": st.error("Accès refusé par le service de sécurité.")
                            elif bcrypt.checkpw(p_in.encode(), res[0]):
                                st.session_state.user = u_in; st.rerun()
                            else: st.error("Identifiants invalides.")
                        else: st.error("Compte introuvable.")
                
                if st.button("Mot de passe oublié ?"):
                    st.session_state.forgot_mode = True
                    st.rerun()

            with t_reg:
                if st.session_state.reg_step == 1:
                    new_u = st.text_input("Pseudo", key="r_u")
                    n = st.text_input("Nom de famille", key="r_n"); p = st.text_input("Prénom", key="r_p")
                    d_n = st.date_input("Date de naissance", value=date(1995, 1, 1))
                    tel = st.text_input("Mobile", key="r_t")
                    pwd = st.text_input("Mot de passe", type="password", key="r_pwd")
                    if st.button("Étape suivante"):
                        st.session_state.tmp = {"u":new_u,"p":pwd,"n":n,"pr":p,"dn":str(d_n), "tel":tel}
                        st.session_state.otp = random.randint(1111, 9999)
                        st.session_state.reg_step = 2; st.rerun()
                elif st.session_state.reg_step == 2:
                    st.info(f"Code de vérification envoyé : **{st.session_state.otp}**")
                    c_otp = st.text_input("Entrez le code reçu", key="r_otp")
                    if st.button("Finaliser mon dossier"):
                        if c_otp == str(st.session_state.otp):
                            d = st.session_state.tmp
                            with sqlite3.connect(DB_NAME) as conn:
                                iban_gen = f"FR76 3000 {random.randint(1000,9999)} {random.randint(1000,9999)} 42"
                                conn.cursor().execute("INSERT INTO users (username, password, phone, nom, prenom, date_naiss, solde_courant, solde_epargne, iban, bic) VALUES (?,?,?,?,?,?,?,?,?,?)",
                                    (d['u'], bcrypt.hashpw(d['p'].encode(), bcrypt.gensalt()), d['tel'], encrypt_data(d['n']), encrypt_data(d['pr']), encrypt_data(d['dn']), 500.0, 50.0, encrypt_data(iban_gen), encrypt_data("BANQPR75")))
                            st.success("Compte créé avec succès ! Connectez-vous."); st.session_state.reg_step = 1
        
        else:
            st.subheader("🔑 Récupération de compte")
            f_user = st.text_input("Nom d'utilisateur")
            f_phone = st.text_input("Numéro de téléphone associé")
            new_p = st.text_input("Nouveau mot de passe", type="password")
            
            c1, c2 = st.columns(2)
            if c1.button("Réinitialiser", type="primary"):
                with sqlite3.connect(DB_NAME) as conn:
                    res = conn.cursor().execute("SELECT phone FROM users WHERE username=?", (f_user.lower().strip(),)).fetchone()
                    if res and res[0] == f_phone:
                        new_h = bcrypt.hashpw(new_p.encode(), bcrypt.gensalt())
                        conn.cursor().execute("UPDATE users SET password=? WHERE username=?", (new_h, f_user.lower().strip()))
                        st.success("Mot de passe modifié ! Connectez-vous.")
                        time.sleep(2)
                        st.session_state.forgot_mode = False
                        st.rerun()
                    else: st.error("Les informations ne correspondent pas.")
            
            if c2.button("Retour"):
                st.session_state.forgot_mode = False
                st.rerun()

# --- 5. ESPACE CLIENT ---
elif st.session_state.user != "admin":
    u = st.session_state.user
    with sqlite3.connect(DB_NAME) as conn:
        data = pd.read_sql_query("SELECT * FROM users WHERE username=?", conn, params=(u,)).iloc[0]
        n_count = conn.cursor().execute("SELECT COUNT(*) FROM notifications WHERE username=? AND lu=0", (u,)).fetchone()[0]

    st.sidebar.title("💎 ELITE BANK")
    menu = st.sidebar.radio("Navigation", ["Tableau de Bord", "Opérations", "Mon Profil", "RIB", "Historique"])
    if st.sidebar.button("Déconnexion"): st.session_state.user = None; st.rerun()

    h_col1, h_col2 = st.columns([5, 1])
    heure_actuelle = datetime.now().hour
    salut = "Bonjour" if heure_actuelle < 18 else "Bonsoir"
    h_col1.title(f"{salut}, {decrypt_data(data['prenom'])} 👋")
    
    with h_col2:
        if st.button(f"🔔 Notifs ({n_count})"):
            with sqlite3.connect(DB_NAME) as conn:
                notifs = pd.read_sql_query("SELECT message, date FROM notifications WHERE username=? ORDER BY id DESC", conn, params=(u,))
                conn.cursor().execute("UPDATE notifications SET lu=1 WHERE username=?", (u,)).connection.commit()
                for _, n in notifs.iterrows(): st.toast(f"{n['message']}")

    if data['gel_avoirs']: st.error("🚫 AVOIRS GELÉS : Vos comptes sont temporairement bloqués par les autorités bancaires.")

    if menu == "Tableau de Bord":
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='bank-card'>SOLDE COURANT<br><h2 style='color:#10b981;'>{data['solde_courant']:,.2f} €</h2></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='bank-card'>SOLDE ÉPARGNE<br><h2 style='color:#3b82f6;'>{data['solde_epargne']:,.2f} €</h2></div>", unsafe_allow_html=True)
        
        st.subheader("💳 Carte Virtuelle Active")
        nom_complet = f"{decrypt_data(data['prenom'])} {decrypt_data(data['nom'])}".upper()
        user_iban = decrypt_data(data['iban'])
        
        st.markdown(f"""
        <div class="virtual-card">
            <div class="card-logo">ELITE BANK</div>
            <div class="card-chip"></div>
            <div class="card-number">4532 1029 8834 {random.randint(1000,9999)}</div>
            <div class="card-iban">{user_iban}</div>
            <div class="card-details">
                <div><div class="card-label">Titulaire</div><div class="card-val">{nom_complet}</div></div>
                <div><div class="card-label">Expire fin</div><div class="card-val">12/28</div></div>
                <div><div class="card-label">CVV</div><div class="card-val">{random.randint(100,999)}</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif menu == "Opérations":
        t1, t2 = st.tabs(["Dépôt / Retrait", "Virement"])
        with t1:
            ca, cb = st.columns(2)
            op = ca.selectbox("Mouvement", ["Dépôt", "Retrait"])
            cpte = cb.selectbox("Sur le compte", ["Courant", "Épargne"])
            mnt = st.number_input("Somme (€)", min_value=1.0)
            if st.button("Confirmer l'opération", disabled=data['gel_avoirs']):
                col_sql = "solde_courant" if cpte == "Courant" else "solde_epargne"
                val = mnt if op == "Dépôt" else -mnt
                if (data[col_sql] + val) < 0: st.error("Fonds insuffisants.")
                else:
                    with sqlite3.connect(DB_NAME) as conn:
                        conn.cursor().execute(f"UPDATE users SET {col_sql} = {col_sql} + ? WHERE username=?", (val, u))
                        conn.cursor().execute("INSERT INTO transactions (username, type, montant, detail, date, statut, compte_cible) VALUES (?,?,?,?,?,?,?)", 
                                            (u, op, mnt, f"{op} guichet", datetime.now().strftime("%d/%m/%Y"), "Validé", cpte))
                    add_notif(u, f"Opération {op} de {mnt}€ effectuée.")
                    st.rerun()

        with t2:
            st.info("Effectuez un virement sécurisé en saisissant l'IBAN du bénéficiaire.")
            ib_d = st.text_input("IBAN du bénéficiaire (Ex: FR76...)")
            mnt_s = st.number_input("Montant (€)", min_value=1.0, key="vsepa")
            
            if st.button("Envoyer le virement", disabled=data['gel_avoirs']):
                if data['solde_courant'] < mnt_s: 
                    st.error("Solde courant insuffisant.")
                elif ib_d == decrypt_data(data['iban']):
                    st.error("Action impossible : vous ne pouvez pas vous envoyer de fonds à vous-même.")
                elif ib_d == "":
                    st.warning("Veuillez saisir un IBAN valide.")
                else:
                    stat = "En attente" if mnt_s > 1000 else "Validé"
                    with sqlite3.connect(DB_NAME) as conn:
                        # On vérifie si l'IBAN appartient à un client de la banque (virement interne)
                        internal_dest = None
                        all_users_db = conn.cursor().execute("SELECT username, iban FROM users").fetchall()
                        for row in all_users_db:
                            if decrypt_data(row[1]) == ib_d:
                                internal_dest = row[0]
                                break
                        
                        if stat == "Validé":
                            conn.cursor().execute("UPDATE users SET solde_courant = solde_courant - ? WHERE username=?", (mnt_s, u))
                            add_notif(u, f"Virement de {mnt_s}€ vers {ib_d} validé.")
                            
                            if internal_dest: # Si le client est trouvé chez nous
                                conn.cursor().execute("UPDATE users SET solde_courant = solde_courant + ? WHERE username=?", (mnt_s, internal_dest))
                                add_notif(internal_dest, f"Virement reçu : +{mnt_s}€ de {u}")
                                conn.cursor().execute("INSERT INTO transactions (username, type, montant, detail, date, statut) VALUES (?,?,?,?,?,?)", 
                                                    (internal_dest, "Virement Reçu", mnt_s, f"De {u}", datetime.now().strftime("%d/%m/%Y"), "Validé"))
                        else:
                            add_notif(u, f"Virement de {mnt_s}€ en attente de vérification administrative.")
                            
                        conn.cursor().execute("INSERT INTO transactions (username, type, montant, detail, date, statut, iban_dest) VALUES (?,?,?,?,?,?,?)", 
                                            (u, "Virement Sortant", mnt_s, f"Vers {ib_d}", datetime.now().strftime("%d/%m/%Y"), stat, ib_d))
                    st.rerun()

    elif menu == "Mon Profil":
        st.subheader("👤 Informations du Titulaire")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
            st.file_uploader("Modifier la photo", type=['jpg', 'png'])
        with col2:
            st.markdown(f"**IDENTIFIANT :** `{u}`\n\n**PRÉNOM :** {decrypt_data(data['prenom'])}\n\n**NOM :** {decrypt_data(data['nom'])}\n\n**MOBILE :** {data['phone']}\n\n**STATUT :** {data['status']}")
        st.divider()
        st.subheader("📑 Vérification d'Identité")
        st.file_uploader("Copie CNI / Passeport", type=['jpg', 'png', 'pdf'])
        if st.button("Soumettre mon dossier"): st.success("Documents envoyés.")

    elif menu == "RIB":
        nom_complet = f"{decrypt_data(data['prenom'])} {decrypt_data(data['nom'])}".upper()
        st.markdown(f"<div style='background:white; color:black; padding:40px; border-radius:10px; border:2px solid #ccc; font-family:monospace;'><h2 style='text-align:center;'>RELEVÉ D'IDENTITÉ BANCAIRE</h2><hr><p><b>TITULAIRE :</b> {nom_complet}</p><p><b>IBAN :</b> {decrypt_data(data['iban'])}</p><p><b>BIC :</b> {decrypt_data(data['bic'])}</p></div>", unsafe_allow_html=True)

    elif menu == "Historique":
        with sqlite3.connect(DB_NAME) as conn:
            df = pd.read_sql_query("SELECT date, type, montant, statut, detail FROM transactions WHERE username=? ORDER BY id DESC", conn, params=(u,))
        
        st.subheader("📊 Analyses & Statistiques")
        if not df.empty:
            df_plot = df[df['statut'] == 'Validé'].copy()
            df_plot['Catégorie'] = df_plot['type'].apply(lambda x: 'Revenus' if x in ['Dépôt', 'Virement Reçu'] else 'Dépenses')
            stats = df_plot.groupby('Catégorie')['montant'].sum().reset_index()
            st.bar_chart(data=stats, x='Catégorie', y='montant')
        else:
            st.info("Aucune donnée disponible pour le graphique.")
            
        st.divider()
        st.subheader("📜 Liste des mouvements")
        st.table(df)

# --- 6. ESPACE ADMIN ---
else:
    st.sidebar.title("🏢 ADMIN PANEL")
    if st.sidebar.button("Log out"): st.session_state.user = None; st.rerun()
    t1, t2 = st.tabs(["Utilisateurs", "Virements en attente"])
    with t1:
        with sqlite3.connect(DB_NAME) as conn:
            users = pd.read_sql_query("SELECT username, status, gel_avoirs FROM users", conn)
        for _, r in users.iterrows():
            with st.expander(f"Client : {r['username']}"):
                c1, c2 = st.columns(2)
                if c1.button("Bloquer/Débloquer", key=f"b_{r['username']}"):
                    new_s = "Bloqué" if r['status'] == "Actif" else "Actif"
                    with sqlite3.connect(DB_NAME) as conn: conn.cursor().execute("UPDATE users SET status=? WHERE username=?", (new_s, r['username']))
                    st.rerun()
                if c2.button("Geler/Dégeler", key=f"g_{r['username']}"):
                    new_g = 1 if r['gel_avoirs'] == 0 else 0
                    with sqlite3.connect(DB_NAME) as conn: conn.cursor().execute("UPDATE users SET gel_avoirs=? WHERE username=?", (new_g, r['username']))
                    st.rerun()
    with t2:
        with sqlite3.connect(DB_NAME) as conn:
            pends = pd.read_sql_query("SELECT * FROM transactions WHERE statut='En attente'", conn)
        for _, t in pends.iterrows():
            st.warning(f"Virement de {t['montant']}€ vers {t['iban_dest']}")
            ca, cb = st.columns(2)
            if ca.button("✅ Approuver", key=f"ok_{t['id']}"):
                with sqlite3.connect(DB_NAME) as conn:
                    conn.cursor().execute("UPDATE users SET solde_courant = solde_courant - ? WHERE username=?", (t['montant'], t['username']))
                    all_u = conn.cursor().execute("SELECT username, iban FROM users").fetchall()
                    for row in all_u:
                        if decrypt_data(row[1]) == t['iban_dest']:
                            conn.cursor().execute("UPDATE users SET solde_courant = solde_courant + ? WHERE username=?", (t['montant'], row[0]))
                            add_notif(row[0], f"Virement reçu : +{t['montant']}€")
                    conn.cursor().execute("UPDATE transactions SET statut='Validé' WHERE id=?", (t['id'],))
                st.rerun()
            if cb.button("❌ Refuser", key=f"no_{t['id']}"):
                with sqlite3.connect(DB_NAME) as conn:
                    conn.cursor().execute("UPDATE transactions SET statut='Refusé' WHERE id=?", (t['id'],))
                st.rerun()