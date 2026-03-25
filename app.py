import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Gestão de Perdas", layout="wide")

# =========================
# HEADER
# =========================
st.title("📊 Gestão Inteligente de Perdas")
st.markdown("Ferramenta de apoio à decisão para redução de perdas e planejamento operacional")

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
# ENTRADA DE DADOS
# =========================
st.markdown("## 📥 Entrada de Dados")

modo = st.radio(
    "Escolha o modo:",
    ["Upload de Excel", "Preenchimento Manual"]
)

df = None

# =========================
# UPLOAD
# =========================
if modo == "Upload de Excel":

    st.info("""
    📌 Formato obrigatório:
    - INSTALACAO
    - REQUERIDA
    - INJETADA
    - PERDA_INICIAL
    """)

    file = st.file_uploader("Upload da base", type=["xlsx"])

    if file:
        df = pd.read_excel(file)

# =========================
# MANUAL
# =========================
elif modo == "Preenchimento Manual":

    st.subheader("✍️ Inserir Dados")

    col1, col2 = st.columns(2)

    with col1:
        inst = st.text_input("Instalação", "INST_001")
        requerida = st.number_input("Energia Requerida", value=10000.0)

    with col2:
        injetada = st.number_input("Energia Injetada", value=0.0)
        perda_inicial = st.number_input("Perda Inicial", value=2000.0)

    if st.button("Calcular"):
        df = pd.DataFrame([{
            "INSTALACAO": inst,
            "REQUERIDA": requerida,
            "INJETADA": injetada,
            "PERDA_INICIAL": perda_inicial
        }])

# =========================
# PROCESSAMENTO
# =========================
if df is not None:

    df.columns = df.columns.str.strip().str.upper()

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

        # METAS
        reducao_minima = perda_inicial * (meta_pct/100)
        meta_10 = 0.10 * total
        reducao_10 = max(0, perda_inicial - meta_10)

        reducao = max(reducao_minima, reducao_10)

        # OTIMIZADOR
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

            qtd = math.ceil((ganho_necessario - ganho) / impacto)
            plano[nome] = qtd
            ganho += qtd * impacto

        perda_final = perda_inicial - ganho

        resultados.append({
            "INSTALACAO": row["INSTALACAO"],
            "PERDA_%": perda_pct * 100,
            "META_%": meta_pct,
            "RED_MIN": reducao_minima,
            "RED_10": reducao_10,
            "RED_TOTAL": reducao,
            "PERDA_FINAL": perda_final,
            "ATINGIU_META": perda_final <= (perda_inicial - reducao),
            "TOTAL_ACOES": sum(plano.values()),
            **plano
        })

    df_res = pd.DataFrame(resultados)

    # =========================
    # KPIs
    # =========================
    st.markdown("## 📊 Visão Executiva")

    col1, col2, col3 = st.columns(3)

    col1.metric("Instalações", len(df_res))
    col2.metric("Meta Atingida (%)", f"{df_res['ATINGIU_META'].mean()*100:.1f}%")
    col3.metric("Ações Totais", int(df_res["TOTAL_ACOES"].sum()))

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

    # =========================
    # SIMULADOR
    # =========================
    st.markdown("---")
    st.subheader("🛠️ Simulação de Execução")

    inst_sel = st.selectbox("Selecione a instalação", df_res["INSTALACAO"])
    linha = df_res[df_res["INSTALACAO"] == inst_sel].iloc[0]

    perda_inicial = df.loc[df["INSTALACAO"] == inst_sel, "PERDA_INICIAL"].iloc[0]
    meta_perda = perda_inicial - linha["RED_TOTAL"]

    col1, col2, col3 = st.columns(3)

    with col1:
        exec_inclusoes = st.number_input("Inclusões", 0)
    with col2:
        exec_cod100 = st.number_input("Cód 100", 0)
        exec_cod200 = st.number_input("Cód 200", 0)
    with col3:
        exec_exclusoes = st.number_input("Exclusões", 0)
        exec_cod300 = st.number_input("Cód 300", 0)

    ganho_real = (
        exec_inclusoes * 150 +
        exec_cod100 * 120 +
        exec_exclusoes * 100 +
        exec_cod200 * 100 +
        exec_cod300 * 30
    )

    perda_proj = perda_inicial - ganho_real

    st.markdown("### 📉 Resultado")

    col4, col5, col6 = st.columns(3)

    col4.metric("Ganho", f"{ganho_real:.2f}")
    col5.metric("Perda Projetada", f"{perda_proj:.2f}")
    col6.metric("Meta", f"{meta_perda:.2f}")

    if perda_proj <= meta_perda:
        st.success("✅ Meta atingida")
    else:
        st.error(f"❌ Faltam {perda_proj - meta_perda:.2f}")

else:
    st.info("Escolha um modo de entrada para começar.")
