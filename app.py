import streamlit as st
import base64

# --- CONFIGURAZIONE AUTO-DEPLOY (SECRETS) ---
try:
    # Verifichiamo che la chiave esista nei secrets (in locale .streamlit/secrets.toml)
    if not st.secrets.get("OPENROUTER_API_KEY"):
        st.error("❌ ERRORE: Chiave API mancante nei Secrets!")
        st.info(
            "Aggiungi OPENROUTER_API_KEY = 'sk-or-...' nel file .streamlit/secrets.toml"
        )
        st.stop()
except FileNotFoundError:
    st.error("❌ ERRORE CRITICO: File secrets.toml non trovato.")
    st.stop()

# Nota: Non importiamo più os o base64 se non servono

# Importiamo i moduli solo dopo aver settato la chiave,
# così logic.py può leggerla se necessario (anche se idealmente andrebbe rifattorizzato)
from engine import generate_trajectory_simulation
import logic
import utils

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="FUTURE.IO",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# --- CARICAMENTO CSS ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("assets/style.css")

# --- BACKGROUND VIDEO HACK ---
# Streamlit non ha bg video nativo. Uso HTML puro fissato.
try:
    video_file = open("assets/Galactic2.mp4", "rb")
    video_bytes = video_file.read()
    video_b64 = base64.b64encode(video_bytes).decode()

    st.markdown(
        f"""
        <style>
        .video-bg {{
            position: fixed;
            right: 0;
            bottom: 0;
            min-width: 100%;
            min-height: 100%;
            z-index: -1;
            opacity: 0.6; /* Leggermente più visibile per contrastare il testo bianco */
            filter: grayscale(100%) contrast(1.1) brightness(0.8);
        }}
        </style>
        <video autoplay muted loop playsinline class="video-bg">
            <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
        </video>
        """,
        unsafe_allow_html=True,
    )
except FileNotFoundError:
    st.error(
        "File 'Galactic2.mp4' non trovato. Assicurati che sia nella cartella assets."
    )

# --- NAVBAR ---
st.markdown(
    """
<div class="nav-container">
    <div style="font-family: 'Space Grotesk'; font-weight: 700; font-size: 1.5rem; letter-spacing: -1px;">
        ◈ FUTURE.IO
    </div>
    <div class="mono-text" style="font-size: 0.75rem; opacity: 0.6; letter-spacing: 2px;">
        SYSTEM_READY // HACKATHON_BUILD
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# --- SESSION STATE ---
if "step" not in st.session_state:
    st.session_state.step = 0

# --- HERO SECTION (TITLE) ---
# Uso spacer per mantenere il titolo centrato e bello, ma non restringiamo il resto
st.markdown("<br><br><br><br>", unsafe_allow_html=True)

col_spacer_l, col_content, col_spacer_r = st.columns([1, 20, 1])

with col_content:
    st.markdown(
        """
        <div style="text-align: center;">
            <h1 class="hero-title">SEI FUTURO<br><span class="subtitle-gradient">NON MEMORIA</span></h1>
        </div>
    """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # STEP 0: SOLO BOTTONE INIZIALE (CENTRATO)
    if st.session_state.step == 0:
        col_btn_l, col_btn_c, col_btn_r = st.columns([1, 1, 1])
        with col_btn_c:
            # Usiamo un callback per avanzare di step senza rerun complessi
            if st.button("SCOPRI CHI SARAI", use_container_width=True):
                st.session_state.step = 1
                st.rerun()

# --- STEP 1: INPUT E GENERAZIONE (FULL WIDTH) ---
if st.session_state.step >= 1:
    st.divider()  # Separatore visivo dopo il titolo

    # --- INPUT SECTION ---
    # Container principale per gli input
    with st.container():
        st.markdown("### ▽ DATI INGRESSO BIOMETRICI")

        col_cv, col_pers = st.columns([1, 1])

        with col_cv:
            with st.container(border=True):
                st.subheader("1. CARICA CV")
                uploaded_file = st.file_uploader(
                    "Carica PDF", type="pdf", label_visibility="collapsed"
                )

                if uploaded_file is not None:
                    cv_text_extracted = utils.extract_text_from_pdf(uploaded_file)
                    st.success("PDF Caricato con successo!")
                    cv_text = st.text_area(
                        "ANTEMPRIMA TESTO ESTRATTO",
                        value=cv_text_extracted,
                        height=150,
                        disabled=False,
                    )
                else:
                    cv_text = st.text_area(
                        "Oppure INCOLLA CV GREZZO",
                        height=200,
                        placeholder="Incolla qui il testo del tuo CV se non hai il PDF...",
                    )

        with col_pers:
            with st.container(border=True):
                st.subheader("2. MATRICE PERSONALITÀ & DIGITAL FOOTPRINT")

                # Digital Input Section
                col_dig_1, col_dig_2 = st.columns(2)
                with col_dig_1:
                    github_user = st.text_input(
                        "GitHub Username", placeholder="e.g. DAlexis0"
                    )
                with col_dig_2:
                    web_links = st.text_input(
                        "Web / Behance / Portfolio", placeholder="url1.com, url2.com"
                    )
                    # Placeholder per feedback visivo immediato
                    portfolio_feedback = st.empty()

                st.divider()
                st.caption("Human Inputs")

                # Split inputs come richiesto
                p_pers = st.text_input(
                    "Personalità", placeholder="Curioso, resiliente..."
                )
                p_dreams = st.text_input(
                    "Sogni", placeholder="Fondare una startup su Marte..."
                )
                p_goals = st.text_input(
                    "Obbiettivi", placeholder="Diventare CPO entro 5 anni..."
                )
                col_sub_1, col_sub_2 = st.columns(2)
                with col_sub_1:
                    p_work = st.text_input(
                        "Modo di lavorare", placeholder="Team player, async..."
                    )
                with col_sub_2:
                    p_learn = st.text_input(
                        "Modo di imparare", placeholder="Visuale, Hands-on..."
                    )

                # Concatenazione per il backend
                personality_text = f"""
                Personalità: {p_pers}
                Sogni: {p_dreams}
                Obbiettivi: {p_goals}
                Modo di lavorare: {p_work}
                Modo di imparare: {p_learn}
                """

    st.markdown("<br>", unsafe_allow_html=True)

    # --- BUTTON LOGIC WITH STATE ---
    if "analyzing" not in st.session_state:
        st.session_state.analyzing = False

    # Area Bottone Finale (Centrato ma in contesto full width)
    # Mostriamo il bottone SOLO se non stiamo già analizzando
    if not st.session_state.analyzing:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            start_analysis = st.button(
                "PROCEDI ALL'ANALISI", type="primary", use_container_width=True
            )

            if start_analysis:
                st.session_state.analyzing = True
                st.rerun()

    # --- ESECUZIONE ANALISI ---
    if st.session_state.analyzing:
        # Check validazione semplice
        if not cv_text:
            st.error("Per favore, carica almeno il CV per procedere.")
            st.session_state.analyzing = False  # Reset stato per mostrare bottone
        else:
            # --- VALIDAZIONE PRELIMINARE (Gate Check) ---
            with st.spinner("Verifica accessibilità link digitali..."):
                if web_links:
                    is_valid, error_msg = utils.validate_optional_link(web_links)
                    if not is_valid:
                        # Feedback negativo nel placeholder dedicato
                        portfolio_feedback.error(f"❌ Link non valido: {error_msg}")
                        st.error(
                            f"Errore nel link del portfolio: {error_msg}. Correggi o svuota il campo."
                        )
                        st.session_state.analyzing = (
                            False  # Reset stato per permettere correzione
                        )
                        st.stop()  # Blocca l'esecuzione QUI.
                    else:
                        portfolio_feedback.success("✅ Link verificato e accessibile.")

            with st.status(
                "Inizializzazione scansione neurale...", expanded=True
            ) as status:
                # 0. Data Enrichment (New)
                st.write("Analisi Digital Footprint (GitHub & Web)...")
                github_data = utils.get_github_dna(github_user)
                web_data = utils.get_web_dna(web_links)

                # 1. Analisi Archetipo (logic.py)
                st.write("Identificazione Archetipo Visionario...")
                archetype_data = logic.get_archetype_analysis(
                    personality_text + " " + cv_text
                )

                if "error" in archetype_data:
                    st.error(f"Errore Archetipo: {archetype_data['error']}")
                else:
                    st.markdown(
                        f"### Archetipo Identificato: **{archetype_data.get('archetype_title', 'Unknown')}**"
                    )
                    st.json(archetype_data, expanded=False)

                # 2. Generazione Traiettorie Future (engine.py)
                st.write("Simulazione Traiettorie Future...")
                cts_analysis = generate_trajectory_simulation(
                    cv_text, personality_text, github_data, web_data
                )

                if cts_analysis:
                    st.success("Simulazione Completata!")
                    status.update(
                        label="Sistema Pronto", state="complete", expanded=False
                    )

                    # Visualizzazione Risultati
                    st.divider()
                    st.markdown(f"## CORE VECTOR\n*{cts_analysis.core_vector}*")

                    st.divider()

                    # Layout FULL WIDTH per le 3 Traiettorie
                    # Qui è la chiave: st.columns(3) viene chiamato nel contesto principale (wide)
                    col1, col2, col3 = st.columns(3)

                    # Funzione helper per card
                    def draw_trajectory_card(column, trajectory, type_label, color):
                        with column:
                            st.markdown(
                                f"<h3 style='color:{color}'>{type_label}</h3>",
                                unsafe_allow_html=True,
                            )
                            with st.container(border=True):
                                st.markdown(f"#### {trajectory.title}")
                                st.caption(f"Probabilità: {trajectory.probability}")
                                st.write(trajectory.description)
                                st.markdown("---")
                                st.markdown("**Progetto Ipotetico:**")
                                st.markdown(
                                    f"""
                                    <div class="project-box">
                                        <span style="font-size: 0.8rem; text-transform: uppercase; color: rgba(255,255,255,0.5); letter-spacing: 1px;">PROGETTO IPOTETICO</span>
                                        <p style="margin-top: 0.5rem; font-size: 0.95rem; line-height: 1.4;">{trajectory.hypothetical_project}</p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                    draw_trajectory_card(
                        col1,
                        cts_analysis.trajectory_1_strategic,
                        "STRATEGIC PATH",
                        "#4CAF50",
                    )
                    draw_trajectory_card(
                        col2,
                        cts_analysis.trajectory_2_challenge,
                        "CHALLENGE PATH",
                        "#FFC107",
                    )
                    draw_trajectory_card(
                        col3,
                        cts_analysis.trajectory_3_visionary,
                        "VISIONARY PATH",
                        "#F44336",
                    )

                else:
                    st.error(
                        "Errore nella generazione delle traiettorie. Verifica la chiave API."
                    )


# --- SPACER ---
st.markdown("<br><br>", unsafe_allow_html=True)

# --- MARQUEE ---
st.markdown(
    """
<div style="overflow: hidden; white-space: nowrap; border-top: 1px solid rgba(255,255,255,0.1); border-bottom: 1px solid rgba(255,255,255,0.1); padding: 15px 0; background: rgba(0,0,0,0.3); backdrop-filter: blur(5px);">
    <div style="display: inline-block; animation: marquee 20s linear infinite;" class="mono-text">
        <span style="opacity: 0.7; font-size: 0.9rem; letter-spacing: 3px;">
        PREDICTIVE PORTFOLIO ✦ NEURAL ARCHITECTURE ✦ BIO-DATA INPUT ✦ FUTURE CASTING ✦ PREDICTIVE PORTFOLIO ✦ NEURAL ARCHITECTURE ✦ BIO-DATA INPUT ✦ FUTURE CASTING
        </span>
    </div>
</div>
<style>
@keyframes marquee {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}
</style>
""",
    unsafe_allow_html=True,
)

# --- FOOTER ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
<div style="border-top: 1px solid #ffffff; padding: 3rem 0; text-align: center; color: #ffffff;" class="mono-text">
    <p style="font-size: 0.9rem; margin-bottom: 0.3rem;">FUTURE.IO // HACKATHON BUILD</p>
    <p style="font-size: 0.8rem; opacity: 0.8;">© Alejandro Lopez</p>
</div>
""",
    unsafe_allow_html=True,
)
