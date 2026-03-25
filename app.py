import streamlit as st
import pandas as pd
import math

st.set_page_config(
    page_title="Gestão de Perdas",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# CSS GLOBAL — Paleta Clean & Neutra
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding: 2rem 1.5rem 4rem !important;
    max-width: 1000px !important;
}

/* Typography */
h1, h2, h3 {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    color: #1e293b;
    letter-spacing: -0.025em;
}

/* Header */
.app-header {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    border-radius: 20px;
    padding: 2rem 2rem 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 20px 25px -5px rgba(0, 0,0, 0.1), 0 10px 10px -5px rgba(0, 0,0, 0.04);
}

.app-header h1 {
    color: #ffffff;
    font-size: clamp(1.5rem, 5vw, 2rem);
    font-weight: 700;
    margin: 0 0 0.5rem 0;
    letter-spacing: -0.03em;
}

.app-header p {
    color: #cbd5e1;
    font-size: 0.95rem;
    margin: 0;
    font-weight: 400;
}

/* Section labels */
.section-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #64748b;
    margin: 2.5rem 0 1rem 0;
}

/* Metrics - Clean cards */
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.5rem !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0,0, 0.1), 0 2px 4px -1px rgba(0, 0,0, 0.06);
    transition: all 0.2s ease;
}

[data-testid="metric-container"]:hover {
    box-shadow: 0 10px 15px -3px rgba(0, 0,0, 0.1), 0 4px 6px -2px rgba(0, 0,0, 0.05);
    transform: translateY(-2px);
}

[data-testid="metric-container"] > div:first-child {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #64748b !important;
    margin-bottom: 0.25rem;
}

[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Inter', sans-serif !important;
    font-size: clamp(1.4rem, 4.5vw, 1.8rem) !important;
    font-weight: 700 !important;
    color: #1e293b !important;
}

/* Inputs - Minimal */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    border-radius: 12px !important;
    border: 2px solid #e2e8f0 !important;
    background: #ffffff !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.875rem 1rem !important;
    transition: all 0.2s ease;
    font-weight: 500;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    outline: none !important;
}

[data-testid="stTextInput"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: #475569 !important;
    letter-spacing: 0.025em !important;
    text-transform: uppercase !important;
    margin-bottom: 0.5rem !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
    border-radius: 12px !important;
    border: 2px solid #e2e8f0 !!important;
    background: #ffffff !important;
}

/* Buttons - Primary */
.stButton > button {
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.025em !important;
    border: none !important;
    padding: 0.875rem 1.5rem !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px 0 rgba(59, 130, 246, 0.4);
}

.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
    transform: translateY(-1px);
    box-shadow: 0 8px 25px 0 rgba(59, 130, 246, 0.4);
}

/* Secondary buttons */
.stDownloadButton > button {
    background: #f8fafc !important;
    color: #1e293b !important;
    border: 2px solid #e2e8f0 !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    width: 100% !important;
    padding: 0.875rem 1.5rem !important;
    transition: all 0.2s ease;
}

.stDownloadButton > button:hover {
    background: #f1f5f9 !important;
    border-color: #cbd5e1 !important;
    transform: translateY(-1px);
}

/* Radio buttons */
[data-testid="stRadio"] label {
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    color: #374151 !important;
    padding: 0.5rem 0;
}

/* File uploader */
[data-testid="stFileUploader"] {
    border: 2px dashed #e2e8f0 !important;
    border-radius: 16px !important;
    background: #f8fafc !important;
    transition: all 0.2s ease;
}

[data-testid="stFileUploader"]:hover {
    border-color: #cbd5e1 !important;
    background: #f1f5f9 !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 1px solid #e2e8f0 !important;
    font-size: 0.88rem !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0,0, 0.1);
}

/* Info box */
.info-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem;
    font-size: 0.9rem;
    color: #64748b;
    line-height: 1.7;
    margin-bottom: 1rem;
}

.info-box strong {
    color: #1e293b;
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
}

/* Divider */
hr {
    border: none !important;
    border-top: 1px solid #e2e8f0 !important;
    margin: 2.5rem 0 !important;
}

/* Simulation results */
.sim-result-ok {
    background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
    border: 2px solid #22c55e;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: #166534;
    font-weight: 600;
    font-size: 0.95rem;
    text-align: center;
    margin-top: 1rem;
    box-shadow: 0 4px 12px rgba(34, 197, 94, 0.15);
}

.sim-result-fail {
    background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
    border: 2px solid #ef4444;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: #dc2626;
    font-weight: 600;
    font-size: 0.95rem;
    text-align: center;
    margin-top: 1rem;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.15);
}

/* Columns spacing */
.stColumns > div {
    padding: 0 0.25rem;
}

/* Mobile */
@media (max-width: 768px) {
    .block-container {
        padding: 1.5rem 1rem 3rem !important;
    }
    .app-header {
        border-radius: 16px;
        padding: 1.5rem 1.25rem 1.25rem;
        margin-bottom: 1.5rem;
    }
}
</style>
""", unsafe_allow_html=True)
# =========================
# SESSION STATE
# =========================
if "df_manual" not in st.session_state:
    st.session_state.df_manual = pd.DataFrame(columns=[
        "INSTALACAO","REQUERIDA","INJETADA",
        "REVERSA","CONSUMO","ILUMINACAO_PUBLICA"
    ])
if "df" not in st.session_state:
    st.session_state.df = None
if "df_res" not in st.session_state:
    st.session_state.df_res = None

# =========================
# CURVA EQTL
# =========================
curva_lista = [
    0,0.88,1.4,1.84,2.22,2.58,2.91,3.23,3.53,3.82,4.09,
    4.36,4.62,4.87,5.12,5.36,5.6,5.83,6.05,6.27,6.49,
    6.71,6.92,7.12,7.33,7.53,7.73,7.93,8.12,8.31,8.5,
    8.69,8.87,9.06,9.24,9.42,9.6,9.77,9.95,10.12,10.29,
    10.47,10.63,10.8,10.97,11.13,11.3,11.46,11.62,11.78,11.94,
    12.1,12.26,12.41,12.57,12.72,12.88,13.03,13.18,13.33,13.48,
    13.63,13.78,13.93,14.07,14.22,14.37,14.51,14.65,14.8,14.94,
    15.08,15.22,15.36,15.5,15.64,15.78,15.92,16.05,16.19,16.33,
    16.46,16.6,16.73,16.87,17,17.13,17.26,17.4,17.53,17.66,
    17.79,17.92,18.05,18.18,18.31,18.43,18.56,18.69,18.81,18.94
]
curva = {i: curva_lista[i] for i in range(len(curva_lista))}

# =========================
# HEADER
# =========================
st.markdown("""
<div class="app-header">
    <h1>Gestão de Perdas</h1>
    <p>Planejamento, otimização e simulação operacional</p>
</div>
""", unsafe_allow_html=True)

# =========================
# ENTRADA
# =========================
st.markdown('<p class="section-label">Modo de entrada</p>', unsafe_allow_html=True)
modo = st.radio("Modo de entrada", ["Upload de Excel", "Manual"],
                horizontal=True, label_visibility="collapsed")

# =========================
# UPLOAD
# =========================
if modo == "Upload de Excel":

    st.markdown("""
    <div class="info-box">
        <strong>Colunas esperadas</strong>
        INSTALACAO &nbsp;·&nbsp; REQUERIDA &nbsp;·&nbsp; INJETADA &nbsp;·&nbsp;
        REVERSA &nbsp;·&nbsp; CONSUMO &nbsp;·&nbsp; ILUMINACAO_PUBLICA
    </div>
    """, unsafe_allow_html=True)

    file = st.file_uploader("Arquivo Excel (.xlsx)", type=["xlsx"])

    if file:
        st.session_state.df = pd.read_excel(file)
        st.session_state.df_res = None

# =========================
# MANUAL
# =========================
elif modo == "Manual":

    st.markdown('<p class="section-label">Nova instalação</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        inst       = st.text_input("Instalação")
        requerida  = st.number_input("Requerida",  0.0, key="in_req")
        injetada   = st.number_input("Injetada",   0.0, key="in_inj")

    with col2:
        reversa    = st.number_input("Reversa",             0.0, key="in_rev")
        consumo    = st.number_input("Consumo",             0.0, key="in_con")
        iluminacao = st.number_input("Iluminação Pública",  0.0, key="in_ilu")

    col_add, col_clear = st.columns(2)

    with col_add:
        if st.button("Adicionar"):
            if inst:
                nova = pd.DataFrame([{
                    "INSTALACAO":       inst,
                    "REQUERIDA":        requerida,
                    "INJETADA":         injetada,
                    "REVERSA":          reversa,
                    "CONSUMO":          consumo,
                    "ILUMINACAO_PUBLICA": iluminacao
                }])
                st.session_state.df_manual = pd.concat(
                    [st.session_state.df_manual, nova], ignore_index=True
                )
                st.session_state.df_res = None

    with col_clear:
        if st.button("Limpar tudo"):
            st.session_state.df_manual = st.session_state.df_manual.iloc[0:0]
            st.session_state.df = None
            st.session_state.df_res = None

    if not st.session_state.df_manual.empty:
        st.markdown('<p class="section-label">Instalações inseridas</p>', unsafe_allow_html=True)
        st.dataframe(st.session_state.df_manual, use_container_width=True)

        if st.button("Rodar Análise"):
            st.session_state.df = st.session_state.df_manual.copy()
            st.session_state.df_res = None

# =========================
# PROCESSAMENTO
# =========================
if st.session_state.df is not None and st.session_state.df_res is None:

    df = st.session_state.df.copy()
    df.columns = df.columns.str.strip().str.upper()
    st.session_state.df = df

    resultados = []

    for _, row in df.iterrows():

        total = row["REQUERIDA"] + row["INJETADA"]
        perda = (
            row["REQUERIDA"] + row["INJETADA"]
            - row["REVERSA"] - row["CONSUMO"]
            - row["ILUMINACAO_PUBLICA"]
        )
        perda = max(0, perda)

        if total == 0:
            continue

        perda_pct = perda / total
        faixa     = math.ceil(perda_pct * 100)
        meta_pct  = curva.get(faixa, 0)

        red_min   = perda * (meta_pct / 100)
        red_10    = max(0, perda - 0.10 * total)
        red_total = max(red_min, red_10)

        ganho = 0
        plano = {}
        acoes = [
            ("Inclusoes", 150),
            ("Cod100",    120),
            ("Exclusoes", 100),
            ("Cod200",    100),
            ("Cod300",     30)
        ]
        acoes.sort(key=lambda x: x[1], reverse=True)

        for nome, impacto in acoes:
            if ganho >= red_total:
                break
            qtd   = math.ceil((red_total - ganho) / impacto)
            plano[nome] = qtd
            ganho += qtd * impacto

        perda_final = perda - ganho

        resultados.append({
            "INSTALACAO":   row["INSTALACAO"],
            "PERDA_%":      round(perda_pct * 100, 2),
            "RED_MIN_EFICIÊNCIA":      round(red_min, 2),
            "RED_PARA_ADEQUADA":       round(red_10, 2),
            "RED_NECESSÁRIA":    round(red_total, 2),
            "PERDA_FINAL":  round(perda_final, 2),
            "ATINGIU_META": perda_final <= (perda - red_total),
            "TOTAL_ACOES":  sum(plano.values()),
            **plano
        })

    st.session_state.df_res = pd.DataFrame(resultados)

# =========================
# DASHBOARD + SIMULADOR
# =========================
if st.session_state.df_res is not None:

    df_res = st.session_state.df_res
    df     = st.session_state.df

    # Métricas
    st.markdown('<p class="section-label">Visão Geral</p>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Instalações",   len(df_res))
    c2.metric("Meta atingida", f"{df_res['ATINGIU_META'].mean() * 100:.1f}%")
    c3.metric("Ações totais",  int(df_res["TOTAL_ACOES"].sum()))

    st.markdown("---")

    # Ranking
    st.markdown('<p class="section-label">Ranking por Perda</p>', unsafe_allow_html=True)
    st.dataframe(
        df_res.sort_values("PERDA_%", ascending=False),
        use_container_width=True
    )

    # Gráficos
    st.markdown('<p class="section-label">Perda por Instalação (%)</p>', unsafe_allow_html=True)
    st.bar_chart(df_res.set_index("INSTALACAO")["PERDA_%"], use_container_width=True)

    st.markdown('<p class="section-label">Ações por Instalação</p>', unsafe_allow_html=True)
    st.bar_chart(df_res.set_index("INSTALACAO")["TOTAL_ACOES"], use_container_width=True)

    # Download
    st.markdown('<p class="section-label">Exportar</p>', unsafe_allow_html=True)
    st.download_button(
        "Baixar resultado (.csv)",
        df_res.to_csv(index=False),
        "resultado.csv",
        mime="text/csv"
    )

    st.markdown("---")

    # Simulador
    st.markdown('<p class="section-label">Simulação de Ações</p>', unsafe_allow_html=True)

    inst_sel = st.selectbox("Instalação", df_res["INSTALACAO"])

    base  = df[df["INSTALACAO"] == inst_sel].iloc[0]
    perda = (
        base["REQUERIDA"] + base["INJETADA"]
        - base["REVERSA"] - base["CONSUMO"]
        - base["ILUMINACAO_PUBLICA"]
    )
    meta = perda - df_res[df_res["INSTALACAO"] == inst_sel]["RED_TOTAL"].iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        inc  = st.number_input("Inclusões",  0, key="sim_inc")
        c100 = st.number_input("Cod 100",    0, key="sim_c100")
        c200 = st.number_input("Cod 200",    0, key="sim_c200")

    with col2:
        exc  = st.number_input("Exclusões",  0, key="sim_exc")
        c300 = st.number_input("Cod 300",    0, key="sim_c300")

    ganho      = inc * 150 + c100 * 120 + exc * 100 + c200 * 100 + c300 * 30
    perda_proj = perda - ganho

    st.markdown('<p class="section-label">Resultado projetado</p>', unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)
    r1.metric("Ganho",       f"{ganho:.2f}")
    r2.metric("Perda Final", f"{perda_proj:.2f}")
    r3.metric("Meta",        f"{meta:.2f}")

    if perda_proj <= meta:
        st.markdown('<div class="sim-result-ok">Meta atingida</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="sim-result-fail">Faltam {perda_proj - meta:.2f} kWh para atingir a meta</div>',
            unsafe_allow_html=True
        )

else:
    st.info("Selecione um modo de entrada e insira os dados para iniciar a análise.")
