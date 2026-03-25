import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Gestão de Perdas", layout="wide")

# =========================
# HEADER
# =========================
st.title("📊 Gestão Inteligente de Perdas")
st.markdown("Planejamento, otimização e simulação operacional de perdas")

# =========================
# SESSION STATE (manual)
# =========================
if "df_manual" not in st.session_state:
    st.session_state.df_manual = pd.DataFrame(columns=[
        "INSTALACAO","REQUERIDA","INJETADA",
        "REVERSA","CONSUMO","ILUMINACAO_PUBLICA"
    ])

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
# ENTRADA
# =========================
st.markdown("## 📥 Entrada de Dados")

modo = st.radio("Modo:", ["Upload de Excel","Manual"])

df = None

# =========================
# UPLOAD
# =========================
if modo == "Upload de Excel":

    st.info("""
Formato obrigatório:
INSTALACAO | REQUERIDA | INJETADA | REVERSA | CONSUMO | ILUMINACAO_PUBLICA
""")

    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file:
        df = pd.read_excel(file)

# =========================
# MANUAL
# =========================
elif modo == "Manual":

    st.subheader("Inserção Manual")

    col1, col2, col3 = st.columns(3)

    with col1:
        inst = st.text_input("Instalação")
        requerida = st.number_input("Requerida", 0.0)

    with col2:
        injetada = st.number_input("Injetada", 0.0)
        reversa = st.number_input("Reversa", 0.0)

    with col3:
        consumo = st.number_input("Consumo", 0.0)
        iluminacao = st.number_input("Iluminação Pública", 0.0)

    if st.button("➕ Adicionar"):
        if inst:
            nova = pd.DataFrame([{
                "INSTALACAO": inst,
                "REQUERIDA": requerida,
                "INJETADA": injetada,
                "REVERSA": reversa,
                "CONSUMO": consumo,
                "ILUMINACAO_PUBLICA": iluminacao
            }])
            st.session_state.df_manual = pd.concat([st.session_state.df_manual, nova], ignore_index=True)

    if st.button("🗑️ Limpar"):
        st.session_state.df_manual = st.session_state.df_manual.iloc[0:0]

    st.dataframe(st.session_state.df_manual)

    if not st.session_state.df_manual.empty:
        if st.button("🚀 Rodar Análise"):
            df = st.session_state.df_manual.copy()

# =========================
# PROCESSAMENTO
# =========================
if df is not None:

    df.columns = df.columns.str.strip().str.upper()

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

        perda_pct = perda / total
        faixa = math.ceil(perda_pct * 100)

        meta_pct = curva.get(faixa, 0)

        # METAS
        red_min = perda * (meta_pct/100)
        red_10 = max(0, perda - 0.10*total)
        red_total = max(red_min, red_10)

        # OTIMIZADOR
        ganho = 0
        plano = {}

        acoes = [
            ("Inclusoes",150),
            ("Cod100",120),
            ("Exclusoes",100),
            ("Cod200",100),
            ("Cod300",30)
        ]

        acoes.sort(key=lambda x: x[1], reverse=True)

        for nome, impacto in acoes:
            if ganho >= red_total:
                break
            qtd = math.ceil((red_total - ganho)/impacto)
            plano[nome] = qtd
            ganho += qtd * impacto

        perda_final = perda - ganho

        resultados.append({
            "INSTALACAO": row["INSTALACAO"],
            "PERDA_%": perda_pct*100,
            "RED_MIN": red_min,
            "RED_10": red_10,
            "RED_TOTAL": red_total,
            "PERDA_FINAL": perda_final,
            "ATINGIU_META": perda_final <= (perda - red_total),
            "TOTAL_ACOES": sum(plano.values()),
            **plano
        })

    df_res = pd.DataFrame(resultados)

    # =========================
    # DASHBOARD
    # =========================
    st.markdown("## 📊 Visão Executiva")

    c1,c2,c3 = st.columns(3)
    c1.metric("Instalações", len(df_res))
    c2.metric("Meta Atingida", f"{df_res['ATINGIU_META'].mean()*100:.1f}%")
    c3.metric("Ações Totais", int(df_res["TOTAL_ACOES"].sum()))

    st.markdown("---")

    st.subheader("🔥 Ranking")
    st.dataframe(df_res.sort_values("PERDA_%", ascending=False))

    st.subheader("📈 Gráficos")
    st.bar_chart(df_res.set_index("INSTALACAO")["PERDA_%"])
    st.bar_chart(df_res.set_index("INSTALACAO")["TOTAL_ACOES"])

    st.download_button("📥 Download", df_res.to_csv(index=False), "resultado.csv")

    # =========================
    # SIMULADOR
    # =========================
    st.markdown("---")
    st.subheader("🛠️ Simulação")

    inst_sel = st.selectbox("Instalação", df_res["INSTALACAO"])

    base = df[df["INSTALACAO"] == inst_sel].iloc[0]

    perda = (
        base["REQUERIDA"] + base["INJETADA"]
        - base["REVERSA"] - base["CONSUMO"]
        - base["ILUMINACAO_PUBLICA"]
    )

    meta = perda - df_res[df_res["INSTALACAO"]==inst_sel]["RED_TOTAL"].iloc[0]

    c1,c2,c3 = st.columns(3)

    with c1:
        inc = st.number_input("Inclusões",0)
    with c2:
        c100 = st.number_input("Cod100",0)
        c200 = st.number_input("Cod200",0)
    with c3:
        exc = st.number_input("Exclusões",0)
        c300 = st.number_input("Cod300",0)

    ganho = inc*150 + c100*120 + exc*100 + c200*100 + c300*30
    perda_proj = perda - ganho

    st.markdown("### Resultado")

    r1,r2,r3 = st.columns(3)
    r1.metric("Ganho", ganho)
    r2.metric("Perda Final", perda_proj)
    r3.metric("Meta", meta)

    if perda_proj <= meta:
        st.success("Meta atingida")
    else:
        st.error(f"Faltam {perda_proj-meta:.2f}")

else:
    st.info("Escolha um modo e insira dados.")
