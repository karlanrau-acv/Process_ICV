import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

# Configuração da página para web pública
st.set_page_config(
    page_title="Plataforma ACV Matricial",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Barra lateral com guia rápido para usuários externos
with st.sidebar:
    st.title("🌱 Guia Rápido - ACV")
    st.markdown("""
    Esta ferramenta automatiza o cálculo de **Avaliação do Ciclo de Vida (ACV)** pelo método matricial:
    
    $$q_u = R_u \cdot T^{-1} \cdot y_u$$
    
    **Passo a passo:**
    1. **FT1:** Defina os processos e a demanda final.
    2. **FT2:** Preencha entradas (-) e saídas (+) na Matriz $T$.
    3. **FT3:** Insira emissões e resíduos na Matriz $R_u$.
    4. **FT4:** Analise os resultados, escolha a escala do gráfico e baixe o relatório.
    """)
    st.divider()
    if st.button("🔄 Restaurar Exemplo Padrão"):
        st.session_state.clear()
        st.rerun()

st.title("🌱 Ferramenta Online de Avaliação do Ciclo de Vida (ACV)")
st.markdown("Preencha as etapas nos fluxos abaixo para quantificar o inventário ambiental do seu sistema de produto.")

tab1, tab2, tab3, tab4 = st.tabs([
    "1️⃣ FT1: Escopo e Fronteira",
    "2️⃣ FT2: Matriz Tecnológica (T)",
    "3️⃣ FT3: Matriz Ambiental (R_u)",
    "4️⃣ FT4: Cálculo e Interpretação"
])

# ==========================================
# FLUXO DE TRABALHO 1 (FT1)
# ==========================================
with tab1:
    st.header("Definição do Sistema, Fronteira e Demanda ($y_u$)")
    
    col1, col2 = st.columns(2)
    with col1:
        funcao = st.text_input("Função do Sistema:", value="Colorir paredes internas de uma residência")
    with col2:
        uf = st.text_input("Unidade Funcional (UF):", value="10 kg de tinta aplicada")

    st.subheader("Processos da Cadeia Produtiva e Demanda Final")
    st.info("Marque 'Na Fronteira?' para incluir o processo no cálculo. Use o botão '+' na base da tabela para adicionar novos processos.")

    df_ft1_inicial = pd.DataFrame({
        "Processo": ["Extração de Petróleo", "Produção de Resina", "Fabricação da Tinta"],
        "Na Fronteira?": [False, True, True],
        "Demanda Final (y_u)": [0.0, 0.0, 10.0]
    })

    df_ft1 = st.data_editor(
        df_ft1_inicial,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_ft1"
    )

    df_fronteira = df_ft1[df_ft1["Na Fronteira?"] == True].copy()
    processos_ativos = df_fronteira["Processo"].dropna().tolist()
    y_u_vetor = df_fronteira["Demanda Final (y_u)"].fillna(0.0).tolist()

    st.subheader("Fluxograma Automático do Sistema")
    if len(df_ft1) > 0:
        dot_code = 'digraph G {\n  rankdir=LR;\n  node [shape=box, style="rounded,filled", fontname="Arial"];\n'
        for _, row in df_ft1.iterrows():
            nome = str(row["Processo"]).replace('"', '')
            if nome and nome != "None":
                if row["Na Fronteira?"]:
                    dot_code += f'  "{nome}" [fillcolor="#d4edda", color="#28a745", label="{nome}\\n(Demanda: {row["Demanda Final (y_u)"]})"];\n'
                else:
                    dot_code += f'  "{nome}" [fillcolor="#f8d7da", color="#dc3545", style="dashed,filled", label="{nome}\\n(Fora da Fronteira)"];\n'
        
        nomes_validos = [str(n).replace('"', '') for n in df_ft1["Processo"].dropna() if str(n).strip() != ""]
        for i in range(len(nomes_validos) - 1):
            dot_code += f'  "{nomes_validos[i]}" -> "{nomes_validos[i+1]}";\n'
        dot_code += '}'
        st.graphviz_chart(dot_code)

# ==========================================
# FLUXO DE TRABALHO 2 (FT2)
# ==========================================
with tab2:
    st.header("Construção da Matriz Tecnológica ($T$)")
    st.markdown("**Regra:** Use **valores negativos (-)** para insumos/entradas e **valores positivos (+)** para produtos/saídas.")

    if len(processos_ativos) == 0:
        st.warning("Selecione pelo menos um processo dentro da fronteira no FT1.")
    else:
        n = len(processos_ativos)
        matriz_t_padrao = np.eye(n)
        
        if n == 2 and processos_ativos == ["Produção de Resina", "Fabricação da Tinta"]:
            matriz_t_padrao = np.array([[1.0, -0.4], [0.0, 1.0]])

        df_t_inicial = pd.DataFrame(
            matriz_t_padrao,
            index=[f"Fluxo: {p}" for p in processos_ativos],
            columns=processos_ativos
        )

        df_T = st.data_editor(df_t_inicial, use_container_width=True, key="editor_ft2")
        T_matrix = df_T.fillna(0.0).to_numpy()

        if T_matrix.shape[0] != T_matrix.shape[1]:
            st.error("A Matriz T precisa ser quadrada.")
        elif np.linalg.det(T_matrix) == 0:
            st.error("⚠️ Alerta: O determinante da Matriz T é zero (matriz não inversível). Verifique os balanços de entrada e saída.")
        else:
            st.success("✅ Matriz T válida e pronta para cálculo!")

# ==========================================
# FLUXO DE TRABALHO 3 (FT3)
# ==========================================
with tab3:
    st.header("Construção da Matriz de Intervenção Ambiental ($R_u$)")
    st.markdown("Insira a quantidade de emissões ou resíduos gerados **por unidade de cada processo**.")

    if len(processos_ativos) == 0:
        st.warning("Defina os processos no FT1 primeiro.")
    else:
        n = len(processos_ativos)
        dados_r = np.zeros((2, n))
        if n == 2 and processos_ativos == ["Produção de Resina", "Fabricação da Tinta"]:
            dados_r = np.array([[2.5, 1.2], [0.1, 0.05]])

        df_r_inicial = pd.DataFrame(dados_r, columns=processos_ativos)
        df_r_inicial.insert(0, "Intervenção Ambiental (Unidade)", ["Emissão CO2 (kg)", "Resíduo Sólido (kg)"])

        df_R = st.data_editor(
            df_r_inicial,
            num_rows="dynamic",
            use_container_width=True,
            key="editor_ft3"
        )

# ==========================================
# FLUXO DE TRABALHO 4 (FT4)
# ==========================================
with tab4:
    st.header("Quantificação do Inventário ($q_u$) e Interpretação")

    if len(processos_ativos) == 0:
        st.warning("Complete os fluxos anteriores para visualizar os resultados.")
    else:
        try:
            y_vec = np.array(y_u_vetor, dtype=float).reshape(-1, 1)
            T_mat = df_T.fillna(0.0).to_numpy(dtype=float)
            
            nomes_intervencoes = df_R["Intervenção Ambiental (Unidade)"].fillna("Intervenção sem nome").tolist()
            R_mat = df_R[processos_ativos].fillna(0.0).to_numpy(dtype=float)

            T_inv = np.linalg.inv(T_mat)
            vetor_escala = np.dot(T_inv, y_vec)
            q_u = np.dot(R_mat, vetor_escala)
            contribuicao_matrix = R_mat * vetor_escala.T

            st.subheader(f"Resultados para: {uf}")
            col_res1, col_res2 = st.columns(2)

            with col_res1:
                st.markdown("**Fator de Escala dos Processos ($s = T^{-1} y_u$)**")
                df_escala = pd.DataFrame(vetor_escala, index=processos_ativos, columns=["Fator de Escala"])
                st.dataframe(df_escala, use_container_width=True)

                st.markdown("**Inventário Total ($q_u$)**")
                df_total = pd.DataFrame(q_u, index=nomes_intervencoes, columns=["Carga Total"])
                st.dataframe(df_total, use_container_width=True)

            with col_res2:
                st.markdown("**Contribuição por Processo (Análise de Hotspots)**")
                df_contrib = pd.DataFrame(contribuicao_matrix, index=nomes_intervencoes, columns=processos_ativos)
                st.dataframe(df_contrib, use_container_width=True)

                st.divider()
                modo_grafico = st.selectbox(
                    "📊 Escolha a escala de visualização do gráfico:",
                    options=[
                        "Valores Reais (Exatos)",
                        "Valores Arredondados (Inteiros)",
                        "Normalizado (0% a 100% por Intervenção)",
                        "Escala Logarítmica (Base Log 10)"
                    ]
                )

                df_dados_grafico = df_contrib.copy()

                if modo_grafico == "Valores Arredondados (Inteiros)":
                    df_dados_grafico = df_dados_grafico.round(0).astype(int)
                    formato_texto = '%d'
                    titulo_y = "Quantidade (Inteiros)"
                    usar_log = False
                    modo_barra = "stack"

                elif modo_grafico == "Normalizado (0% a 100% por Intervenção)":
                    somas_linha = df_dados_grafico.sum(axis=1).replace(0, np.nan)
                    df_dados_grafico = df_dados_grafico.div(somas_linha, axis=0).fillna(0) * 100
                    formato_texto = '.1f'
                    titulo_y = "Contribuição Relativa (%)"
                    usar_log = False
                    modo_barra = "stack"

                elif modo_grafico == "Escala Logarítmica (Base Log 10)":
                    formato_texto = '.2e'
                    titulo_y = "Quantidade (Escala Log 10)"
                    usar_log = True
                    modo_barra = "group"

                else:
                    formato_texto = '.2f'
                    titulo_y = "Quantidade Real"
                    usar_log = False
                    modo_barra = "stack"

                df_plot = df_dados_grafico.reset_index().melt(
                    id_vars="index", 
                    var_name="Processo", 
                    value_name="Valor"
                )
                df_plot.rename(columns={"index": "Intervenção"}, inplace=True)

                if usar_log:
                    df_plot = df_plot[df_plot["Valor"] > 0]

                fig = px.bar(
                    df_plot,
                    x="Intervenção",
                    y="Valor",
                    color="Processo",
