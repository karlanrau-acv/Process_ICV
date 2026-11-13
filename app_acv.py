import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Plataforma ACV Matricial", page_icon="🌱", layout="wide")

with st.sidebar:
    st.title("🌱 Guia Rápido - ACV")
    st.markdown("Cálculo matricial: $q_u = R_u \cdot T^{-1} \cdot y_u$")
    if st.button("🔄 Restaurar Exemplo Padrão"):
        st.session_state.clear()
        st.rerun()

st.title("🌱 Ferramenta Online de Avaliação do Ciclo de Vida (ACV)")
tab1, tab2, tab3, tab4 = st.tabs([
    "1️⃣ FT1: Escopo e Fronteira",
    "2️⃣ FT2: Matriz Tecnológica (T)",
    "3️⃣ FT3: Matriz Ambiental (R_u)",
    "4️⃣ FT4: Cálculo e Interpretação"
])

# FT1
with tab1:
    col1, col2 = st.columns(2)
    funcao = col1.text_input("Função do Sistema:", value="Colorir paredes internas de uma residência")
    uf = col2.text_input("Unidade Funcional (UF):", value="10 kg de tinta aplicada")

    df_ft1_ini = pd.DataFrame({
        "Processo": ["Extração de Petróleo", "Produção de Resina", "Fabricação da Tinta"],
        "Na Fronteira?": [False, True, True],
        "Demanda Final (y_u)": [0.0, 0.0, 10.0]
    })
    df_ft1 = st.data_editor(df_ft1_ini, num_rows="dynamic", use_container_width=True, key="ft1")

    df_front = df_ft1[df_ft1["Na Fronteira?"] == True].copy()
    proc_ativos = df_front["Processo"].dropna().tolist()
    y_u_vec = df_front["Demanda Final (y_u)"].fillna(0.0).tolist()

    if len(df_ft1) > 0:
        dot = 'digraph G { rankdir=LR; node [shape=box, style="rounded,filled"];\n'
        for _, r in df_ft1.iterrows():
            nome = str(r["Processo"]).replace('"', '')
            if nome and nome != "None":
                cor = 'fillcolor="#d4edda", color="#28a745"' if r["Na Fronteira?"] else 'fillcolor="#f8d7da", color="#dc3545", style="dashed,filled"'
                dot += f' "{nome}" [{cor}, label="{nome}\\n(y_u: {r["Demanda Final (y_u)"]})"];\n'
        validos = [str(n).replace('"', '') for n in df_ft1["Processo"].dropna() if str(n).strip() != ""]
        for i in range(len(validos) - 1):
            dot += f' "{validos[i]}" -> "{validos[i+1]}";\n'
        st.graphviz_chart(dot + '}')

# FT2
with tab2:
    st.markdown("**Regra:** Entradas/insumos são **negativos (-)** e saídas/produtos são **positivos (+)**.")
    if not proc_ativos:
        st.warning("Selecione processos na fronteira no FT1.")
    else:
        n = len(proc_ativos)
        mat_t = np.array([[1.0, -0.4], [0.0, 1.0]]) if (n == 2 and proc_ativos == ["Produção de Resina", "Fabricação da Tinta"]) else np.eye(n)
        df_T = st.data_editor(pd.DataFrame(mat_t, index=[f"Fluxo: {p}" for p in proc_ativos], columns=proc_ativos), use_container_width=True, key="ft2")
        T_mat = df_T.fillna(0.0).to_numpy()
        if T_mat.shape[0] != T_mat.shape[1] or np.linalg.det(T_mat) == 0:
            st.error("⚠️ Matriz T inválida ou não inversível.")
        else:
            st.success("✅ Matriz T válida!")

# FT3
with tab3:
    if not proc_ativos:
        st.warning("Defina os processos no FT1 primeiro.")
    else:
        n = len(proc_ativos)
        mat_r = np.array([[2.5, 1.2], [0.1, 0.05]]) if (n == 2 and proc_ativos == ["Produção de Resina", "Fabricação da Tinta"]) else np.zeros((2, n))
        df_r_ini = pd.DataFrame(mat_r, columns=proc_ativos)
        df_r_ini.insert(0, "Intervenção Ambiental", ["Emissão CO2 (kg)", "Resíduo Sólido (kg)"])
        df_R = st.data_editor(df_r_ini, num_rows="dynamic", use_container_width=True, key="ft3")

# FT4
with tab4:
    if not proc_ativos:
        st.warning("Complete os fluxos anteriores.")
    else:
        try:
            y_vec = np.array(y_u_vec, dtype=float).reshape(-1, 1)
            T_mat = df_T.fillna(0.0).to_numpy(dtype=float)
            nomes_int = df_R["Intervenção Ambiental"].fillna("Sem nome").tolist()
            R_mat = df_R[proc_ativos].fillna(0.0).to_numpy(dtype=float)

            s_vec = np.dot(np.linalg.inv(T_mat), y_vec)
            q_u = np.dot(R_mat, s_vec)
            contrib = R_mat * s_vec.T

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Fator de Escala ($s = T^{-1} y_u$)**")
                st.dataframe(pd.DataFrame(s_vec, index=proc_ativos, columns=["Escala"]), use_container_width=True)
                st.markdown("**Inventário Total ($q_u$)**")
                st.dataframe(pd.DataFrame(q_u, index=nomes_int, columns=["Total"]), use_container_width=True)

            with c2:
                st.markdown("**Contribuição por Processo**")
                df_contrib = pd.DataFrame(contrib, index=nomes_int, columns=proc_ativos)
                st.dataframe(df_contrib, use_container_width=True)

                modo = st.selectbox("📊 Escala do Gráfico:", [
                    "Valores Reais (Exatos)",
                    "Valores Arredondados (Inteiros)",
                    "Normalizado (0% a 100%)",
                    "Escala Logarítmica (Base Log 10)"
                ])

                df_g = df_contrib.copy()
                fmt, eixo_y, is_log, b_mode = '.2f', "Quantidade Real", False, "stack"

                if modo == "Valores Arredondados (Inteiros)":
                    df_g = df_g.round(0).astype(int)
                    fmt, eixo_y = '%d', "Quantidade (Inteiros)"
                elif modo == "Normalizado (0% a 100%)":
                    somas = df_g.sum(axis=1).replace(0, np.nan)
                    df_g = df_g.div(somas, axis=0).fillna(0) * 100
                    fmt, eixo_y = '.1f', "Contribuição (%)"
                elif modo == "Escala Logarítmica (Base Log 10)":
                    fmt, eixo_y, is_log, b_mode = '.2e', "Log 10", True, "group"

                df_plot = df_g.reset_index().melt(id_vars="index", var_name="Processo", value_name="Valor")
                df_plot.rename(columns={"index": "Intervenção"}, inplace=True)
                if is_log:
                    df_plot = df_plot[df_plot["Valor"] > 0]

                fig = px.bar(df_plot, x="Intervenção", y="Valor", color="Processo", barmode=b_mode, log_y=is_log, text_auto=fmt, labels={"Valor": eixo_y})
                if modo == "Normalizado (0% a 100%)":
                    fig.update_traces(texttemplate='%{y:.1f}%')
                st.plotly_chart(fig, use_container_width=True)

            st.download_button("📥 Baixar CSV", df_contrib.to_csv().encode('utf-8'), "inventario_acv.csv", "text/csv")
        except Exception as e:
            st.error(f"Erro no cálculo: {e}")
