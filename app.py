import streamlit as st
import pandas as pd
import math

st.set_page_config(
    page_title="Calculadora de Recuperação de Energia",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# PALETA LIME-TEAL VIBRANT
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* VARIÁVEIS DA PALETA */
:root {
    --lime-cream: #d9ed92;
    --light-green: #b5e48c;
    --light-green-2: #99d98c;
    --emerald: #76c893;
    --ocean-mist: #52b69a;
    --tropical-teal: #34a0a4;
    --bondi-blue: #168aad;
    --cerulean: #1a759f;
    --baltic-blue: #1e6091;
    --yale-blue: #184e77;
    
    --bg-primary: #f9fcfa;
    --bg-card: #ffffff;
    --text-primary: #1a3c34;
    --text-secondary: #2d5a4a;
    --border: #e6f3e8;
}

/* BASE */
* { font-family: 'Inter', sans-serif; }
.stApp { 
    background: linear-gradient(135deg, var(--bg-primary) 0%, #f0f8f5 100%);
    color: var(--text-primary);
}

.block-container {
    padding: 2rem 1.5rem 4rem;
    max-width: 1100px;
    color: var(--text-primary);
}

/* HEADER VIBRANTE */
.app-header {
    background: linear-gradient(135deg, var(--yale-blue) 0%, var(--baltic-blue) 20%, var(--bondi-blue) 100%);
    border-radius: 24px;
    padding: 2.5rem 2rem 2rem;
    margin-bottom: 2.5rem;
    box-shadow: 0 25px 50px -12px rgba(24, 78, 119, 0.3);
    position: relative;
    overflow: hidden;
}

.app-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--lime-cream), var(--light-green), var(--tropical-teal));
}

.app-header h1 {
    color: #ffffff;
    font-size: clamp(1.75rem, 5vw, 2.25rem);
    font-weight: 700;
    margin: 0 0 0.5rem;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.app-header p {
    color: #e6f3e8;
    font-size: 1rem;
    font-weight: 400;
    margin: 0;
}

/* SEÇÕES */
.section-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    background: linear-gradient(135deg, var(--tropical-teal), var(--bondi-blue));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 3rem 0 1.25rem 0;
}

/* MÉTRICAS LIME-GREEN */
[data-testid="metric-container"] {
    background: var(--bg-card);
    border: 1px solid var(--light-green-2);
    border-radius: 20px;
    padding: 1.75rem;
    box-shadow: 0 10px 15px -3px rgba(99, 217, 140, 0.2);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

[data-testid="metric-container"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: linear-gradient(180deg, var(--lime-cream), var(--light-green));
}

[data-testid="metric-container"]:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 25px -5px rgba(99, 217, 140, 0.3);
    border-color: var(--emerald);
}

[data-testid="metric-container"] > div:first-child {
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

[data-testid="stMetricValue"] {
    color: var(--text-primary);
    font-weight: 700;
    font-size: clamp(1.5rem, 5vw, 2rem);
}

/* INPUTS TEAL */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    border-radius: 16px;
    border: 2px solid var(--border);
    background: var(--bg-card);
    color: var(--text-primary);
    font-weight: 500;
    padding: 1rem 1.25rem;
    transition: all 0.2s ease;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: var(--tropical-teal);
    box-shadow: 0 0 0 4px rgba(52, 160, 164, 0.15);
}

label {
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.025em;
    text-transform: uppercase;
}

/* BOTÕES EMERALD */
.stButton > button {
    background: linear-gradient(135deg, var(--ocean-mist), var(--tropical-teal));
    color: white;
    border-radius: 16px;
    font-weight: 600;
    padding: 1rem 1.75rem;
    border: none;
    box-shadow: 0 10px 15px -3px rgba(52, 160, 164, 0.4);
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, var(--bondi-blue), var(--cerulean));
    transform: translateY(-2px);
    box-shadow: 0 20px 20px -5px rgba(52, 160, 164, 0.5);
}

.stDownloadButton > button {
    background: linear-gradient(135deg, var(--lime-cream), var(--light-green));
    color: var(--text-primary);
    border: 2px solid var(--light-green-2);
    border-radius: 16px;
    font-weight: 600;
}

.stDownloadButton > button:hover {
    background: linear-gradient(135deg, var(--light-green), var(--emerald));
    transform: translateY(-1px);
}

/* DATAFRAME */
[data-testid="stDataFrame"] {
    border-radius: 20px;
    border: 1px solid var(--border);
    box-shadow: 0 10px 15px -3px rgba(52, 160, 164, 0.15);
}

/* RESULTADOS */
.sim-result-ok {
    background: linear-gradient(135deg, var(--light-green), var(--light-green-2));
    border: 2px solid var(--emerald);
    color: #1a533d;
    border-radius: 16px;
    box-shadow: 0 10px 20px rgba(118, 200, 147, 0.3);
}

.sim-result-fail {
    background: linear-gradient(135deg, #fee2e2, #fecaca);
    border: 2px solid #f87171;
    color: #991b1b;
    border-radius: 16px;
}

/* MOBILE */
@media (max-width: 768px) {
    .block-container { padding: 1.5rem 1rem 3rem; }
    .app-header { padding: 2rem 1.5rem 1.5rem; margin-bottom: 2rem; }
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
    <h1>Projeção de Recuperação de Energia</h1>
    <p>Calculadora de impacto operacional</p>
</div>
""", unsafe_allow_html=True)

# =========================
# ENTRADA
# =========================
st.markdown('<p class="section-label">INPUT DOS DADOS</p>', unsafe_allow_html=True)
modo = st.radio("Modo de entrada", ["Upload de Excel", "Manual"],
                horizontal=True)

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
        inst       = st.text_input("Instalação MF", placeholder = "Campo Necessário")
        requerida  = st.number_input("Requerida",  step = 500.0, key="in_req")
        injetada   = st.number_input("Injetada",   step = 500.0, key="in_inj")

    with col2:
        reversa    = st.number_input("Reversa",   step =    500.0, key="in_rev")
        consumo    = st.number_input("Consumo",   step =    500.0, key="in_con")
        iluminacao = st.number_input("Iluminação Pública",  step = 500.0, key="in_ilu")

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
            "PERDA_(kWh)":  round(perda, 2)
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
    

    st.markdown("---")

    # Ranking
    st.markdown('<p class="section-label">Ranking por Perda</p>', unsafe_allow_html=True)
    st.dataframe(
        df_res.sort_values("PERDA_%", ascending=False),
        use_container_width=True
    )

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
    meta = perda - df_res[df_res["INSTALACAO"] == inst_sel]["RED_NECESSÁRIA"].iloc[0]

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
