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
