import streamlit as st
import pandas as pd
import math
import re
import io
from pypdf import PdfReader

st.set_page_config(
    page_title="Calculadora de Recuperação de Energia",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# ESTILO (ALTO CONTRASTE)
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* VARIÁVEIS */
:root {
    --blue-900: #0f2740;
    --blue-700: #1f4f7a;
    --blue-600: #2d648f;
    --green-500: #2f9e79;
    --green-100: #e8f6f0;
    --gray-50: #f7fafc;
    --gray-100: #eef3f7;
    --gray-300: #ccd9e5;
    --gray-700: #334b61;

    --bg-primary: #f4f8fb;
    --bg-card: #ffffff;
    --text-primary: #10273d;
    --text-secondary: #35506b;
    --border: #d8e3ec;
}

/* BASE */
* { font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; }
.stApp { 
    background: linear-gradient(180deg, var(--bg-primary) 0%, var(--gray-50) 100%);
    color: var(--text-primary);
}

.block-container {
    padding: 2rem 1.5rem 4rem;
    max-width: 1100px;
    color: var(--text-primary);
}

/* HEADER */
.app-header {
    background: linear-gradient(135deg, var(--blue-900) 0%, var(--blue-700) 100%);
    border-radius: 24px;
    padding: 2.5rem 2rem 2rem;
    margin-bottom: 2.5rem;
    box-shadow: 0 16px 32px -10px rgba(15, 39, 64, 0.35);
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
    background: linear-gradient(90deg, #7dd3fc, #34d399);
}

.app-header h1 {
    color: #ffffff;
    font-size: clamp(1.75rem, 5vw, 2.25rem);
    font-weight: 700;
    margin: 0 0 0.5rem;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.app-header p {
    color: #d8e8f6;
    font-size: 1rem;
    font-weight: 400;
    margin: 0;
}

.app-header p,
.app-header h1 {
    color: #ffffff !important;
}

[data-testid="stMarkdownContainer"] .app-header h1,
[data-testid="stMarkdownContainer"] .app-header p {
    color: #ffffff !important;
}

/* SEÇÕES */
.section-label {
    font-size: 0.88rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    color: var(--blue-700);
    margin: 3rem 0 1.25rem 0;
}

.helper-text {
    color: var(--text-secondary);
    font-size: 0.94rem;
    margin: 0.15rem 0 1rem 0;
}

.step-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.85rem;
    margin: 0.75rem 0 1.5rem;
}

.step-card {
    background: var(--bg-card);
    border: 1px solid var(--gray-300);
    border-radius: 14px;
    padding: 0.8rem 0.95rem;
    box-shadow: 0 6px 16px -10px rgba(51, 75, 97, 0.35);
}

.step-card strong {
    display: block;
    color: var(--blue-700);
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.2rem;
}

.step-card span {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.info-box {
    background: linear-gradient(135deg, #f4fafc, #eef6fb);
    border: 1px solid var(--gray-300);
    border-radius: 14px;
    padding: 0.8rem 1rem;
    color: var(--gray-700);
    font-size: 0.9rem;
    margin-bottom: 1rem;
}

.counter-chip {
    display: inline-block;
    background: #e8f1f8;
    color: var(--blue-700);
    border: 1px solid #c5d9ea;
    border-radius: 999px;
    padding: 0.3rem 0.7rem;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.6rem;
}

.module-shell {
    background: var(--bg-card);
    border: 1px solid var(--gray-300);
    border-radius: 18px;
    padding: 1rem 1rem 0.55rem;
    box-shadow: 0 10px 20px -16px rgba(16, 39, 61, 0.42);
    margin-bottom: 1rem;
}

.module-title {
    margin: 0;
    color: var(--blue-700);
    font-size: 1.02rem;
    font-weight: 700;
}

.module-subtitle {
    margin: 0.25rem 0 0;
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.sim-progress-wrap {
    background: var(--bg-card);
    border: 1px solid var(--gray-300);
    border-radius: 16px;
    padding: 0.75rem 0.9rem;
    margin-bottom: 0.9rem;
}

.sim-progress-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--gray-700);
    font-size: 0.83rem;
    margin-bottom: 0.5rem;
}

.sim-progress-track {
    width: 100%;
    height: 10px;
    border-radius: 999px;
    background: #e8eff5;
    overflow: hidden;
}

.sim-progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #34d399, #3b82f6);
    transition: width 0.3s ease;
}

.action-hint {
    margin: 0.2rem 0 0.85rem;
    color: var(--text-secondary);
    font-size: 0.88rem;
}

.status-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.65rem;
    margin: 0.2rem 0 1.2rem;
}

.status-card {
    border-radius: 12px;
    border: 1px solid var(--gray-300);
    background: var(--bg-card);
    padding: 0.65rem 0.8rem;
}

.status-card strong {
    display: block;
    font-size: 0.75rem;
    color: var(--gray-700);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.15rem;
}

.status-ok {
    color: #166534;
    font-weight: 700;
}

.status-wait {
    color: #9a3412;
    font-weight: 700;
}

.sim-badge {
    display: inline-block;
    border-radius: 999px;
    padding: 0.3rem 0.7rem;
    font-size: 0.8rem;
    font-weight: 700;
    margin-bottom: 0.6rem;
}

.sim-badge-critico {
    background: #fee2e2;
    border: 1px solid #ef4444;
    color: #991b1b;
}

.sim-badge-atencao {
    background: #fef3c7;
    border: 1px solid #f59e0b;
    color: #92400e;
}

.sim-badge-ok {
    background: #dcfce7;
    border: 1px solid #22c55e;
    color: #166534;
}

/* MÉTRICAS */
[data-testid="metric-container"] {
    background: var(--bg-card);
    border: 1px solid var(--gray-300);
    border-radius: 20px;
    padding: 1.75rem;
    box-shadow: 0 10px 18px -12px rgba(16, 39, 61, 0.35);
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
    background: linear-gradient(180deg, #34d399, #3b82f6);
}

[data-testid="metric-container"]:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 25px -8px rgba(16, 39, 61, 0.28);
    border-color: #9fc2de;
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
    border-color: var(--blue-600);
    box-shadow: 0 0 0 4px rgba(45, 100, 143, 0.14);
}

label {
    color: var(--gray-700);
    font-size: 0.86rem;
    font-weight: 600;
    letter-spacing: 0;
    text-transform: none;
}

/* BOTÕES */
.stButton > button {
    background: #e8f1f8;
    color: var(--blue-700);
    border-radius: 14px;
    font-weight: 600;
    padding: 0.8rem 1.2rem;
    border: 1px solid #bfd4e6;
    box-shadow: 0 8px 12px -8px rgba(31, 79, 122, 0.25);
    transition: all 0.25s ease;
}

.stButton > button:hover {
    background: #dbeaf5;
    transform: translateY(-1px);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--blue-700), var(--blue-600));
    color: #ffffff;
    border-radius: 14px;
    font-weight: 600;
    padding: 0.9rem 1.35rem;
    border: none;
    box-shadow: 0 10px 15px -3px rgba(31, 79, 122, 0.35);
    transition: all 0.25s ease;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, var(--blue-900), var(--blue-700));
    transform: translateY(-2px);
    box-shadow: 0 20px 20px -5px rgba(31, 79, 122, 0.35);
}

.stButton > button[kind="secondary"] {
    background: #ffffff;
    color: #9a3412;
    border: 1px solid #fdba74;
    box-shadow: 0 8px 12px -8px rgba(194, 65, 12, 0.2);
}

.stButton > button[kind="secondary"]:hover {
    background: #fff7ed;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #dff3ea, #cdeee0);
    color: #0f5132;
    border: 2px solid #8fd6b9;
    border-radius: 16px;
    font-weight: 600;
}

.stDownloadButton > button * {
    color: #0f5132 !important;
}

.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #cdeee0, #b8e7d3);
    transform: translateY(-1px);
}

/* DATAFRAME */
[data-testid="stDataFrame"] {
    border-radius: 20px;
    border: 1px solid var(--border);
    box-shadow: 0 10px 15px -3px rgba(31, 79, 122, 0.12);
}

/* RESULTADOS */
.sim-result-ok {
    background: linear-gradient(135deg, #def7ec, #c8efd9);
    border: 2px solid var(--green-500);
    color: #12503b;
    border-radius: 16px;
    box-shadow: 0 10px 20px rgba(47, 158, 121, 0.2);
    padding: 0.75rem 0.95rem;
    font-weight: 600;
}

.sim-result-fail {
    background: linear-gradient(135deg, #fff1f1, #ffe2e2);
    border: 2px solid #ea6c6c;
    color: #8c1f1f;
    border-radius: 16px;
    padding: 0.75rem 0.95rem;
    font-weight: 600;
}

[data-baseweb="radio"] label,
[data-testid="stAlertContentInfo"],
[data-testid="stAlertContentWarning"],
[data-testid="stAlertContentError"],
[data-testid="stAlertContentSuccess"] {
    color: var(--text-primary) !important;
}

[data-baseweb="select"] > div,
[data-testid="stFileUploader"] section {
    border-color: var(--gray-300) !important;
}

/* MOBILE */
@media (max-width: 768px) {
    .block-container { padding: 1.5rem 1rem 3rem; }
    .app-header { padding: 2rem 1.5rem 1.5rem; margin-bottom: 2rem; }
    .step-grid { grid-template-columns: 1fr; }
    .status-grid { grid-template-columns: 1fr; }
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
if "run_analysis_requested" not in st.session_state:
    st.session_state.run_analysis_requested = False
if "active_step" not in st.session_state:
    st.session_state.active_step = "1. Entrada"
if "pending_step" not in st.session_state:
    st.session_state.pending_step = None
if "sim_clear_requested" not in st.session_state:
    st.session_state.sim_clear_requested = False
if "sim_persist_modo" not in st.session_state:
    st.session_state.sim_persist_modo = "Valor médio"
if "sim_persist_inc" not in st.session_state:
    st.session_state.sim_persist_inc = 0
if "sim_persist_c100" not in st.session_state:
    st.session_state.sim_persist_c100 = 0
if "sim_persist_exc" not in st.session_state:
    st.session_state.sim_persist_exc = 0
if "sim_persist_c200" not in st.session_state:
    st.session_state.sim_persist_c200 = 0
if "sim_persist_c300" not in st.session_state:
    st.session_state.sim_persist_c300 = 0
if "sim_persist_inc_medio" not in st.session_state:
    st.session_state.sim_persist_inc_medio = 150.0
if "sim_persist_c100_medio" not in st.session_state:
    st.session_state.sim_persist_c100_medio = 120.0
if "sim_persist_exc_medio" not in st.session_state:
    st.session_state.sim_persist_exc_medio = 100.0
if "sim_persist_c200_medio" not in st.session_state:
    st.session_state.sim_persist_c200_medio = 100.0
if "sim_persist_c300_medio" not in st.session_state:
    st.session_state.sim_persist_c300_medio = 30.0

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
    <p>Desenvolvido por: José Pedrosa</p>
    <p>jose.peronico@equatorialenergia.com.br</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="step-grid">
    <div class="step-card">
        <strong>Passo 1</strong>
        <span>Escolha o modo de entrada: planilha ou manual.</span>
    </div>
    <div class="step-card">
        <strong>Passo 2</strong>
        <span>Carregue os dados e rode a análise.</span>
    </div>
    <div class="step-card">
        <strong>Passo 3</strong>
        <span>Veja ranking, exporte e simule ações.</span>
    </div>
</div>
""", unsafe_allow_html=True)

def validar_dataframe(df_base):
    colunas_esperadas = {
        "INSTALACAO", "REQUERIDA", "INJETADA",
        "REVERSA", "CONSUMO", "ILUMINACAO_PUBLICA"
    }
    faltantes = colunas_esperadas - set(df_base.columns)
    if faltantes:
        return False, f"Faltam colunas obrigatórias: {', '.join(sorted(faltantes))}"

    df_val = df_base.copy()
    colunas_numericas = ["REQUERIDA", "INJETADA", "REVERSA", "CONSUMO", "ILUMINACAO_PUBLICA"]
    for col in colunas_numericas:
        df_val[col] = pd.to_numeric(df_val[col], errors="coerce")
        if df_val[col].isna().any():
            return False, f"A coluna {col} possui valores inválidos."
        if (df_val[col] < 0).any():
            return False, f"A coluna {col} não pode ter valores negativos."

    if df_val["INSTALACAO"].astype(str).str.strip().eq("").any():
        return False, "A coluna INSTALACAO possui valores vazios."

    if df_val["INSTALACAO"].astype(str).duplicated().any():
        return False, "Existem instalações duplicadas."

    return True, "ok"


def _to_float_br(valor_txt):
    txt = re.sub(r"[^\d,\.\-]", "", str(valor_txt).strip())
    if not txt:
        return None

    # Regras para lidar com formatos mistos de milhar/decimal vindos do PDF.
    if "," in txt and "." in txt:
        if txt.rfind(",") > txt.rfind("."):
            # Ex.: 1.234,56
            txt = txt.replace(".", "").replace(",", ".")
        else:
            # Ex.: 1,234.56
            txt = txt.replace(",", "")
    elif "," in txt:
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+", txt) or re.fullmatch(r"-?\d+,\d{3}", txt):
            # Ex.: 50,065 -> 50065
            txt = txt.replace(",", "")
        elif re.fullmatch(r"-?\d+,\d{1,2}", txt):
            # Ex.: 123,45 -> 123.45
            txt = txt.replace(",", ".")
        else:
            txt = txt.replace(",", "")
    elif "." in txt:
        if re.fullmatch(r"-?\d{1,3}(\.\d{3})+", txt) or re.fullmatch(r"-?\d+\.\d{3}", txt):
            # Ex.: 50.065 -> 50065
            txt = txt.replace(".", "")
    try:
        return float(txt)
    except ValueError:
        return None


def _extrair_serie_metricas(texto_norm, label, proximos_labels):
    idx = texto_norm.find(label)
    if idx == -1:
        return []

    trecho = texto_norm[idx: idx + 450]
    if ":" in trecho:
        trecho = trecho.split(":", 1)[1]

    fim = len(trecho)
    for prox in proximos_labels:
        pos = trecho.find(prox)
        if pos != -1:
            fim = min(fim, pos)
    trecho = trecho[:fim]

    nums = re.findall(r"\d{1,3}(?:\.\d{3})*(?:,\d+)?", trecho)
    serie = []
    for n in nums:
        val = _to_float_br(n)
        if val is not None:
            serie.append(val)
    return serie


def _extrair_instalacao_fiscal(texto_norm):
    # 1) Caso direto: label seguido de número.
    padroes_diretos = [
        r"Instala[çc][aã]o\s*Fiscal\s*:?\s*(\d{8,12})",
        r"Inst\.?\s*Fiscal\s*:?\s*(\d{8,12})",
    ]
    for padrao in padroes_diretos:
        m = re.search(padrao, texto_norm, flags=re.IGNORECASE)
        if m:
            return m.group(1)

    # 2) Caso com label e valor separado por outros textos.
    ancora_ini = re.search(r"Instala[çc][aã]o\s*Fiscal", texto_norm, flags=re.IGNORECASE)
    ancora_fim = re.search(r"Energia\s*Reversa|Consumo\s*Clientes", texto_norm, flags=re.IGNORECASE)
    if ancora_ini:
        ini = ancora_ini.start()
        fim = ancora_fim.start() if (ancora_fim and ancora_fim.start() > ini) else min(len(texto_norm), ini + 900)
        trecho = texto_norm[ini:fim]
        m = re.search(r"\b\d{10}\b", trecho)
        if m:
            return m.group(0)
        m = re.search(r"\b\d{8,12}\b", trecho)
        if m:
            return m.group(0)

    # 3) Fallback: procura no bloco inicial por padrão de instalação (10 dígitos).
    bloco_inicial = texto_norm[:2500]
    candidatos_10 = re.findall(r"\b\d{10}\b", bloco_inicial)
    if candidatos_10:
        return candidatos_10[0]

    # 4) Último fallback: qualquer id de 8 a 12 dígitos no início.
    candidatos = re.findall(r"\b\d{8,12}\b", bloco_inicial)
    if candidatos:
        return candidatos[0]

    return ""


def extrair_dados_pdf(pdf_bytes):
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        texto = " ".join([(pg.extract_text() or "") for pg in reader.pages[:4]])
    except Exception as exc:
        return {"ok": False, "erro": f"Falha ao ler PDF: {exc}"}

    texto_norm = re.sub(r"\s+", " ", texto)

    refs = []
    bloco_refs = ""
    m_ini = re.search(r"Situa[çc][aã]o Inicial", texto_norm, flags=re.IGNORECASE)
    m_fim = re.search(r"Instala[çc][aã]o Fiscal", texto_norm, flags=re.IGNORECASE)
    if m_ini and m_fim and m_fim.start() > m_ini.start():
        bloco_refs = texto_norm[m_ini.start():m_fim.start()]
    else:
        bloco_refs = texto_norm[:1200]

    # Captura mês/ano aceitando quebra no ano (ex.: Feb/20 26) e também Média.
    refs_detectadas = []
    for mes, ano in re.findall(r"\b([A-Za-z]{3,4})\s*/\s*(\d{2}\s*\d{2}|\d{2,4})\b", bloco_refs, flags=re.IGNORECASE):
        ano_limpo = re.sub(r"\s+", "", ano)
        if len(ano_limpo) == 2:
            ano_limpo = f"20{ano_limpo}"
        ref = f"{mes.title()}/{ano_limpo}"
        if ref not in refs_detectadas:
            refs_detectadas.append(ref)
    if re.search(r"M[eé]dia", bloco_refs, flags=re.IGNORECASE):
        refs_detectadas.append("Média")

    labels = [
        "Requerida Trafo (kWh)",
        "Injetada GDIS (kWh)",
        "Energia Reversa (kWh)",
        "Consumo Clientes (kWh)",
        "IP Estimada (kWh)",
    ]

    metricas = {
        "REQUERIDA": _extrair_serie_metricas(texto_norm, labels[0], labels[1:]),
        "INJETADA": _extrair_serie_metricas(texto_norm, labels[1], labels[2:]),
        "REVERSA": _extrair_serie_metricas(texto_norm, labels[2], labels[3:]),
        "CONSUMO": _extrair_serie_metricas(texto_norm, labels[3], labels[4:]),
        "ILUMINACAO_PUBLICA": _extrair_serie_metricas(texto_norm, labels[4], ["Referência", "Perda (KWh)"]),
    }

    # Define a base real de colunas e força padrão do PDF: 3 meses + Média (quando disponível).
    tamanhos_validos = [len(v) for v in metricas.values() if v]
    alvo = min(tamanhos_validos) if tamanhos_validos else 0
    if alvo >= 4:
        alvo = 4

    meses_detectados = [r for r in refs_detectadas if r != "Média"]
    refs = []
    if alvo > 0:
        meses_necessarios = max(0, alvo - 1)
        refs.extend(meses_detectados[:meses_necessarios])
        while len(refs) < meses_necessarios:
            refs.append(f"Mês {len(refs) + 1}")
        refs.append("Média")

    # Evita números extras que podem aparecer após o bloco principal do resumo.
    for campo in metricas:
        if len(metricas[campo]) >= alvo:
            metricas[campo] = metricas[campo][:alvo]

    instalacao = _extrair_instalacao_fiscal(texto_norm)

    if not instalacao:
        return {"ok": False, "erro": "Não foi possível identificar a Instalação Fiscal no PDF."}

    if not all(metricas[chave] for chave in metricas):
        return {"ok": False, "erro": "Não foi possível extrair todas as séries necessárias do PDF."}

    if not refs:
        tam_max = max(len(v) for v in metricas.values())
        if tam_max >= 4:
            refs = ["Mês 1", "Mês 2", "Mês 3", "Média"]
        elif tam_max > 1:
            refs = [f"Mês {i+1}" for i in range(tam_max - 1)] + ["Média"]
        else:
            refs = ["Média"]

    return {
        "ok": True,
        "instalacao": instalacao,
        "refs": refs,
        "metricas": metricas,
    }


def montar_df_a_partir_pdf(pdf_info, referencia_escolhida):
    refs = pdf_info["refs"]
    metricas = pdf_info["metricas"]

    if referencia_escolhida in refs:
        idx = refs.index(referencia_escolhida)
    else:
        idx = len(refs) - 1

    linha = {"INSTALACAO": str(pdf_info["instalacao"]).strip()}
    for campo, serie in metricas.items():
        if not serie:
            linha[campo] = 0.0
        elif idx < len(serie):
            linha[campo] = float(serie[idx])
        else:
            linha[campo] = float(serie[-1])

    df_pdf = pd.DataFrame([linha])
    for col in ["REQUERIDA", "INJETADA", "REVERSA", "CONSUMO", "ILUMINACAO_PUBLICA"]:
        df_pdf[col] = pd.to_numeric(df_pdf[col], errors="coerce").fillna(0.0)
    return df_pdf


entrada_ok = st.session_state.df is not None or not st.session_state.df_manual.empty
analise_ok = st.session_state.df_res is not None

st.markdown(
    f"""
    <div class="status-grid">
        <div class="status-card">
            <strong>Etapa 1</strong>
            <span class="{'status-ok' if entrada_ok else 'status-wait'}">{'Entrada concluída' if entrada_ok else 'Aguardando entrada'}</span>
        </div>
        <div class="status-card">
            <strong>Etapa 2</strong>
            <span class="{'status-ok' if analise_ok else 'status-wait'}">{'Análise concluída' if analise_ok else 'Aguardando análise'}</span>
        </div>
        <div class="status-card">
            <strong>Etapa 3</strong>
            <span class="{'status-ok' if analise_ok else 'status-wait'}">{'Simulação disponível' if analise_ok else 'Bloqueada até análise'}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

if st.session_state.pending_step is not None:
    st.session_state.active_step = st.session_state.pending_step
    st.session_state.pending_step = None

selected_step = st.radio(
    "Navegação por etapa",
    ["1. Entrada", "2. Resultados", "3. Simulação"],
    horizontal=True,
    key="active_step"
)

if selected_step == "1. Entrada":
    st.markdown('<p class="section-label">INPUT DOS DADOS</p>', unsafe_allow_html=True)
    st.markdown('<p class="helper-text">Escolha abaixo como deseja inserir os dados para cálculo.</p>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="module-shell">
            <p class="module-title">Módulo de Entrada</p>
            <p class="module-subtitle">Defina o modo de coleta e preencha os dados operacionais.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    modo = st.radio("Modo de entrada", ["Upload de Arquivo", "Manual"], horizontal=True)

    if modo == "Upload de Arquivo":
        st.markdown("""
        <div class="info-box">
            <strong>Arquivos aceitos</strong><br/>
            Excel (.xlsx) ou PDF de Medição Fiscal.<br/>
            <br/>
            <strong>Colunas esperadas para análise</strong><br/>
            INSTALACAO &nbsp;·&nbsp; REQUERIDA &nbsp;·&nbsp; INJETADA &nbsp;·&nbsp;
            REVERSA &nbsp;·&nbsp; CONSUMO &nbsp;·&nbsp; ILUMINACAO_PUBLICA
        </div>
        """, unsafe_allow_html=True)

        file = st.file_uploader("Arquivo (.xlsx ou .pdf)", type=["xlsx", "pdf"])
        if file:
            nome = file.name.lower()
            if nome.endswith(".xlsx"):
                df_upload = pd.read_excel(file)
                df_upload.columns = df_upload.columns.str.strip().str.upper()
                ok, msg = validar_dataframe(df_upload)

                if not ok:
                    st.error(msg)
                    st.session_state.df = None
                    st.session_state.df_res = None
                    st.session_state.run_analysis_requested = False
                else:
                    st.success(f"Arquivo carregado com sucesso. Registros encontrados: {len(df_upload)}")
                    st.session_state.df = df_upload
                    st.session_state.df_res = None
                    with st.expander("Pré-visualizar dados carregados"):
                        st.dataframe(df_upload.head(10), use_container_width=True)

                    if st.button("Rodar análise", key="btn_rodar_upload", use_container_width=True, type="primary"):
                        st.session_state.run_analysis_requested = True
                        st.rerun()
            else:
                pdf_info = extrair_dados_pdf(file.getvalue())
                if not pdf_info["ok"]:
                    st.error(pdf_info["erro"])
                else:
                    refs = pdf_info["refs"]
                    ref_padrao = "Média" if "Média" in refs else refs[-1]
                    idx_padrao = refs.index(ref_padrao)
                    ref_escolhida = st.selectbox(
                        "Referência para extração dos dados do PDF",
                        refs,
                        index=idx_padrao,
                        key="pdf_ref_escolhida"
                    )

                    df_pdf = montar_df_a_partir_pdf(pdf_info, ref_escolhida)
                    ok, msg = validar_dataframe(df_pdf)
                    if not ok:
                        st.error(msg)
                    else:
                        st.success(
                            f"PDF lido com sucesso para instalação {df_pdf.iloc[0]['INSTALACAO']} usando referência: {ref_escolhida}"
                        )
                        with st.expander("Pré-visualizar dados extraídos do PDF"):
                            st.dataframe(df_pdf, use_container_width=True)

                        st.session_state.df = df_pdf
                        st.session_state.df_res = None

                        if st.button("Rodar análise", key="btn_rodar_upload_pdf", use_container_width=True, type="primary"):
                            st.session_state.run_analysis_requested = True
                            st.rerun()

    else:
        st.markdown('<p class="section-label">Nova instalação</p>', unsafe_allow_html=True)
        st.markdown('<p class="helper-text">Preencha os campos e clique em adicionar para montar sua base.</p>', unsafe_allow_html=True)

        st.markdown(
            f'<span class="counter-chip">Instalações inseridas: {len(st.session_state.df_manual)}</span>',
            unsafe_allow_html=True
        )

        with st.form("form_nova_instalacao", clear_on_submit=False):
            col1, col2 = st.columns(2)

            with col1:
                inst = st.text_input("Instalação MF", placeholder="Ex: 123456789")
                requerida = st.number_input("Requerida", min_value=0.0, step=500.0, key="in_req")
                injetada = st.number_input("Injetada", min_value=0.0, step=500.0, key="in_inj")

            with col2:
                reversa = st.number_input("Reversa", min_value=0.0, step=500.0, key="in_rev")
                consumo = st.number_input("Consumo", min_value=0.0, step=500.0, key="in_con")
                iluminacao = st.number_input("Iluminação Pública", min_value=0.0, step=500.0, key="in_ilu")

            col_add, col_clear = st.columns(2)
            with col_add:
                adicionar = st.form_submit_button("Adicionar instalação")
            with col_clear:
                limpar = st.form_submit_button("Limpar tudo")

        if adicionar:
            inst_txt = str(inst).strip()
            if not inst_txt:
                st.warning("Informe a instalação antes de adicionar.")
            elif not st.session_state.df_manual.empty and inst_txt in st.session_state.df_manual["INSTALACAO"].astype(str).values:
                st.warning("Esta instalação já existe na lista manual.")
            else:
                nova = pd.DataFrame([{
                    "INSTALACAO": inst_txt,
                    "REQUERIDA": requerida,
                    "INJETADA": injetada,
                    "REVERSA": reversa,
                    "CONSUMO": consumo,
                    "ILUMINACAO_PUBLICA": iluminacao
                }])
                st.session_state.df_manual = pd.concat([st.session_state.df_manual, nova], ignore_index=True)
                st.session_state.df_res = None
                st.success("Instalação adicionada à lista.")

        if limpar:
            st.session_state.df_manual = st.session_state.df_manual.iloc[0:0]
            st.session_state.df = None
            st.session_state.df_res = None
            st.session_state.run_analysis_requested = False
            st.info("Lista manual limpa.")

        if not st.session_state.df_manual.empty:
            st.markdown('<p class="section-label">Instalações inseridas</p>', unsafe_allow_html=True)

            editor_df = st.data_editor(
                st.session_state.df_manual,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
                key="manual_editor"
            )

            editor_df.columns = editor_df.columns.str.strip().str.upper()

            st.markdown('<p class="helper-text">Gerencie a base manual e rode a análise.</p>', unsafe_allow_html=True)

            opcoes_inst = editor_df["INSTALACAO"].astype(str).tolist()
            centro_esq, centro, centro_dir = st.columns([1, 1.8, 1])
            with centro:
                inst_remover = st.selectbox("Remover instalação", opcoes_inst, key="inst_remover")

            b_remove, b_run = st.columns(2)

            with b_remove:
                if st.button("Remover selecionada", key="btn_remover", use_container_width=True, type="secondary"):
                    st.session_state.df_manual = editor_df[
                        editor_df["INSTALACAO"].astype(str) != str(inst_remover)
                    ].reset_index(drop=True)
                    st.session_state.df_res = None
                    st.session_state.run_analysis_requested = False
                    st.success("Instalação removida.")

            with b_run:
                if st.button("Rodar análise", key="btn_rodar_manual", use_container_width=True, type="primary"):
                    base_manual = editor_df.copy()
                    ok, msg = validar_dataframe(base_manual)
                    if ok:
                        st.session_state.df_manual = base_manual
                        st.session_state.df = base_manual.copy()
                        st.session_state.df_res = None
                        st.session_state.run_analysis_requested = True
                        st.rerun()
                    else:
                        st.error(msg)

# =========================
# PROCESSAMENTO
# =========================
if (
    st.session_state.df is not None
    and st.session_state.df_res is None
    and st.session_state.run_analysis_requested
):

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
            ("Exclusoes", -100),
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
    st.session_state.run_analysis_requested = False
    st.session_state.pending_step = "2. Resultados"
    st.rerun()

# =========================
# GANHOS PADRÃO (BASE)
# =========================
ganho_inc  = 150.0
ganho_c100 = 120.0
ganho_exc  = 100.0
ganho_c200 = 100.0
ganho_c300 = 30.0


# =========================
# RESULTADOS
# =========================
if selected_step == "2. Resultados":
    if st.session_state.df_res is None:
        st.info("A etapa de resultados será habilitada após rodar a análise na aba Entrada.")
    else:
        df_res = st.session_state.df_res

        if df_res.empty:
            st.warning(
                "A análise foi concluída, mas nenhum resultado válido foi gerado. "
                "Revise os dados de entrada e os critérios de processamento na aba Entrada."
            )
        else:
            st.markdown('<p class="section-label">Visão Geral</p>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.metric("Instalações", len(df_res))
            c2.metric("Perda média (%)", f"{df_res['PERDA_%'].mean():.2f}")
            c3.metric("Perda total (kWh)", f"{df_res['PERDA_(kWh)'].sum():,.2f}")

            st.markdown("---")
            st.markdown('<p class="section-label">Ranking por Perda</p>', unsafe_allow_html=True)
            st.markdown('<p class="helper-text">Instalações com maior % de perda aparecem no topo para priorização.</p>', unsafe_allow_html=True)
            st.dataframe(df_res.sort_values("PERDA_%", ascending=False), use_container_width=True)

            st.markdown('<p class="section-label">Exportar</p>', unsafe_allow_html=True)
            st.download_button(
                "Baixar resultado (.csv)",
                df_res.to_csv(index=False),
                "resultado.csv",
                mime="text/csv"
            )

# =========================
# SIMULAÇÃO
# =========================
if selected_step == "3. Simulação":
    if st.session_state.df_res is None:
        st.warning("A simulação fica disponível após a conclusão da análise na aba Resultados.")
    else:
        df_res = st.session_state.df_res
        df = st.session_state.df

        st.markdown('<p class="section-label">Simulação de Ações</p>', unsafe_allow_html=True)
        st.markdown('<p class="helper-text">Escolha uma instalação e simule o impacto das ações no atingimento da meta.</p>', unsafe_allow_html=True)

        st.markdown(
            """
            <div class="module-shell">
                <p class="module-title">Módulo de Simulação</p>
                <p class="module-subtitle">Ajuste as ações e acompanhe em tempo real o progresso para a meta.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        inst_sel = st.selectbox("Instalação", df_res["INSTALACAO"])
        base = df[df["INSTALACAO"] == inst_sel].iloc[0]

        perda = (
            base["REQUERIDA"] + base["INJETADA"]
            - base["REVERSA"] - base["CONSUMO"]
            - base["ILUMINACAO_PUBLICA"]
        )
        meta = perda - df_res[df_res["INSTALACAO"] == inst_sel]["RED_NECESSÁRIA"].iloc[0]

        modo_ganho = st.radio(
            "Modo de cálculo do ganho",
            ["Valor médio", "Customizar individualmente"],
            horizontal=True,
            key="sim_modo_ganho",
            index=0 if st.session_state.sim_persist_modo == "Valor médio" else 1
        )
        st.session_state.sim_persist_modo = modo_ganho

        def calcular_ganho(qtd, valor_padrao, acao_key, rotulo):
            if qtd == 0:
                return 0

            if modo_ganho == "Valor médio":
                valor_inicial = float(st.session_state.get(f"sim_persist_{acao_key}_medio", valor_padrao))
                valor = st.number_input(
                    f"{rotulo} (kWh por ação)",
                    min_value=0.0,
                    value=valor_inicial,
                    key=f"sim_{acao_key}_medio"
                )
                st.session_state[f"sim_persist_{acao_key}_medio"] = float(valor)
                return qtd * valor
            ganhos = []
            with st.expander(f"Detalhar {rotulo}"):
                for i in range(qtd):
                    persist_key = f"sim_persist_{acao_key}_{i}"
                    valor_inicial = float(st.session_state.get(persist_key, valor_padrao))
                    val = st.number_input(
                        f"{rotulo} #{i+1} (kWh)",
                        min_value=0.0,
                        value=valor_inicial,
                        key=f"sim_{acao_key}_{i}",
                        step=20.0
                    )
                    st.session_state[persist_key] = float(val)
                    ganhos.append(val)
            return sum(ganhos)

        def limpar_codigos_simulacao():
            st.session_state["sim_inc"] = 0
            st.session_state["sim_c100"] = 0
            st.session_state["sim_exc"] = 0
            st.session_state["sim_c200"] = 0
            st.session_state["sim_c300"] = 0
            st.session_state["sim_persist_inc"] = 0
            st.session_state["sim_persist_c100"] = 0
            st.session_state["sim_persist_exc"] = 0
            st.session_state["sim_persist_c200"] = 0
            st.session_state["sim_persist_c300"] = 0
            st.session_state["sim_persist_modo"] = "Valor médio"

            padroes = {
                "inc": ganho_inc,
                "c100": ganho_c100,
                "exc": ganho_exc,
                "c200": ganho_c200,
                "c300": ganho_c300,
            }
            for acao_key, valor_padrao in padroes.items():
                st.session_state[f"sim_{acao_key}_medio"] = float(valor_padrao)
                st.session_state[f"sim_persist_{acao_key}_medio"] = float(valor_padrao)

            for key in list(st.session_state.keys()):
                if key.startswith("sim_inc_") and key != "sim_inc_medio":
                    del st.session_state[key]
                if key.startswith("sim_c100_") and key != "sim_c100_medio":
                    del st.session_state[key]
                if key.startswith("sim_exc_") and key != "sim_exc_medio":
                    del st.session_state[key]
                if key.startswith("sim_c200_") and key != "sim_c200_medio":
                    del st.session_state[key]
                if key.startswith("sim_c300_") and key != "sim_c300_medio":
                    del st.session_state[key]
                if key.startswith("sim_persist_inc_") and key != "sim_persist_inc_medio":
                    del st.session_state[key]
                if key.startswith("sim_persist_c100_") and key != "sim_persist_c100_medio":
                    del st.session_state[key]
                if key.startswith("sim_persist_exc_") and key != "sim_persist_exc_medio":
                    del st.session_state[key]
                if key.startswith("sim_persist_c200_") and key != "sim_persist_c200_medio":
                    del st.session_state[key]
                if key.startswith("sim_persist_c300_") and key != "sim_persist_c300_medio":
                    del st.session_state[key]

        if st.session_state.sim_clear_requested:
            limpar_codigos_simulacao()
            st.session_state.sim_clear_requested = False

        st.markdown('<p class="action-hint">Informe a quantidade de ações planejadas em cada categoria.</p>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            inc = st.number_input("Inclusões", min_value=0, value=int(st.session_state.sim_persist_inc), key="sim_inc")
            c100 = st.number_input("Cod 100", min_value=0, value=int(st.session_state.sim_persist_c100), key="sim_c100")
            c200 = st.number_input("Cod 200", min_value=0, value=int(st.session_state.sim_persist_c200), key="sim_c200")
        with col2:
            exc = st.number_input("Exclusões", min_value=0, value=int(st.session_state.sim_persist_exc), key="sim_exc")
            c300 = st.number_input("Cod 300", min_value=0, value=int(st.session_state.sim_persist_c300), key="sim_c300")

        st.session_state.sim_persist_inc = int(inc)
        st.session_state.sim_persist_c100 = int(c100)
        st.session_state.sim_persist_c200 = int(c200)
        st.session_state.sim_persist_exc = int(exc)
        st.session_state.sim_persist_c300 = int(c300)

        if st.button("Limpar códigos", key="btn_limpar_codigos", type="secondary"):
            st.session_state.sim_clear_requested = True
            st.rerun()

        ganho_total = (
            calcular_ganho(inc, ganho_inc, "inc", "Inclusões") +
            calcular_ganho(c100, ganho_c100, "c100", "Cod 100") -
            calcular_ganho(exc, ganho_exc, "exc", "Exclusões") +
            calcular_ganho(c200, ganho_c200, "c200", "Cod 200") +
            calcular_ganho(c300, ganho_c300, "c300", "Cod 300")
        )

        perda_proj = perda - ganho_total
        reducao_necessaria = max(0.0, perda - meta)
        reducao_obtida = max(0.0, perda - perda_proj)
        if reducao_necessaria == 0:
            atingimento = 100.0
        else:
            atingimento = max(0.0, min(100.0, (reducao_obtida / reducao_necessaria) * 100))

        if atingimento < 60:
            classe_badge = "sim-badge sim-badge-critico"
            texto_badge = "Crítico"
            cor_barra = "#ef4444"
        elif atingimento < 90:
            classe_badge = "sim-badge sim-badge-atencao"
            texto_badge = "Atenção"
            cor_barra = "#f59e0b"
        else:
            classe_badge = "sim-badge sim-badge-ok"
            texto_badge = "Meta próxima/atingida"
            cor_barra = "#22c55e"

        st.markdown(f'<div class="{classe_badge}">Status da simulação: {texto_badge}</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="sim-progress-wrap">
                <div class="sim-progress-head">
                    <span>Progresso para meta da instalação selecionada</span>
                    <strong>{atingimento:.1f}%</strong>
                </div>
                <div class="sim-progress-track">
                    <div class="sim-progress-fill" style="width:{atingimento:.1f}%; background:{cor_barra};"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<p class="section-label">Resultado projetado</p>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        r1.metric("Ganho", f"{ganho_total:.2f}")
        r2.metric("Perda Projetada", f"{perda_proj:.2f}")
        r3.metric("Meta", f"{meta:.2f}")

        if perda_proj <= meta:
            st.markdown('<div class="sim-result-ok">Meta atingida</div>', unsafe_allow_html=True)
        else:
            falta = perda_proj - meta
            st.markdown(
                f'<div class="sim-result-fail">Faltam {falta:.2f} kWh para atingir a meta</div>',
                unsafe_allow_html=True
            )

