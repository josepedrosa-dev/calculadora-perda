import streamlit as st
import pandas as pd
import math

st.set_page_config(layout="wide")

st.title("📊 Gestão de Perdas - Dashboard Inteligente")

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
# UPLOAD
# =========================

file = st.file_uploader("📂 Upload da base (Excel)", type=["xlsx"])

if file:

    df = pd.read_excel(file)

    # =========================
    # PROCESSAMENTO
    # =========================

    resultados = []

    for _, row in df.iterrows():

        requerida = row["REQUERIDA"]
        injetada = row["INJETADA"]
        perda_inicial = row["PERDA_INICIAL"]

        total = requerida + injetada

        if total == 0:
            continue

        perda_pct = perda_inicial / total
        faixa = math.ceil(perda_pct * 100)

        meta_pct = curva.get(faixa, 0)
        reducao = meta_pct / 100 * total

        # =========================
        # OTIMIZADOR
        # =========================

        ganho_necessario = reducao

        acoes = [
            ("Inclusoes",150),
            ("Cod100",120),
            ("Exclusoes",100),
            ("Cod200",100),
            ("Cod300",30),
        ]

        acoes.sort(key=lambda x: x[1], reverse=True)

        ganho = 0
        plano = {}

        for nome, impacto in acoes:
            if ganho >= ganho_necessario:
                break

            restante = ganho_necessario - ganho
            qtd = math.ceil(restante / impacto)

            plano[nome] = qtd
            ganho += qtd * impacto

        perda_final = perda_inicial - ganho
        gap = (perda_inicial - reducao) - perda_final

        resultados.append({
            "INSTALACAO": row["INSTALACAO"],
            "PERDA_%": perda_pct * 100,
            "META_%": meta_pct,
            "REDUCAO_NEC": reducao,
            "GANHO_OTIM": ganho,
            "PERDA_FINAL": perda_final,
            "ATINGIU_META": perda_final <= (perda_inicial - reducao),
            "TOTAL_ACOES": sum(plano.values()),
            **plano
        })

    df_res = pd.DataFrame(resultados)

    # =========================
    # DASHBOARD
    # =========================

    st.subheader("📊 Visão Executiva")

    col1, col2, col3 = st.columns(3)

    col1.metric("Instalações", len(df_res))
    col2.metric("Meta Atingida", df_res["ATINGIU_META"].mean()*100)
    col3.metric("Ações Totais", df_res["TOTAL_ACOES"].sum())

    st.markdown("---")

    # =========================
    # RANKING
    # =========================

    st.subheader("🔥 Ranking Prioritário")

    ranking = df_res.sort_values(by="PERDA_%", ascending=False)

    st.dataframe(ranking, use_container_width=True)

    # =========================
    # GRÁFICOS
    # =========================

    st.subheader("📈 Análises")

    st.bar_chart(df_res.set_index("INSTALACAO")["PERDA_%"])

    st.bar_chart(df_res.set_index("INSTALACAO")["TOTAL_ACOES"])

    # =========================
    # DOWNLOAD
    # =========================

    st.download_button(
        "📥 Baixar Resultado",
        df_res.to_csv(index=False),
        "resultado.csv"
    )

else:
    st.info("Faça upload da base para iniciar.")