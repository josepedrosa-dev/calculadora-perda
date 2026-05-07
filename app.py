import io
import math
import re

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader

st.set_page_config(
    page_title="Calculadora de Recuperação de Energia",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _to_float_br(valor_txt):
    txt = re.sub(r"[^\d,\.\-]", "", str(valor_txt).strip())
    if not txt:
        return None

    if "," in txt and "." in txt:
        if txt.rfind(",") > txt.rfind("."):
            txt = txt.replace(".", "").replace(",", ".")
        else:
            txt = txt.replace(",", "")
    elif "," in txt:
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+", txt) or re.fullmatch(r"-?\d+,\d{3}", txt):
            txt = txt.replace(",", "")
        elif re.fullmatch(r"-?\d+,\d{1,2}", txt):
            txt = txt.replace(",", ".")
        else:
            txt = txt.replace(",", "")
    elif "." in txt:
        if re.fullmatch(r"-?\d{1,3}(\.\d{3})+", txt) or re.fullmatch(r"-?\d+\.\d{3}", txt):
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
    for padrao in [
        r"Instala[çc][aã]o\s*Fiscal\s*:?\s*(\d{8,12})",
        r"Inst\.?\s*Fiscal\s*:?\s*(\d{8,12})",
    ]:
        m = re.search(padrao, texto_norm, flags=re.IGNORECASE)
        if m:
            return m.group(1)

    trecho = texto_norm[:2500]
    candidatos = re.findall(r"\b\d{8,12}\b", trecho)
    return candidatos[0] if candidatos else ""


def extrair_dados_pdf_text(texto):
    texto_norm = re.sub(r"\s+", " ", texto)

    bloco_refs = texto_norm[:1200]
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

    instalacao = _extrair_instalacao_fiscal(texto_norm)
    if not instalacao:
        return {"ok": False, "erro": "Não foi possível identificar a Instalação Fiscal no PDF."}
    if not all(metricas[chave] for chave in metricas):
        return {"ok": False, "erro": "Não foi possível extrair todas as séries necessárias do PDF."}

    alvo = min(len(v) for v in metricas.values() if v)
    alvo = min(alvo, 4)
    refs = [r for r in refs_detectadas if r != "Média"][: max(0, alvo - 1)]
    while len(refs) < max(0, alvo - 1):
        refs.append(f"Mês {len(refs) + 1}")
    refs.append("Média")

    for campo in metricas:
        metricas[campo] = metricas[campo][:alvo]

    return {
        "ok": True,
        "instalacao": instalacao,
        "refs": refs,
        "metricas": metricas,
    }


def montar_df_a_partir_pdf(pdf_info, referencia_escolhida):
    refs = pdf_info["refs"]
    idx = refs.index(referencia_escolhida) if referencia_escolhida in refs else len(refs) - 1

    linha = {"INSTALACAO": str(pdf_info["instalacao"]).strip()}
    for campo, serie in pdf_info["metricas"].items():
        linha[campo] = float(serie[idx]) if idx < len(serie) else float(serie[-1])

    df_pdf = pd.DataFrame([linha])
    for col in ["REQUERIDA", "INJETADA", "REVERSA", "CONSUMO", "ILUMINACAO_PUBLICA"]:
        df_pdf[col] = pd.to_numeric(df_pdf[col], errors="coerce").fillna(0.0)
    return df_pdf


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --blue-900: #0f2740;
    --blue-700: #1f4f7a;
    --blue-600: #2d648f;
    --green-500: #2f9e79;
    --amber-500: #b45309;
    --red-500: #b91c1c;

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

* { font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; }

.stApp {
    background: linear-gradient(180deg, var(--bg-primary) 0%, var(--gray-50) 100%);
    color: var(--text-primary);
}

.block-container {
    padding: 2rem 1.5rem 4rem;
    max-width: 1120px;
}

.app-header {
    background: linear-gradient(135deg, var(--blue-900) 0%, var(--blue-700) 100%);
    border-radius: 24px;
    padding: 2.4rem 2rem 1.9rem;
    margin-bottom: 1.4rem;
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

.app-header h1,
.app-header p,
[data-testid="stMarkdownContainer"] .app-header h1,
[data-testid="stMarkdownContainer"] .app-header p {
    color: #ffffff !important;
}

.app-header h1 {
    margin: 0 0 0.45rem;
    font-size: clamp(1.72rem, 5vw, 2.22rem);
    font-weight: 700;
}

.app-header p {
    margin: 0;
    font-size: 0.98rem;
}

.step-grid,
.status-grid,
.results-grid,
.sim-grid {
    display: grid;
    gap: 0.75rem;
}

.step-grid,
.status-grid,
.results-grid,
.sim-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
}

.step-grid { margin: 0.45rem 0 1.1rem; }
.status-grid { margin: 0.25rem 0 1rem; }
.results-grid,
.sim-grid { margin: 0.9rem 0 1rem; }

.step-card,
.status-card,
.results-card,
.sim-card {
    background: var(--bg-card);
    border: 1px solid var(--gray-300);
    border-radius: 14px;
    padding: 0.82rem 0.95rem;
    box-shadow: 0 6px 16px -10px rgba(51, 75, 97, 0.35);
}

.step-card strong,
.status-card strong,
.results-card span,
.sim-card span {
    display: block;
    color: var(--gray-700);
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.18rem;
}

.step-card span,
.results-note,
.helper-text,
.module-subtitle,
.sim-control-note {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.status-ok { color: #166534; font-weight: 700; }
.status-wait { color: var(--amber-500); font-weight: 700; }

.section-label {
    font-size: 0.87rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    color: var(--blue-700);
    margin: 2rem 0 0.7rem;
}

.helper-text { margin: 0.15rem 0 0.9rem; }

.module-shell,
.results-shell,
.sim-shell,
.info-box,
.results-table-shell,
.export-shell,
.sim-control-shell,
.sim-progress-wrap {
    background: var(--bg-card);
    border: 1px solid var(--gray-300);
    border-radius: 16px;
    padding: 0.88rem 0.96rem;
}

.module-shell,
.results-shell,
.sim-shell {
    border-radius: 18px;
    box-shadow: 0 10px 20px -16px rgba(16, 39, 61, 0.42);
    margin-bottom: 0.9rem;
}

.info-box,
.export-shell,
.sim-control-shell {
    background: linear-gradient(135deg, #f4fafc, #eef6fb);
}

.module-title {
    margin: 0;
    color: var(--blue-700);
    font-size: 1.01rem;
    font-weight: 700;
}

.module-subtitle {
    margin: 0.22rem 0 0;
}

.counter-chip {
    display: inline-block;
    background: #e8f1f8;
    color: var(--blue-700);
    border: 1px solid #c5d9ea;
    border-radius: 999px;
    padding: 0.28rem 0.7rem;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.6rem;
}

.results-card strong,
.sim-card strong {
    color: var(--text-primary);
    font-size: 1.18rem;
    font-weight: 700;
}

.results-table-shell {
    padding: 0.64rem;
    margin-top: 0.62rem;
}

.sim-control-note {
    margin: 0.28rem 0 0;
}

.action-hint {
    margin: 0.2rem 0 0.7rem;
    color: var(--text-secondary);
    font-size: 0.88rem;
}

.sim-badge {
    display: inline-block;
    border-radius: 999px;
    padding: 0.32rem 0.72rem;
    font-size: 0.8rem;
    font-weight: 700;
    margin-bottom: 0.62rem;
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

.sim-progress-wrap { margin-bottom: 0.85rem; }

.sim-progress-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: var(--gray-700);
    font-size: 0.83rem;
    margin-bottom: 0.48rem;
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

.sim-result-ok {
    background: linear-gradient(135deg, #def7ec, #c8efd9);
    border: 2px solid var(--green-500);
    color: #12503b;
    border-radius: 16px;
    padding: 0.74rem 0.95rem;
    font-weight: 600;
}

.sim-result-fail {
    background: linear-gradient(135deg, #fff1f1, #ffe2e2);
    border: 2px solid #ea6c6c;
    color: #8c1f1f;
    border-radius: 16px;
    padding: 0.74rem 0.95rem;
    font-weight: 600;
}

[data-testid="metric-container"] {
    background: var(--bg-card);
    border: 1px solid var(--gray-300);
    border-radius: 20px;
    padding: 1.55rem;
    box-shadow: 0 10px 18px -12px rgba(16, 39, 61, 0.35);
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

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    border-radius: 14px;
    border: 2px solid var(--border);
    background: var(--bg-card);
    color: var(--text-primary);
    padding: 0.86rem 1.1rem;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: var(--blue-600);
    box-shadow: 0 0 0 4px rgba(45, 100, 143, 0.14);
}

.stButton > button {
    background: #e8f1f8;
    color: var(--blue-700);
    border-radius: 14px;
    font-weight: 600;
    padding: 0.8rem 1.2rem;
    border: 1px solid #bfd4e6;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--blue-700), var(--blue-600));
    color: #ffffff;
    border: none;
}

.stButton > button[kind="secondary"] {
    background: #ffffff;
    color: #9a3412;
    border: 1px solid #fdba74;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #dff3ea, #cdeee0);
    color: #0f5132;
    border: 2px solid #8fd6b9;
    border-radius: 14px;
    font-weight: 600;
}

.stDownloadButton > button * {
    color: #0f5132 !important;
}

[data-testid="stDataFrame"] {
    border-radius: 18px;
    border: 1px solid var(--border);
}

[data-baseweb="radio"] label,
[data-testid="stAlertContentInfo"],
[data-testid="stAlertContentWarning"],
[data-testid="stAlertContentError"],
[data-testid="stAlertContentSuccess"] {
    color: var(--text-primary) !important;
}

@media (max-width: 768px) {
    .block-container { padding: 1.5rem 1rem 3rem; }
    .app-header { padding: 2rem 1.5rem 1.5rem; margin-bottom: 1.4rem; }
    .step-grid,
    .status-grid,
    .results-grid,
    .sim-grid { grid-template-columns: 1fr; }
}
</style>
""",
    unsafe_allow_html=True,
)


if "df_manual" not in st.session_state:
    st.session_state.df_manual = pd.DataFrame(
        columns=[
            "INSTALACAO",
            "REQUERIDA",
            "INJETADA",
            "REVERSA",
            "CONSUMO",
            "ILUMINACAO_PUBLICA",
        ]
    )
if "df" not in st.session_state:
    st.session_state.df = None
if "df_res" not in st.session_state:
    st.session_state.df_res = None
if "run_analysis_requested" not in st.session_state:
    st.session_state.run_analysis_requested = False
if "pending_tab_index" not in st.session_state:
    st.session_state.pending_tab_index = None
if "last_input_signature" not in st.session_state:
    st.session_state.last_input_signature = None

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


curva_lista = [
    0,
    0.88,
    1.4,
    1.84,
    2.22,
    2.58,
    2.91,
    3.23,
    3.53,
    3.82,
    4.09,
    4.36,
    4.62,
    4.87,
    5.12,
    5.36,
    5.6,
    5.83,
    6.05,
    6.27,
    6.49,
    6.71,
    6.92,
    7.12,
    7.33,
    7.53,
    7.73,
    7.93,
    8.12,
    8.31,
    8.5,
    8.69,
    8.87,
    9.06,
    9.24,
    9.42,
    9.6,
    9.77,
    9.95,
    10.12,
    10.29,
    10.47,
    10.63,
    10.8,
    10.97,
    11.13,
    11.3,
    11.46,
    11.62,
    11.78,
    11.94,
    12.1,
    12.26,
    12.41,
    12.57,
    12.72,
    12.88,
    13.03,
    13.18,
    13.33,
    13.48,
    13.63,
    13.78,
    13.93,
    14.07,
    14.22,
    14.37,
    14.51,
    14.65,
    14.8,
    14.94,
    15.08,
    15.22,
    15.36,
    15.5,
    15.64,
    15.78,
    15.92,
    16.05,
    16.19,
    16.33,
    16.46,
    16.6,
    16.73,
    16.87,
    17,
    17.13,
    17.26,
    17.4,
    17.53,
    17.66,
    17.79,
    17.92,
    18.05,
    18.18,
    18.31,
    18.43,
    18.56,
    18.69,
    18.81,
    18.94,
]
curva = {i: curva_lista[i] for i in range(len(curva_lista))}


st.markdown(
    """
<div class="app-header">
    <h1>Projeção de Recuperação de Energia</h1>
    <p>Calculadora de impacto operacional</p>
    <p>Desenvolvido por: José Pedrosa</p>
    <p>jose.peronico@equatorialenergia.com.br</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="step-grid">
    <div class="step-card">
        <strong>Passo 1</strong>
        <span>Escolha o modo de entrada: planilha, PDF ou manual.</span>
    </div>
    <div class="step-card">
        <strong>Passo 2</strong>
        <span>Rode a análise e priorize instalações por perda.</span>
    </div>
    <div class="step-card">
        <strong>Passo 3</strong>
        <span>Simule ações e acompanhe o atingimento da meta.</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


def validar_dataframe(df_base):
    colunas_esperadas = {
        "INSTALACAO",
        "REQUERIDA",
        "INJETADA",
        "REVERSA",
        "CONSUMO",
        "ILUMINACAO_PUBLICA",
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


@st.cache_data(show_spinner=False)
def carregar_excel_bytes(file_bytes):
    df = pd.read_excel(io.BytesIO(file_bytes))
    df.columns = df.columns.str.strip().str.upper()
    return df


@st.cache_data(show_spinner=False)
def extrair_dados_pdf_cached(pdf_bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    texto = " ".join([(pg.extract_text() or "") for pg in reader.pages[:4]])
    return extrair_dados_pdf_text(texto)


def extrair_dados_pdf(pdf_bytes):
    try:
        return extrair_dados_pdf_cached(pdf_bytes)
    except Exception as exc:
        return {"ok": False, "erro": f"Falha ao ler PDF: {exc}"}


def montar_tabela_referencias_pdf(pdf_info):
    linhas = []
    for idx, ref in enumerate(pdf_info["refs"]):
        linha = {"REFERENCIA": ref}
        for campo, serie in pdf_info["metricas"].items():
            if idx < len(serie):
                linha[campo] = float(serie[idx])
            else:
                linha[campo] = None
        linhas.append(linha)
    return pd.DataFrame(linhas)


def montar_export_resultado(df_res):
    df_export = df_res.copy()

    mapa_legado = {
        "PERDA_%_ATUAL": "PERDA_%",
        "PERDA_KWH": "PERDA_(kWh)",
        "RED_MIN_CURVA_KWH": "RED_MIN_EFICIÊNCIA",
        "RED_PARA_10%_KWH": "RED_PARA_ADEQUADA",
        "RED_NECESSARIA_KWH": "RED_NECESSÁRIA",
    }

    for novo, legado in mapa_legado.items():
        if novo in df_export.columns and legado not in df_export.columns:
            df_export[legado] = df_export[novo]

    return df_export


@st.cache_data(show_spinner=False)
def processar_resultados(df_input):
    df = df_input.copy()
    resultados = []

    for _, row in df.iterrows():
        total = row["REQUERIDA"] + row["INJETADA"]

        perda = (
            row["REQUERIDA"]
            + row["INJETADA"]
            - row["REVERSA"]
            - row["CONSUMO"]
            - row["ILUMINACAO_PUBLICA"]
        )
        perda = max(0, perda)

        if total == 0:
            continue

        # =========================
        # PERDA ATUAL
        # =========================
        
        perda_pct = perda / total
        faixa = int(round(perda_pct * 100, 0))
        faixa = min(max(faixa, 0), max(curva.keys()))
        meta_pp = curva.get(faixa, 0)

        perda_pct_alvo = max(0, (perda_pct * 100 - meta_pp) / 100)
        perda_alvo_curva_kwh = perda_pct_alvo * total

        red_min = perda - perda_alvo_curva_kwh
        perda_10_kwh = 0.10 * total
        red_10 = max(0, perda - perda_10_kwh)
        red_total = max(red_min, red_10)

        # =========================
        # PLANO DE AÇÃO
        # =========================
        ganho = 0
        acoes = [
            ("Inclusoes", 150),
            ("Cod100", 120),
            ("Exclusoes", -100),
            ("Cod200", 100),
            ("Cod300", 30),
        ]

        acoes.sort(key=lambda x: x[1], reverse=True)

        for _, impacto in acoes:
            if ganho >= red_total:
                break
            if impacto <= 0:
                continue
            qtd = math.ceil((red_total - ganho) / impacto)
            ganho += qtd * impacto

        perda_final = max(0, perda - ganho)

        resultados.append(
            {
                "INSTALACAO": row["INSTALACAO"],
                "PERDA_%_ATUAL": round(perda_pct * 100, 2),
                "PERDA_KWH": round(perda, 2),
                "PERDA_ALVO_CURVA_%": round(perda_pct_alvo * 100, 2),
                "PERDA_ALVO_CURVA_KWH": round(perda_alvo_curva_kwh, 2),
                "RED_MIN_CURVA_KWH": round(red_min, 2),
                "RED_PARA_10%_KWH": round(red_10, 2),
                "RED_NECESSARIA_KWH": round(red_total, 2),
                "PERDA_POS_ACAO_KWH": round(perda_final, 2),
            }
        )

    return pd.DataFrame(resultados)


def atualizar_base_entrada(df_novo, assinatura):
    """Atualiza a base e invalida resultados apenas quando a entrada mudar."""
    if st.session_state.last_input_signature != assinatura:
        st.session_state.df = df_novo
        st.session_state.df_res = None
        st.session_state.run_analysis_requested = False
        st.session_state.last_input_signature = assinatura


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
    unsafe_allow_html=True,
)

st.markdown('<p class="helper-text">Navegue entre as etapas pelas abas abaixo.</p>', unsafe_allow_html=True)
tab_entrada, tab_resultados, tab_simulacao = st.tabs(["1. Entrada", "2. Resultados", "3. Simulação"])

with tab_entrada:
    st.markdown('<p class="section-label">Input dos dados</p>', unsafe_allow_html=True)
    st.markdown('<p class="helper-text">Escolha como deseja montar a base para análise.</p>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="module-shell">
    <p class="module-title">Módulo de Entrada</p>
    <p class="module-subtitle">Validação robusta para garantir qualidade dos dados antes do cálculo.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    modo = st.radio("Modo de entrada", ["Upload de Arquivo", "Manual"], horizontal=True)

    if modo == "Upload de Arquivo":
        st.markdown(
            """
<div class="info-box">
    <strong>Arquivos aceitos</strong><br/>
    Excel (.xlsx) ou PDF de Medição Fiscal.<br/><br/>
    <strong>Colunas esperadas</strong><br/>
    INSTALACAO · REQUERIDA · INJETADA · REVERSA · CONSUMO · ILUMINACAO_PUBLICA
</div>
""",
            unsafe_allow_html=True,
        )

        file = st.file_uploader("Arquivo (.xlsx ou .pdf)", type=["xlsx", "pdf"])
        if file:
            file_bytes = file.getvalue()
            nome = file.name.lower()
            if nome.endswith(".xlsx"):
                df_upload = carregar_excel_bytes(file_bytes)
                ok, msg = validar_dataframe(df_upload)

                if not ok:
                    st.error(msg)
                    st.session_state.df = None
                    st.session_state.df_res = None
                    st.session_state.run_analysis_requested = False
                else:
                    st.success(f"Arquivo carregado com sucesso. Registros encontrados: {len(df_upload)}")
                    assinatura = f"excel::{file.name}::{len(df_upload)}::{','.join(df_upload.columns)}"
                    atualizar_base_entrada(df_upload, assinatura)

                    with st.expander("Pré-visualizar dados carregados"):
                        st.dataframe(df_upload.head(10), use_container_width=True)

                    if st.button("Rodar análise", key="btn_rodar_upload", use_container_width=True, type="primary"):
                        st.session_state.run_analysis_requested = True
                        st.session_state.pending_tab_index = 1
                        st.rerun()
            else:
                pdf_info = extrair_dados_pdf(file_bytes)
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
                        key="pdf_ref_escolhida",
                    )

                    st.markdown('<p class="helper-text">Conferência visual dos valores extraídos por referência.</p>', unsafe_allow_html=True)
                    st.dataframe(montar_tabela_referencias_pdf(pdf_info), use_container_width=True, hide_index=True)

                    df_pdf = montar_df_a_partir_pdf(pdf_info, ref_escolhida)
                    ok, msg = validar_dataframe(df_pdf)
                    if not ok:
                        st.error(msg)
                    else:
                        df_pdf["INSTALACAO"] = df_pdf["INSTALACAO"].astype(str)
                        st.success(
                            f"PDF lido com sucesso para instalação {df_pdf.iloc[0]['INSTALACAO']} usando referência: {ref_escolhida}"
                        )
                        with st.expander("Pré-visualizar dados extraídos do PDF"):
                            st.dataframe(df_pdf, use_container_width=True)

                        assinatura = f"pdf::{file.name}::{ref_escolhida}::{df_pdf.iloc[0]['INSTALACAO']}"
                        atualizar_base_entrada(df_pdf, assinatura)

                        if st.button("Rodar análise", key="btn_rodar_upload_pdf", use_container_width=True, type="primary"):
                            st.session_state.run_analysis_requested = True
                            st.session_state.pending_tab_index = 1
                            st.rerun()

    else:
        st.markdown('<p class="section-label">Nova instalação</p>', unsafe_allow_html=True)
        st.markdown('<p class="helper-text">Preencha os campos e clique em adicionar para montar sua base.</p>', unsafe_allow_html=True)
        st.markdown(
            f'<span class="counter-chip">Instalações inseridas: {len(st.session_state.df_manual)}</span>',
            unsafe_allow_html=True,
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
            elif (
                not st.session_state.df_manual.empty
                and inst_txt in st.session_state.df_manual["INSTALACAO"].astype(str).values
            ):
                st.warning("Esta instalação já existe na lista manual.")
            else:
                nova = pd.DataFrame(
                    [
                        {
                            "INSTALACAO": inst_txt,
                            "REQUERIDA": requerida,
                            "INJETADA": injetada,
                            "REVERSA": reversa,
                            "CONSUMO": consumo,
                            "ILUMINACAO_PUBLICA": iluminacao,
                        }
                    ]
                )
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
                key="manual_editor",
            )
            editor_df.columns = editor_df.columns.str.strip().str.upper()

            st.markdown('<p class="helper-text">Gerencie a base manual e rode a análise.</p>', unsafe_allow_html=True)

            opcoes_inst = editor_df["INSTALACAO"].astype(str).tolist()
            _, col_centro, _ = st.columns([1, 1.8, 1])
            with col_centro:
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
                        st.session_state.last_input_signature = f"manual::{len(base_manual)}"
                        st.session_state.pending_tab_index = 1
                        st.rerun()
                    else:
                        st.error(msg)


if (
    st.session_state.df is not None
    and st.session_state.df_res is None
    and st.session_state.run_analysis_requested
):
    df = st.session_state.df.copy()
    df.columns = df.columns.str.strip().str.upper()
    if "INSTALACAO" in df.columns:
        df["INSTALACAO"] = df["INSTALACAO"].astype(str)
    st.session_state.df = df

    st.session_state.df_res = processar_resultados(df)
    st.session_state.run_analysis_requested = False
    st.session_state.pending_tab_index = 1
    st.rerun()


ganho_inc = 150.0
ganho_c100 = 120.0
ganho_exc = 100.0
ganho_c200 = 100.0
ganho_c300 = 30.0


with tab_resultados:
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
            df_ranked = df_res.sort_values("PERDA_%_ATUAL", ascending=False).reset_index(drop=True)

            st.markdown('<p class="section-label">Visão geral</p>', unsafe_allow_html=True)
            st.markdown(
                """
<div class="results-shell">
    <p class="module-title">Resumo operacional</p>
    <p class="module-subtitle">Priorização automática por maior perda percentual.</p>
</div>
""",
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
<div class="results-grid">
    <div class="results-card">
        <span>Instalações</span>
        <strong>{len(df_ranked)}</strong>
    </div>
    <div class="results-card">
        <span>Perda média (%)</span>
        <strong>{df_ranked['PERDA_%_ATUAL'].mean():.2f}</strong>
    </div>
    <div class="results-card">
        <span>Perda total (kWh)</span>
        <strong>{df_ranked['PERDA_KWH'].sum():,.2f}</strong>
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

            st.markdown('<p class="section-label">Ranking por perda</p>', unsafe_allow_html=True)
            st.markdown('<p class="results-note">Instalações mais críticas aparecem no topo para priorização.</p>', unsafe_allow_html=True)
            st.markdown('<div class="results-table-shell">', unsafe_allow_html=True)
            st.dataframe(df_ranked, use_container_width=True, hide_index=True, height=420)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<p class="section-label">Exportar</p>', unsafe_allow_html=True)
            st.markdown('<div class="export-shell">', unsafe_allow_html=True)
            st.markdown('<p class="results-note">Baixe o resultado consolidado da análise.</p>', unsafe_allow_html=True)
            df_export = montar_export_resultado(df_ranked)
            st.download_button(
                "Baixar resultado (.csv)",
                df_export.to_csv(index=False),
                "resultado.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary",
            )
            st.markdown('</div>', unsafe_allow_html=True)


with tab_simulacao:
    if st.session_state.df_res is None:
        st.warning("A simulação fica disponível após a conclusão da análise na aba Resultados.")
    else:
        df_res = st.session_state.df_res.copy()
        df = st.session_state.df.copy()

        if "INSTALACAO" not in df_res.columns or "INSTALACAO" not in df.columns:
            st.error("Base inválida para simulação: coluna INSTALACAO não encontrada.")
            st.stop()

        df_res["INSTALACAO"] = df_res["INSTALACAO"].astype(str)
        df["INSTALACAO"] = df["INSTALACAO"].astype(str)

        st.markdown('<p class="section-label">Simulação de ações</p>', unsafe_allow_html=True)
        st.markdown('<p class="helper-text">Ajuste ações e acompanhe em tempo real o progresso da meta.</p>', unsafe_allow_html=True)
        st.markdown(
            """
<div class="sim-shell">
    <p class="module-title">Módulo de Simulação</p>
    <p class="module-subtitle">Persistência de estado, limpeza segura e semáforo de atingimento.</p>
</div>
""",
            unsafe_allow_html=True,
        )

        inst_sel = st.selectbox("Instalação", df_res["INSTALACAO"].tolist())
        base_rows = df[df["INSTALACAO"] == str(inst_sel)]
        if base_rows.empty:
            st.error("Não foi possível localizar os dados de entrada para a instalação selecionada.")
            st.stop()
        base = base_rows.iloc[0]

        perda = (
            base["REQUERIDA"]
            + base["INJETADA"]
            - base["REVERSA"]
            - base["CONSUMO"]
            - base["ILUMINACAO_PUBLICA"]
        )
        red_series = df_res[df_res["INSTALACAO"] == str(inst_sel)]["RED_NECESSARIA_KWH"]
        if red_series.empty:
            st.error("Não foi possível obter a meta para a instalação selecionada.")
            st.stop()
        meta = perda - float(red_series.iloc[0])

        st.markdown(
            f"""
<div class="sim-grid">
    <div class="sim-card">
        <span>Instalação selecionada</span>
        <strong>{inst_sel}</strong>
    </div>
    <div class="sim-card">
        <span>Perda atual</span>
        <strong>{perda:.2f} kWh</strong>
    </div>
    <div class="sim-card">
        <span>Meta projetada</span>
        <strong>{meta:.2f} kWh</strong>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sim-control-shell">', unsafe_allow_html=True)
        modo_ganho = st.radio(
            "Modo de cálculo do ganho",
            ["Valor médio", "Customizar individualmente"],
            horizontal=True,
            key="sim_modo_ganho",
            index=0 if st.session_state.sim_persist_modo == "Valor médio" else 1,
        )
        st.session_state.sim_persist_modo = modo_ganho
        st.markdown(
            '<p class="sim-control-note">Modo médio usa um valor por ação; modo customizado permite valor por ocorrência.</p>',
            unsafe_allow_html=True,
        )

        def calcular_ganho(qtd, valor_padrao, acao_key, rotulo):
            if qtd == 0:
                return 0

            if modo_ganho == "Valor médio":
                valor_inicial = float(st.session_state.get(f"sim_persist_{acao_key}_medio", valor_padrao))
                valor = st.number_input(
                    f"{rotulo} (kWh por ação)",
                    min_value=0.0,
                    value=valor_inicial,
                    key=f"sim_{acao_key}_medio",
                )
                st.session_state[f"sim_persist_{acao_key}_medio"] = float(valor)
                return qtd * valor

            ganhos = []
            with st.expander(f"Detalhar {rotulo}"):
                for i in range(qtd):
                    persist_key = f"sim_persist_{acao_key}_{i}"
                    valor_inicial = float(st.session_state.get(persist_key, valor_padrao))
                    val = st.number_input(
                        f"{rotulo} #{i + 1} (kWh)",
                        min_value=0.0,
                        value=valor_inicial,
                        key=f"sim_{acao_key}_{i}",
                        step=20.0,
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

        b1, b2 = st.columns(2)
        with b1:
            if st.button("Limpar códigos", key="btn_limpar_codigos", type="secondary", use_container_width=True):
                st.session_state.sim_clear_requested = True
                st.rerun()
        with b2:
            st.markdown(
                '<p class="sim-control-note">A limpeza afeta somente os controles da simulação, sem alterar a base de entrada.</p>',
                unsafe_allow_html=True,
            )

        st.markdown('</div>', unsafe_allow_html=True)

        ganho_total = (
            calcular_ganho(inc, ganho_inc, "inc", "Inclusões")
            + calcular_ganho(c100, ganho_c100, "c100", "Cod 100")
            - calcular_ganho(exc, ganho_exc, "exc", "Exclusões")
            + calcular_ganho(c200, ganho_c200, "c200", "Cod 200")
            + calcular_ganho(c300, ganho_c300, "c300", "Cod 300")
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
            texto_badge = "Meta próxima"
            cor_barra = "#f59e0b"
        else:
            classe_badge = "sim-badge sim-badge-ok"
            texto_badge = "Meta atingida"
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
            unsafe_allow_html=True,
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
                unsafe_allow_html=True,
            )

# Clica automaticamente na aba pendente (ex.: após Rodar análise).
if st.session_state.pending_tab_index is not None:
        target_idx = int(st.session_state.pending_tab_index)
        components.html(
                f"""
                <script>
                const target = {target_idx};
                const clickTab = () => {{
                    const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                    if (tabs && tabs.length > target) {{
                        tabs[target].click();
                        return true;
                    }}
                    return false;
                }};
                if (!clickTab()) {{
                    let tries = 0;
                    const timer = setInterval(() => {{
                        tries += 1;
                        if (clickTab() || tries > 20) clearInterval(timer);
                    }}, 120);
                }}
                </script>
                """,
                height=0,
        )
        st.session_state.pending_tab_index = None
