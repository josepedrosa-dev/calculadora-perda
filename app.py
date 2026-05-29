import io
import os
import math
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader


APP_TITLE = "Calculadora de Recuperação de Energia"
APP_SUBTITLE = "Calculadora de impacto operacional"
AUTHOR_NAME = "José Pedrosa"
AUTHOR_EMAIL = "jose.peronico@equatorialenergia.com.br"
USAGE_LOG_PATH = Path(__file__).with_name("usage_events.csv")
USER_NAME_OPTIONS = [
    "João",
    "Marciel",
    "Matheus",
    "Alex",
    "Adriel",
    "Bismackson",
    "Felipe",
    "Mariane",
    "Outros",
]
OTHER_USER_OPTION = "Outros"
DEFAULT_USER_AREA = "Não informado"
USAGE_EVENT_COLUMNS = [
    "timestamp",
    "session_id",
    "user_id",
    "user_name",
    "user_area",
    "is_admin",
    "event_type",
    "details",
]

REQUIRED_COLUMNS = [
    "INSTALACAO",
    "REQUERIDA",
    "INJETADA",
    "REVERSA",
    "CONSUMO",
    "ILUMINACAO_PUBLICA",
]
NUMERIC_COLUMNS = REQUIRED_COLUMNS[1:]

ACTION_DEFAULTS = {
    "inc": {"label": "Inclusões", "default_gain": 150.0},
    "c100": {"label": "Cod 100", "default_gain": 120.0},
    "exc": {"label": "Exclusões", "default_gain": 100.0},
    "c200": {"label": "Cod 200", "default_gain": 100.0},
    "c300": {"label": "Cod 300", "default_gain": 30.0},
}

LEGACY_EXPORT_COLUMNS = {
    "PERDA_%_ATUAL": "PERDA_%",
    "PERDA_KWH": "PERDA_(kWh)",
    "RED_MIN_CURVA_KWH": "RED_MIN_EFICIÊNCIA",
    "RED_PARA_10%_KWH": "RED_PARA_ADEQUADA",
    "RED_NECESSARIA_KWH": "RED_NECESSÁRIA",
}

CURVA_LISTA = [
    0.88, 1.4, 1.84, 2.22, 2.58, 2.91, 3.23, 3.53, 3.82, 4.09,
    4.36, 4.62, 4.87, 5.12, 5.36, 5.6, 5.83, 6.05, 6.27, 6.49,
    6.71, 6.92, 7.12, 7.33, 7.53, 7.73, 7.93, 8.12, 8.31, 8.5,
    8.69, 8.87, 9.06, 9.24, 9.42, 9.6, 9.77, 9.95, 10.12, 10.29,
    10.47, 10.63, 10.8, 10.97, 11.13, 11.3, 11.46, 11.62, 11.78,
    11.94, 12.1, 12.26, 12.41, 12.57, 12.72, 12.88, 13.03, 13.18,
    13.33, 13.48, 13.63, 13.78, 13.93, 14.07, 14.22, 14.37, 14.51,
    14.65, 14.8, 14.94, 15.08, 15.22, 15.36, 15.5, 15.64, 15.78,
    15.92, 16.05, 16.19, 16.33, 16.46, 16.6, 16.73, 16.87, 17,
    17.13, 17.26, 17.4, 17.53, 17.66, 17.79, 17.92, 18.05, 18.18,
    18.31, 18.43, 18.56, 18.69, 18.81, 18.94,
]
CURVA = {i: valor for i, valor in enumerate(CURVA_LISTA)}


@dataclass
class ValidationResult:
    ok: bool
    message: str


@dataclass
class SimulationResult:
    perda_atual: float
    perda_projetada: float
    meta_ganho: float
    ganho_realizado: float
    atingimento: float
    atingimento_barra: float

    @property
    def meta_atingida(self) -> bool:
        return self.ganho_realizado >= self.meta_ganho

    @property
    def falta_para_meta(self) -> float:
        return max(0.0, self.meta_ganho - self.ganho_realizado)


st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="collapsed",
)


def render_css() -> None:
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

.app-header p { margin: 0; font-size: 0.98rem; }

.step-grid,
.status-grid,
.results-grid,
.sim-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
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

.module-subtitle { margin: 0.22rem 0 0; }

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

.sim-control-note { margin: 0.28rem 0 0; }

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

.stDownloadButton > button * { color: #0f5132 !important; }

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


def init_session_state() -> None:
    defaults = {
        "df": None,
        "df_res": None,
        "run_analysis_requested": False,
        "pending_tab_index": None,
        "last_input_signature": None,
        "sim_clear_requested": False,
        "sim_persist_modo": "Valor médio",
        "usage_user": None,
        "usage_session_id": None,
        "simulation_view_logged": False,
        "usage_dashboard_logged": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "df_manual" not in st.session_state:
        st.session_state.df_manual = pd.DataFrame(columns=REQUIRED_COLUMNS)

    for action_key, config in ACTION_DEFAULTS.items():
        st.session_state.setdefault(f"sim_persist_{action_key}", 0)
        st.session_state.setdefault(f"sim_persist_{action_key}_medio", config["default_gain"])


def get_admin_password() -> str:
    try:
        secret_password = st.secrets.get("ADMIN_PASSWORD")
        if secret_password:
            return str(secret_password).strip()
    except Exception:
        pass

    env_password = os.environ.get("ADMIN_PASSWORD")
    if env_password:
        return env_password.strip()

    return ""


def normalize_lookup_text(value: str) -> str:
    return " ".join(str(value).strip().casefold().split())


def get_admin_names() -> set[str]:
    raw_names = None
    try:
        raw_names = st.secrets.get("ADMIN_NAMES")
    except Exception:
        pass

    if raw_names is None:
        raw_names = os.environ.get("ADMIN_NAMES")

    if isinstance(raw_names, str):
        names = [name.strip() for name in raw_names.split(",")]
    elif raw_names:
        names = [str(name).strip() for name in raw_names]
    else:
        names = []

    return {normalize_lookup_text(name) for name in names if str(name).strip()}


def user_name_is_admin(name: str) -> bool:
    return normalize_lookup_text(name) in get_admin_names()


def admin_credentials_are_valid(name: str, password: str) -> bool:
    admin_password = get_admin_password()
    return bool(admin_password and password and user_name_is_admin(name) and password == admin_password)


def make_user_identifier(name: str) -> str:
    normalized_name = normalize_lookup_text(name).replace(" ", "_")
    return f"nome:{normalized_name}"


def current_user() -> dict | None:
    return st.session_state.get("usage_user")


def current_user_is_admin() -> bool:
    user = current_user()
    return bool(user and user.get("is_admin"))


def ensure_usage_session_id() -> str:
    if not st.session_state.get("usage_session_id"):
        st.session_state.usage_session_id = uuid.uuid4().hex
    return st.session_state.usage_session_id


def append_usage_event(event_type: str, details: str = "") -> None:
    user = current_user() or {}
    event = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "session_id": ensure_usage_session_id(),
        "user_id": user.get("identifier", ""),
        "user_name": user.get("name", ""),
        "user_area": user.get("area", ""),
        "is_admin": bool(user.get("is_admin", False)),
        "event_type": event_type,
        "details": details,
    }
    file_exists = USAGE_LOG_PATH.exists()
    try:
        pd.DataFrame([event], columns=USAGE_EVENT_COLUMNS).to_csv(
            USAGE_LOG_PATH,
            mode="a",
            header=not file_exists,
            index=False,
            encoding="utf-8",
        )
    except OSError as exc:
        st.warning(f"Não foi possível registrar o evento de uso: {exc}")


def load_usage_events() -> pd.DataFrame:
    if not USAGE_LOG_PATH.exists():
        return pd.DataFrame(columns=USAGE_EVENT_COLUMNS)

    events = pd.read_csv(USAGE_LOG_PATH, encoding="utf-8")
    for column in USAGE_EVENT_COLUMNS:
        if column not in events.columns:
            events[column] = ""
    events = events[USAGE_EVENT_COLUMNS]
    events["timestamp"] = pd.to_datetime(events["timestamp"], errors="coerce")
    return events


def render_login() -> None:
    st.markdown(
        f"""
<div class="app-header">
    <h1>{APP_TITLE}</h1>
    <p>{APP_SUBTITLE}</p>
    <p>Identificação de usuário para controle de uso da ferramenta.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    selected_name = st.selectbox("Nome", USER_NAME_OPTIONS, key="usage_login_name_option")
    with st.form("usage_login_form"):
        custom_name = ""
        if selected_name == OTHER_USER_OPTION:
            custom_name = st.text_input("Digite o nome")
        admin_password = st.text_input("Senha de administrador (opcional)", type="password")
        submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

    if not submitted:
        return

    name = custom_name if selected_name == OTHER_USER_OPTION else selected_name
    name = name.strip()
    if not name:
        st.error("Informe o nome para acessar a ferramenta.")
        return

    typed_admin_password = admin_password.strip()
    is_admin = admin_credentials_are_valid(name, typed_admin_password)
    if typed_admin_password and not is_admin:
        st.error("Credenciais de administrador inválidas.")
        return

    st.session_state.usage_user = {
        "name": name,
        "identifier": make_user_identifier(name),
        "area": DEFAULT_USER_AREA,
        "is_admin": is_admin,
    }
    ensure_usage_session_id()
    append_usage_event("login", f"admin={is_admin}")
    st.rerun()


def require_login() -> bool:
    if current_user():
        return True
    render_login()
    return False


def render_logged_user_sidebar() -> None:
    user = current_user()
    if not user:
        return

    st.sidebar.markdown("### Usuário")
    st.sidebar.write(user["name"])
    if user.get("is_admin"):
        st.sidebar.success("Administrador")
    else:
        st.sidebar.caption("Sessão ativa")

    if st.sidebar.button("Sair", use_container_width=True):
        append_usage_event("logout")
        st.session_state.usage_user = None
        st.session_state.usage_session_id = None
        st.session_state.simulation_view_logged = False
        st.session_state.usage_dashboard_logged = False
        st.rerun()


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result.columns = result.columns.str.strip().str.upper()
    return result


def normalize_instalacao(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    if "INSTALACAO" in result.columns:
        result["INSTALACAO"] = result["INSTALACAO"].astype(str).str.strip()
    return result


def parse_float_br(value) -> float | None:
    text = re.sub(r"[^\d,\.\-]", "", str(value).strip())
    if not text:
        return None

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+", text) or re.fullmatch(r"-?\d+,\d{3}", text):
            text = text.replace(",", "")
        elif re.fullmatch(r"-?\d+,\d{1,2}", text):
            text = text.replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "." in text and (
        re.fullmatch(r"-?\d{1,3}(\.\d{3})+", text) or re.fullmatch(r"-?\d+\.\d{3}", text)
    ):
        text = text.replace(".", "")

    try:
        return float(text)
    except ValueError:
        return None


def validate_dataframe(df_base: pd.DataFrame) -> ValidationResult:
    missing = set(REQUIRED_COLUMNS) - set(df_base.columns)
    if missing:
        return ValidationResult(False, f"Faltam colunas obrigatórias: {', '.join(sorted(missing))}")

    df_val = df_base.copy()
    for column in NUMERIC_COLUMNS:
        df_val[column] = pd.to_numeric(df_val[column], errors="coerce")
        if df_val[column].isna().any():
            return ValidationResult(False, f"A coluna {column} possui valores inválidos.")
        if (df_val[column] < 0).any():
            return ValidationResult(False, f"A coluna {column} não pode ter valores negativos.")

    instalacoes = df_val["INSTALACAO"].astype(str).str.strip()
    if instalacoes.eq("").any():
        return ValidationResult(False, "A coluna INSTALACAO possui valores vazios.")
    if instalacoes.duplicated().any():
        return ValidationResult(False, "Existem instalações duplicadas.")

    return ValidationResult(True, "ok")


def calculate_loss(row: pd.Series) -> float:
    perda = row["REQUERIDA"] + row["INJETADA"] - row["REVERSA"] - row["CONSUMO"] - row["ILUMINACAO_PUBLICA"]
    return max(0.0, float(perda))


def extract_metric_series(texto_norm: str, label: str, next_labels: list[str]) -> list[float]:
    start = texto_norm.find(label)
    if start == -1:
        return []

    segment = texto_norm[start : start + 450]
    if ":" in segment:
        segment = segment.split(":", 1)[1]

    end = len(segment)
    for next_label in next_labels:
        position = segment.find(next_label)
        if position != -1:
            end = min(end, position)
    segment = segment[:end]

    values = []
    for number in re.findall(r"\d{1,3}(?:\.\d{3})*(?:,\d+)?", segment):
        parsed = parse_float_br(number)
        if parsed is not None:
            values.append(parsed)
    return values


def extract_installation_id(texto_norm: str) -> str:
    patterns = [
        r"Instala[çc][aã]o\s*Fiscal\s*:?\s*(\d{8,12})",
        r"Inst\.?\s*Fiscal\s*:?\s*(\d{8,12})",
    ]
    for pattern in patterns:
        match = re.search(pattern, texto_norm, flags=re.IGNORECASE)
        if match:
            return match.group(1)

    candidates = re.findall(r"\b\d{8,12}\b", texto_norm[:2500])
    return candidates[0] if candidates else ""


def extract_pdf_data_from_text(text: str) -> dict:
    texto_norm = re.sub(r"\s+", " ", text)
    refs_detectadas = extract_pdf_references(texto_norm[:1200])

    labels = [
        "Requerida Trafo (kWh)",
        "Injetada GDIS (kWh)",
        "Energia Reversa (kWh)",
        "Consumo Clientes (kWh)",
        "IP Estimada (kWh)",
    ]
    metrics = {
        "REQUERIDA": extract_metric_series(texto_norm, labels[0], labels[1:]),
        "INJETADA": extract_metric_series(texto_norm, labels[1], labels[2:]),
        "REVERSA": extract_metric_series(texto_norm, labels[2], labels[3:]),
        "CONSUMO": extract_metric_series(texto_norm, labels[3], labels[4:]),
        "ILUMINACAO_PUBLICA": extract_metric_series(texto_norm, labels[4], ["Referência", "Perda (KWh)"]),
    }

    installation = extract_installation_id(texto_norm)
    if not installation:
        return {"ok": False, "erro": "Não foi possível identificar a Instalação Fiscal no PDF."}
    if not all(metrics[column] for column in metrics):
        return {"ok": False, "erro": "Não foi possível extrair todas as séries necessárias do PDF."}

    target_len = min(min(len(values) for values in metrics.values() if values), 4)
    refs = [ref for ref in refs_detectadas if ref != "Média"][: max(0, target_len - 1)]
    while len(refs) < max(0, target_len - 1):
        refs.append(f"Mês {len(refs) + 1}")
    refs.append("Média")

    for column in metrics:
        metrics[column] = metrics[column][:target_len]

    return {"ok": True, "instalacao": installation, "refs": refs, "metricas": metrics}


def extract_pdf_references(text: str) -> list[str]:
    references = []
    pattern = r"\b([A-Za-z]{3,4})\s*/\s*(\d{2}\s*\d{2}|\d{2,4})\b"
    for month, year in re.findall(pattern, text, flags=re.IGNORECASE):
        clean_year = re.sub(r"\s+", "", year)
        if len(clean_year) == 2:
            clean_year = f"20{clean_year}"
        reference = f"{month.title()}/{clean_year}"
        if reference not in references:
            references.append(reference)

    if re.search(r"M[eé]dia", text, flags=re.IGNORECASE):
        references.append("Média")
    return references


@st.cache_data(show_spinner=False)
def load_excel_bytes(file_bytes: bytes) -> pd.DataFrame:
    return normalize_columns(pd.read_excel(io.BytesIO(file_bytes)))


@st.cache_data(show_spinner=False)
def extract_pdf_data_cached(pdf_bytes: bytes) -> dict:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = " ".join(page.extract_text() or "" for page in reader.pages[:4])
    return extract_pdf_data_from_text(text)


def extract_pdf_data(pdf_bytes: bytes) -> dict:
    try:
        return extract_pdf_data_cached(pdf_bytes)
    except Exception as exc:
        return {"ok": False, "erro": f"Falha ao ler PDF: {exc}"}


def build_pdf_dataframe(pdf_info: dict, selected_reference: str) -> pd.DataFrame:
    refs = pdf_info["refs"]
    idx = refs.index(selected_reference) if selected_reference in refs else len(refs) - 1

    row = {"INSTALACAO": str(pdf_info["instalacao"]).strip()}
    for column, series in pdf_info["metricas"].items():
        row[column] = float(series[idx]) if idx < len(series) else float(series[-1])

    df_pdf = pd.DataFrame([row])
    for column in NUMERIC_COLUMNS:
        df_pdf[column] = pd.to_numeric(df_pdf[column], errors="coerce").fillna(0.0)
    return df_pdf


def build_pdf_reference_table(pdf_info: dict) -> pd.DataFrame:
    rows = []
    for idx, reference in enumerate(pdf_info["refs"]):
        row = {"REFERENCIA": reference}
        for column, series in pdf_info["metricas"].items():
            row[column] = float(series[idx]) if idx < len(series) else None
        rows.append(row)
    return pd.DataFrame(rows)


def process_results(df_input: pd.DataFrame) -> pd.DataFrame:
    rows = []
    df = normalize_instalacao(df_input)

    for _, row in df.iterrows():
        total = row["REQUERIDA"] + row["INJETADA"]
        if total == 0:
            continue

        perda = calculate_loss(row)
        perda_pct = perda / total
        faixa = min(max(math.ceil(perda_pct * 100), 0), max(CURVA.keys()))
        meta_pp = CURVA.get(faixa, 0)

        perda_pct_alvo = max(0.0, (perda_pct * 100 - meta_pp) / 100)
        perda_alvo_curva_kwh = perda_pct_alvo * total

        red_min = (perda - perda_alvo_curva_kwh)*1.3
        perda_10_kwh = 0.10 * total
        red_10 = max(0.0, perda - perda_10_kwh)
        red_total = max(red_min, red_10)
        perda_final = max(0.0, perda - estimate_action_plan_gain(red_total))

        rows.append(
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

    return pd.DataFrame(rows)


def estimate_action_plan_gain(target_reduction: float) -> float:
    gain = 0.0
    impacts = sorted([150.0, 120.0, -100.0, 100.0, 30.0], reverse=True)
    for impact in impacts:
        if gain >= target_reduction:
            break
        if impact <= 0:
            continue
        quantity = math.ceil((target_reduction - gain) / impact)
        gain += quantity * impact
    return gain


def build_export_dataframe(df_res: pd.DataFrame) -> pd.DataFrame:
    df_export = df_res.copy()
    for new_column, legacy_column in LEGACY_EXPORT_COLUMNS.items():
        if new_column in df_export.columns and legacy_column not in df_export.columns:
            df_export[legacy_column] = df_export[new_column]
    return df_export


def update_input_base(df_new: pd.DataFrame, signature: str) -> None:
    if st.session_state.last_input_signature != signature:
        st.session_state.df = df_new
        st.session_state.df_res = None
        st.session_state.run_analysis_requested = False
        st.session_state.last_input_signature = signature


def request_analysis(target_tab_index: int = 1, source: str = "analysis") -> None:
    append_usage_event("analysis_requested", source)
    st.session_state.run_analysis_requested = True
    st.session_state.pending_tab_index = target_tab_index
    st.rerun()


def run_pending_analysis() -> None:
    if not (
        st.session_state.df is not None
        and st.session_state.df_res is None
        and st.session_state.run_analysis_requested
    ):
        return

    df = normalize_instalacao(normalize_columns(st.session_state.df))
    st.session_state.df = df
    st.session_state.df_res = process_results(df)
    st.session_state.run_analysis_requested = False
    st.session_state.pending_tab_index = 1
    st.rerun()


def render_header() -> None:
    st.markdown(
        f"""
<div class="app-header">
    <h1>{APP_TITLE}</h1>
    <p>{APP_SUBTITLE}</p>
    <p>Desenvolvido por: {AUTHOR_NAME}</p>
    <p>{AUTHOR_EMAIL}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_step_cards() -> None:
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


def render_status_cards() -> None:
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


def render_module_shell(title: str, subtitle: str, css_class: str = "module-shell") -> None:
    st.markdown(
        f"""
<div class="{css_class}">
    <p class="module-title">{title}</p>
    <p class="module-subtitle">{subtitle}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_input_tab() -> None:
    st.markdown('<p class="section-label">Input dos dados</p>', unsafe_allow_html=True)
    st.markdown('<p class="helper-text">Escolha como deseja montar a base para análise.</p>', unsafe_allow_html=True)
    render_module_shell("Módulo de Entrada", "Validação robusta para garantir qualidade dos dados antes do cálculo.")

    input_mode = st.radio("Modo de entrada", ["Upload de Arquivo", "Manual"], horizontal=True)
    if input_mode == "Upload de Arquivo":
        render_upload_input()
    else:
        render_manual_input()


def render_upload_input() -> None:
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

    uploaded_file = st.file_uploader("Arquivo (.xlsx ou .pdf)", type=["xlsx", "pdf"])
    if not uploaded_file:
        return

    file_bytes = uploaded_file.getvalue()
    if uploaded_file.name.lower().endswith(".xlsx"):
        handle_excel_upload(uploaded_file.name, file_bytes)
    else:
        handle_pdf_upload(uploaded_file.name, file_bytes)


def handle_excel_upload(filename: str, file_bytes: bytes) -> None:
    df_upload = load_excel_bytes(file_bytes)
    validation = validate_dataframe(df_upload)
    if not validation.ok:
        st.error(validation.message)
        reset_loaded_analysis()
        return

    st.success(f"Arquivo carregado com sucesso. Registros encontrados: {len(df_upload)}")
    signature = f"excel::{filename}::{len(df_upload)}::{','.join(df_upload.columns)}"
    if st.session_state.last_input_signature != signature:
        append_usage_event("input_loaded", f"excel:{filename}:rows={len(df_upload)}")
    update_input_base(df_upload, signature)

    with st.expander("Pré-visualizar dados carregados"):
        st.dataframe(df_upload.head(10), use_container_width=True)

    if st.button("Rodar análise", key="btn_rodar_upload", use_container_width=True, type="primary"):
        request_analysis(source="upload_excel")


def handle_pdf_upload(filename: str, file_bytes: bytes) -> None:
    pdf_info = extract_pdf_data(file_bytes)
    if not pdf_info["ok"]:
        st.error(pdf_info["erro"])
        return

    refs = pdf_info["refs"]
    default_reference = "Média" if "Média" in refs else refs[-1]
    selected_reference = st.selectbox(
        "Referência para extração dos dados do PDF",
        refs,
        index=refs.index(default_reference),
        key="pdf_ref_escolhida",
    )

    st.markdown(
        '<p class="helper-text">Conferência visual dos valores extraídos por referência.</p>',
        unsafe_allow_html=True,
    )
    st.dataframe(build_pdf_reference_table(pdf_info), use_container_width=True, hide_index=True)

    df_pdf = build_pdf_dataframe(pdf_info, selected_reference)
    validation = validate_dataframe(df_pdf)
    if not validation.ok:
        st.error(validation.message)
        return

    st.success(
        f"PDF lido com sucesso para instalação {df_pdf.iloc[0]['INSTALACAO']} "
        f"usando referência: {selected_reference}"
    )
    with st.expander("Pré-visualizar dados extraídos do PDF"):
        st.dataframe(df_pdf, use_container_width=True)

    signature = f"pdf::{filename}::{selected_reference}::{df_pdf.iloc[0]['INSTALACAO']}"
    if st.session_state.last_input_signature != signature:
        append_usage_event(
            "input_loaded",
            f"pdf:{filename}:ref={selected_reference}:instalacao={df_pdf.iloc[0]['INSTALACAO']}",
        )
    update_input_base(df_pdf, signature)
    if st.button("Rodar análise", key="btn_rodar_upload_pdf", use_container_width=True, type="primary"):
        request_analysis(source="upload_pdf")


def reset_loaded_analysis() -> None:
    st.session_state.df = None
    st.session_state.df_res = None
    st.session_state.run_analysis_requested = False


def render_manual_input() -> None:
    st.markdown('<p class="section-label">Nova instalação</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="helper-text">Preencha os campos e clique em adicionar para montar sua base.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<span class="counter-chip">Instalações inseridas: {len(st.session_state.df_manual)}</span>',
        unsafe_allow_html=True,
    )

    manual_entry = render_manual_form()
    if manual_entry["add"]:
        add_manual_installation(manual_entry)
    if manual_entry["clear"]:
        clear_manual_installations()

    if not st.session_state.df_manual.empty:
        render_manual_table()


def render_manual_form() -> dict:
    with st.form("form_nova_instalacao", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            installation = st.text_input("Instalação MF", placeholder="Ex: 123456789")
            requerida = st.number_input("Requerida", min_value=0.0, step=500.0, key="in_req")
            injetada = st.number_input("Injetada", min_value=0.0, step=500.0, key="in_inj")
        with col2:
            reversa = st.number_input("Reversa", min_value=0.0, step=500.0, key="in_rev")
            consumo = st.number_input("Consumo", min_value=0.0, step=500.0, key="in_con")
            iluminacao = st.number_input("Iluminação Pública", min_value=0.0, step=500.0, key="in_ilu")

        col_add, col_clear = st.columns(2)
        with col_add:
            add = st.form_submit_button("Adicionar instalação")
        with col_clear:
            clear = st.form_submit_button("Limpar tudo")

    return {
        "add": add,
        "clear": clear,
        "INSTALACAO": str(installation).strip(),
        "REQUERIDA": requerida,
        "INJETADA": injetada,
        "REVERSA": reversa,
        "CONSUMO": consumo,
        "ILUMINACAO_PUBLICA": iluminacao,
    }


def add_manual_installation(entry: dict) -> None:
    installation = entry["INSTALACAO"]
    if not installation:
        st.warning("Informe a instalação antes de adicionar.")
        return

    existing = st.session_state.df_manual["INSTALACAO"].astype(str).values
    if not st.session_state.df_manual.empty and installation in existing:
        st.warning("Esta instalação já existe na lista manual.")
        return

    new_row = pd.DataFrame([{column: entry[column] for column in REQUIRED_COLUMNS}])
    st.session_state.df_manual = pd.concat([st.session_state.df_manual, new_row], ignore_index=True)
    st.session_state.df_res = None
    st.success("Instalação adicionada à lista.")


def clear_manual_installations() -> None:
    st.session_state.df_manual = st.session_state.df_manual.iloc[0:0]
    reset_loaded_analysis()
    st.info("Lista manual limpa.")


def render_manual_table() -> None:
    st.markdown('<p class="section-label">Instalações inseridas</p>', unsafe_allow_html=True)
    editor_df = st.data_editor(
        st.session_state.df_manual,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="manual_editor",
    )
    editor_df = normalize_columns(editor_df)
    st.markdown('<p class="helper-text">Gerencie a base manual e rode a análise.</p>', unsafe_allow_html=True)

    options = editor_df["INSTALACAO"].astype(str).tolist()
    _, center_col, _ = st.columns([1, 1.8, 1])
    with center_col:
        selected_installation = st.selectbox("Remover instalação", options, key="inst_remover")

    col_remove, col_run = st.columns(2)
    with col_remove:
        if st.button("Remover selecionada", key="btn_remover", use_container_width=True, type="secondary"):
            st.session_state.df_manual = editor_df[
                editor_df["INSTALACAO"].astype(str) != str(selected_installation)
            ].reset_index(drop=True)
            st.session_state.df_res = None
            st.session_state.run_analysis_requested = False
            st.success("Instalação removida.")

    with col_run:
        if st.button("Rodar análise", key="btn_rodar_manual", use_container_width=True, type="primary"):
            run_manual_analysis(editor_df)


def run_manual_analysis(editor_df: pd.DataFrame) -> None:
    validation = validate_dataframe(editor_df)
    if not validation.ok:
        st.error(validation.message)
        return

    st.session_state.df_manual = editor_df
    st.session_state.df = editor_df.copy()
    st.session_state.df_res = None
    st.session_state.run_analysis_requested = True
    st.session_state.last_input_signature = f"manual::{len(editor_df)}"
    st.session_state.pending_tab_index = 1
    append_usage_event("input_loaded", f"manual:rows={len(editor_df)}")
    append_usage_event("analysis_requested", "manual")
    st.rerun()


def render_results_tab() -> None:
    if st.session_state.df_res is None:
        st.info("A etapa de resultados será habilitada após rodar a análise na aba Entrada.")
        return

    df_res = st.session_state.df_res
    if df_res.empty:
        st.warning(
            "A análise foi concluída, mas nenhum resultado válido foi gerado. "
            "Revise os dados de entrada e os critérios de processamento na aba Entrada."
        )
        return

    df_ranked = df_res.sort_values("PERDA_%_ATUAL", ascending=False).reset_index(drop=True)
    st.markdown('<p class="section-label">Visão geral</p>', unsafe_allow_html=True)
    render_module_shell("Resumo operacional", "Priorização automática por maior perda percentual.", "results-shell")
    render_results_summary(df_ranked)
    render_results_table(df_ranked)
    render_export_section(df_ranked)


def render_results_summary(df_ranked: pd.DataFrame) -> None:
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


def render_results_table(df_ranked: pd.DataFrame) -> None:
    st.markdown('<p class="section-label">Ranking por perda</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="results-note">Instalações mais críticas aparecem no topo para priorização.</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="results-table-shell">', unsafe_allow_html=True)
    st.dataframe(df_ranked, use_container_width=True, hide_index=True, height=420)
    st.markdown("</div>", unsafe_allow_html=True)


def render_export_section(df_ranked: pd.DataFrame) -> None:
    st.markdown('<p class="section-label">Exportar</p>', unsafe_allow_html=True)
    st.markdown('<div class="export-shell">', unsafe_allow_html=True)
    st.markdown('<p class="results-note">Baixe o resultado consolidado da análise.</p>', unsafe_allow_html=True)
    st.download_button(
        "Baixar resultado (.csv)",
        build_export_dataframe(df_ranked).to_csv(index=False),
        "resultado.csv",
        mime="text/csv",
        use_container_width=True,
        type="primary",
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_simulation_tab() -> None:
    if st.session_state.df_res is None:
        st.warning("A simulação fica disponível após a conclusão da análise na aba Resultados.")
        return

    if not st.session_state.simulation_view_logged:
        append_usage_event("simulation_viewed")
        st.session_state.simulation_view_logged = True

    df_res = normalize_instalacao(st.session_state.df_res)
    df = normalize_instalacao(st.session_state.df)
    if "INSTALACAO" not in df_res.columns or "INSTALACAO" not in df.columns:
        st.error("Base inválida para simulação: coluna INSTALACAO não encontrada.")
        st.stop()

    st.markdown('<p class="section-label">Simulação de ações</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="helper-text">Ajuste ações e acompanhe em tempo real o progresso da meta.</p>',
        unsafe_allow_html=True,
    )
    render_module_shell(
        "Módulo de Simulação",
        "Persistência de estado, limpeza segura e semáforo de atingimento.",
        "sim-shell",
    )

    selected_installation = st.selectbox("Instalação", df_res["INSTALACAO"].tolist())
    base_row = get_selected_base_row(df, selected_installation)
    target_gain = get_selected_target_gain(df_res, selected_installation)*1.3
    current_loss = calculate_loss(base_row)
    render_simulation_context(selected_installation, current_loss, target_gain)

    gain_total = render_simulation_controls()
    result = calculate_simulation_result(current_loss, target_gain, gain_total)
    render_simulation_progress(result)
    render_simulation_metrics(result)


def get_selected_base_row(df: pd.DataFrame, selected_installation: str) -> pd.Series:
    rows = df[df["INSTALACAO"] == str(selected_installation)]
    if rows.empty:
        st.error("Não foi possível localizar os dados de entrada para a instalação selecionada.")
        st.stop()
    return rows.iloc[0]


def get_selected_target_gain(df_res: pd.DataFrame, selected_installation: str) -> float:
    target_series = df_res[df_res["INSTALACAO"] == str(selected_installation)]["RED_MIN_CURVA_KWH"]
    if target_series.empty:
        st.error("Não foi possível obter a meta para a instalação selecionada.")
        st.stop()
    return max(0.0, float(target_series.iloc[0]))


def render_simulation_context(installation: str, current_loss: float, target_gain: float) -> None:
    st.markdown(
        f"""
<div class="sim-grid">
    <div class="sim-card">
        <span>Instalação selecionada</span>
        <strong>{installation}</strong>
    </div>
    <div class="sim-card">
        <span>Perda atual</span>
        <strong>{current_loss:.2f} kWh</strong>
    </div>
    <div class="sim-card">
        <span>Meta de recuperação</span>
        <strong>{target_gain:.2f} kWh</strong>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_simulation_controls() -> float:
    st.markdown('<div class="sim-control-shell">', unsafe_allow_html=True)
    gain_mode = st.radio(
        "Modo de cálculo do ganho",
        ["Valor médio", "Customizar individualmente"],
        horizontal=True,
        key="sim_modo_ganho",
        index=0 if st.session_state.sim_persist_modo == "Valor médio" else 1,
    )
    st.session_state.sim_persist_modo = gain_mode
    st.markdown(
        '<p class="sim-control-note">Modo médio usa um valor por ação; modo customizado permite valor por ocorrência.</p>',
        unsafe_allow_html=True,
    )

    if st.session_state.sim_clear_requested:
        clear_simulation_controls()
        st.session_state.sim_clear_requested = False

    st.markdown(
        '<p class="action-hint">Informe a quantidade de ações planejadas em cada categoria.</p>',
        unsafe_allow_html=True,
    )
    quantities = render_action_quantity_inputs()
    render_clear_simulation_button()
    st.markdown("</div>", unsafe_allow_html=True)

    return calculate_total_gain(quantities, gain_mode)


def render_action_quantity_inputs() -> dict[str, int]:
    col1, col2 = st.columns(2)
    with col1:
        quantities = {
            "inc": st.number_input("Inclusões", min_value=0, value=int(st.session_state.sim_persist_inc), key="sim_inc"),
            "c100": st.number_input("Cod 100", min_value=0, value=int(st.session_state.sim_persist_c100), key="sim_c100"),
            "c200": st.number_input("Cod 200", min_value=0, value=int(st.session_state.sim_persist_c200), key="sim_c200"),
        }
    with col2:
        quantities["exc"] = st.number_input(
            "Exclusões",
            min_value=0,
            value=int(st.session_state.sim_persist_exc),
            key="sim_exc",
        )
        quantities["c300"] = st.number_input(
            "Cod 300",
            min_value=0,
            value=int(st.session_state.sim_persist_c300),
            key="sim_c300",
        )

    for action_key, quantity in quantities.items():
        st.session_state[f"sim_persist_{action_key}"] = int(quantity)
    return quantities


def render_clear_simulation_button() -> None:
    col_button, col_note = st.columns(2)
    with col_button:
        if st.button("Limpar códigos", key="btn_limpar_codigos", type="secondary", use_container_width=True):
            st.session_state.sim_clear_requested = True
            st.rerun()
    with col_note:
        st.markdown(
            '<p class="sim-control-note">A limpeza afeta somente os controles da simulação, sem alterar a base de entrada.</p>',
            unsafe_allow_html=True,
        )


def calculate_total_gain(quantities: dict[str, int], gain_mode: str) -> float:
    total = 0.0
    for action_key, quantity in quantities.items():
        action_gain = render_action_gain_inputs(action_key, quantity, gain_mode)
        if action_key == "exc":
            total -= action_gain
        else:
            total += action_gain
    return total


def render_action_gain_inputs(action_key: str, quantity: int, gain_mode: str) -> float:
    if quantity == 0:
        return 0.0

    config = ACTION_DEFAULTS[action_key]
    if gain_mode == "Valor médio":
        persist_key = f"sim_persist_{action_key}_medio"
        initial_value = float(st.session_state.get(persist_key, config["default_gain"]))
        value = st.number_input(
            f"{config['label']} (kWh por ação)",
            min_value=0.0,
            value=initial_value,
            key=f"sim_{action_key}_medio",
        )
        st.session_state[persist_key] = float(value)
        return quantity * float(value)

    values = []
    with st.expander(f"Detalhar {config['label']}"):
        for idx in range(quantity):
            persist_key = f"sim_persist_{action_key}_{idx}"
            initial_value = float(st.session_state.get(persist_key, config["default_gain"]))
            value = st.number_input(
                f"{config['label']} #{idx + 1} (kWh)",
                min_value=0.0,
                value=initial_value,
                key=f"sim_{action_key}_{idx}",
                step=20.0,
            )
            st.session_state[persist_key] = float(value)
            values.append(value)
    return float(sum(values))


def clear_simulation_controls() -> None:
    for action_key, config in ACTION_DEFAULTS.items():
        st.session_state[f"sim_{action_key}"] = 0
        st.session_state[f"sim_persist_{action_key}"] = 0
        st.session_state[f"sim_{action_key}_medio"] = float(config["default_gain"])
        st.session_state[f"sim_persist_{action_key}_medio"] = float(config["default_gain"])
    st.session_state["sim_persist_modo"] = "Valor médio"

    prefixes_to_clean = tuple(f"sim_{key}_" for key in ACTION_DEFAULTS) + tuple(
        f"sim_persist_{key}_" for key in ACTION_DEFAULTS
    )
    protected = {f"sim_{key}_medio" for key in ACTION_DEFAULTS} | {
        f"sim_persist_{key}_medio" for key in ACTION_DEFAULTS
    }
    for key in list(st.session_state.keys()):
        if key.startswith(prefixes_to_clean) and key not in protected:
            del st.session_state[key]


def calculate_simulation_result(current_loss: float, target_gain: float, total_gain: float) -> SimulationResult:
    gain_done = max(0.0, total_gain)
    if target_gain == 0:
        achievement = 100.0
    else:
        achievement = max(0.0, (gain_done / target_gain) * 100)

    return SimulationResult(
        perda_atual=current_loss,
        perda_projetada=max(0.0, current_loss - total_gain),
        meta_ganho=target_gain,
        ganho_realizado=gain_done,
        atingimento=achievement,
        atingimento_barra=min(achievement, 100.0),
    )


def simulation_status(result: SimulationResult) -> tuple[str, str, str]:
    if result.atingimento < 90:
        return "sim-badge sim-badge-critico", "Crítico", "#ef4444"
    if result.atingimento < 100:
        return "sim-badge sim-badge-atencao", "Meta próxima", "#f59e0b"
    return "sim-badge sim-badge-ok", "Meta atingida", "#22c55e"


def render_simulation_progress(result: SimulationResult) -> None:
    badge_class, badge_text, bar_color = simulation_status(result)
    st.markdown(
        f'<div class="{badge_class}">Status da simulação: {badge_text}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
<div class="sim-progress-wrap">
    <div class="sim-progress-head">
        <span>Progresso para meta da instalação selecionada</span>
        <strong>{result.atingimento:.1f}%</strong>
    </div>
    <div class="sim-progress-track">
        <div class="sim-progress-fill" style="width:{result.atingimento_barra:.1f}%; background:{bar_color};"></div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_simulation_metrics(result: SimulationResult) -> None:
    st.markdown('<p class="section-label">Resultado projetado</p>', unsafe_allow_html=True)
    col_gain, col_projected_loss, col_target = st.columns(3)
    col_gain.metric("Ganho", f"{result.ganho_realizado:.2f}")
    col_projected_loss.metric("Perda Projetada", f"{result.perda_projetada:.2f}")
    col_target.metric("Meta", f"{result.meta_ganho:.2f}")

    if result.meta_atingida:
        st.markdown('<div class="sim-result-ok">Meta atingida</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="sim-result-fail">Faltam {result.falta_para_meta:.2f} kWh para atingir a meta</div>',
            unsafe_allow_html=True,
        )


def render_usage_dashboard() -> None:
    if not st.session_state.usage_dashboard_logged:
        append_usage_event("usage_dashboard_viewed")
        st.session_state.usage_dashboard_logged = True

    events = load_usage_events()
    st.markdown('<p class="section-label">Dashboard de uso</p>', unsafe_allow_html=True)

    if events.empty:
        st.info("Ainda não há eventos de uso registrados.")
        return

    valid_timestamps = events["timestamp"].dropna()
    unique_users = events["user_id"].replace("", pd.NA).dropna().nunique()
    unique_sessions = events["session_id"].replace("", pd.NA).dropna().nunique()
    last_access = "-"
    if not valid_timestamps.empty:
        last_access = valid_timestamps.max().strftime("%d/%m/%Y %H:%M")

    col_users, col_sessions, col_events, col_last = st.columns(4)
    col_users.metric("Usuários", unique_users)
    col_sessions.metric("Sessões", unique_sessions)
    col_events.metric("Eventos", len(events))
    col_last.metric("Último acesso", last_access)

    st.markdown('<p class="section-label">Uso por usuário</p>', unsafe_allow_html=True)
    by_user = (
        events.groupby(["user_id", "user_name"], dropna=False)
        .agg(
            eventos=("event_type", "count"),
            sessoes=("session_id", "nunique"),
            ultimo_acesso=("timestamp", "max"),
        )
        .reset_index()
    )
    by_user["ultimo_acesso"] = by_user["ultimo_acesso"].dt.strftime("%d/%m/%Y %H:%M")
    by_user = by_user.rename(
        columns={
            "user_id": "identificador",
            "user_name": "nome",
        }
    )
    st.dataframe(
        by_user.sort_values(["eventos", "sessoes"], ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    chart_col_events, chart_col_days = st.columns(2)
    with chart_col_events:
        st.markdown('<p class="section-label">Eventos por tipo</p>', unsafe_allow_html=True)
        events_by_type = events["event_type"].value_counts().rename_axis("tipo").reset_index(name="eventos")
        st.bar_chart(events_by_type, x="tipo", y="eventos")

    with chart_col_days:
        st.markdown('<p class="section-label">Eventos por dia</p>', unsafe_allow_html=True)
        events_by_day = events.dropna(subset=["timestamp"]).copy()
        if events_by_day.empty:
            st.info("Sem eventos com data válida.")
        else:
            events_by_day["data"] = events_by_day["timestamp"].dt.date
            events_by_day = events_by_day.groupby("data").size().reset_index(name="eventos")
            st.line_chart(events_by_day, x="data", y="eventos")

    st.markdown('<p class="section-label">Eventos recentes</p>', unsafe_allow_html=True)
    events_table = events.sort_values("timestamp", ascending=False).copy()
    events_table["timestamp"] = events_table["timestamp"].dt.strftime("%d/%m/%Y %H:%M:%S")
    st.dataframe(events_table, use_container_width=True, hide_index=True)
    st.download_button(
        "Baixar eventos (.csv)",
        data=events_table.to_csv(index=False).encode("utf-8"),
        file_name="usage_events.csv",
        mime="text/csv",
        use_container_width=True,
    )


def click_pending_tab() -> None:
    if st.session_state.pending_tab_index is None:
        return

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


def main() -> None:
    render_css()
    init_session_state()
    if not require_login():
        return

    render_logged_user_sidebar()
    render_header()
    render_step_cards()
    render_status_cards()

    st.markdown('<p class="helper-text">Navegue entre as etapas pelas abas abaixo.</p>', unsafe_allow_html=True)
    tab_labels = ["1. Entrada", "2. Resultados", "3. Simulação"]
    if current_user_is_admin():
        tab_labels.append("4. Uso")
    tabs = st.tabs(tab_labels)
    tab_input, tab_results, tab_simulation = tabs[:3]

    with tab_input:
        render_input_tab()

    run_pending_analysis()

    with tab_results:
        render_results_tab()

    with tab_simulation:
        render_simulation_tab()

    if current_user_is_admin():
        with tabs[3]:
            render_usage_dashboard()

    click_pending_tab()


if __name__ == "__main__":
    main()
