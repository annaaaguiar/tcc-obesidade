
import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(
    layout="wide",
    page_title="Dashboard de Saúde - Análise de Risco",
)

# --- Constantes Globais ---
COLOR_MAP = {'Homem': '#1f77b4', 'Mulher': '#e377c2'}
LABELS_IMC = ['Abaixo do Peso', 'Peso Normal', 'Sobrepeso', 'Obesidade Grau I', 'Obesidade Grau II', 'Obesidade Grau III']
LABELS_SED = ['Baixo (até 5h)', 'Moderado (5h a 8h)', 'Alto (acima de 8h)']

# --- Carregamento e Processamento dos Dados (com Cache) ---
@st.cache_data
def load_data():
    """
    Carrega, une, limpa e pré-processa todos os dataframes.
    A anotação @st.cache_data garante que esta função complexa execute apenas uma vez.
    """
    try:
        df_demo = pd.read_csv("DEMO.csv", on_bad_lines='skip', sep=';')
        df_bmx = pd.read_csv("BMX.csv", on_bad_lines='skip', sep=';')
        df_bpq = pd.read_csv("BPQ.csv", on_bad_lines='skip', sep=';')
        df_paq = pd.read_csv("PAQ.csv", on_bad_lines='skip', sep=';')
        df_tchol = pd.read_csv("TCHOL.csv", on_bad_lines='skip', sep=';')
        df_trigly = pd.read_csv("TRIGLY.csv", on_bad_lines='skip', sep=';')
        df_hdl = pd.read_csv("HDL.csv", on_bad_lines='skip', sep=';')

        df_demo = df_demo.rename(columns={'SEQN': 'id_participante', 'RIDAGEYR': 'idade_anos', 'RIAGENDR': 'genero'})
        df_bmx = df_bmx.rename(columns={'SEQN': 'id_participante', 'BMXWT': 'peso_kg', 'BMXHT': 'altura_cm','BMXBMI': 'imc', 'BMXWAIST': 'circunferencia_cintura_cm'})
        df_paq = df_paq.rename(columns={'SEQN': 'id_participante', 'PAD680': 'tempo_sentado_min'})
        df_bpq = df_bpq.rename(columns={'SEQN': 'id_participante', 'BPQ020': 'historico_pressao_alta','BPQ080': 'historico_colesterol_alto', 'BPQ090D': 'historico_doenca_cardiaca'})
        df_tchol = df_tchol.rename(columns={'SEQN': 'id_participante', 'LBXTC': 'colesterol_total'})
        df_trigly = df_trigly.rename(columns={'SEQN': 'id_participante', 'LBDLDL': 'ldl'})
        df_hdl = df_hdl.rename(columns={'SEQN': 'id_participante', 'LBDHDD': 'hdl'})

        df_merged = df_demo[['id_participante', 'idade_anos', 'genero']].merge(df_bmx[['id_participante', 'imc']], on='id_participante', how='inner')
        df_merged = df_merged.merge(df_paq[['id_participante', 'tempo_sentado_min']], on='id_participante', how='inner')
        df_merged = df_merged.merge(df_bpq[['id_participante', 'historico_pressao_alta', 'historico_colesterol_alto', 'historico_doenca_cardiaca']], on='id_participante', how='inner')
        df_merged = df_merged.merge(df_tchol[['id_participante', 'colesterol_total']], on='id_participante', how='left')
        df_merged = df_merged.merge(df_trigly[['id_participante', 'ldl']], on='id_participante', how='left')
        df_merged = df_merged.merge(df_hdl[['id_participante', 'hdl']], on='id_participante', how='left')

        colunas_essenciais = ['imc', 'colesterol_total', 'ldl', 'hdl', 'tempo_sentado_min']
        df_merged.dropna(subset=colunas_essenciais, inplace=True)
        
        df_merged['genero'] = df_merged['genero'].replace({1: 'Homem', 2: 'Mulher'})
        df_merged['historico_doenca_cardiaca'] = df_merged['historico_doenca_cardiaca'].fillna(9)
        df_merged['idade_anos'] = pd.to_numeric(df_merged['idade_anos'], errors='coerce')
        df_merged['tempo_sentado_min'] = pd.to_numeric(df_merged['tempo_sentado_min'], errors='coerce')
        df_merged['tempo_sentado_min'] = df_merged['tempo_sentado_min'].fillna(df_merged['tempo_sentado_min'].median())

        bins_imc = [0, 18.5, 24.9, 29.9, 34.9, 39.9, float('inf')]
        df_merged['obesidade_class'] = pd.cut(df_merged['imc'], bins=bins_imc, labels=LABELS_IMC, right=False)

        sedentary_bins = [0, 300, 480, float('inf')]
        df_merged['sedentarismo_nivel'] = pd.cut(df_merged['tempo_sentado_min'], bins=sedentary_bins, labels=LABELS_SED, right=False)
        if not pd.api.types.is_categorical_dtype(df_merged['sedentarismo_nivel']):
            df_merged['sedentarismo_nivel'] = df_merged['sedentarismo_nivel'].astype('category')
        df_merged['sedentarismo_nivel'] = df_merged['sedentarismo_nivel'].cat.add_categories(['Não Informado']).fillna('Não Informado')

        df_merged['historico_pressao_alta_cat'] = df_merged['historico_pressao_alta'].replace({1.0: 'Sim', 2.0: 'Não', 9.0: 'Não Sabe'})
        df_merged['historico_colesterol_alto_cat'] = df_merged['historico_colesterol_alto'].replace({1.0: 'Sim', 2.0: 'Não', 7.0: 'Não Sabe', 9.0: 'Não Sabe'}).fillna('Não Sabe')
        df_merged['historico_doenca_cardiaca_cat'] = df_merged['historico_doenca_cardiaca'].replace({1.0: 'Sim', 2.0: 'Não', 7.0: 'Não Sabe', 9.0: 'Não Sabe'}).fillna('Não Sabe')

        return df_merged

    except FileNotFoundError as e:
        st.error(f"Erro ao carregar o arquivo: {e}. Certifique-se de que todos os arquivos CSV estão na mesma pasta que o script `app.py`.")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

# --- Barra Lateral de Filtros ---
st.sidebar.header("Filtros Interativos")
genero_selecionado = st.sidebar.multiselect("Gênero", options=df['genero'].unique(), default=df['genero'].unique())
idade_min = int(df['idade_anos'].min())
idade_max = int(df['idade_anos'].max())
faixa_etaria = st.sidebar.slider("Faixa Etária", min_value=idade_min, max_value=idade_max, value=(idade_min, idade_max))
obesidade_selecionada = st.sidebar.multiselect("Classificação de Obesidade", options=df['obesidade_class'].cat.categories, default=df['obesidade_class'].cat.categories)
sedentarismo_selecionado = st.sidebar.multiselect("Nível de Sedentarismo", options=df['sedentarismo_nivel'].cat.categories, default=df['sedentarismo_nivel'].cat.categories)

df_filtrado = df[
    (df['genero'].isin(genero_selecionado)) &
    (df['idade_anos'].between(faixa_etaria[0], faixa_etaria[1])) &
    (df['obesidade_class'].isin(obesidade_selecionada)) &
    (df['sedentarismo_nivel'].isin(sedentarismo_selecionado))
]

# --- Título Principal ---
st.title("Dashboard Interativo: Análise de Obesidade, Sedentarismo e Riscos Associados")
st.markdown(f"Analisando **{len(df_filtrado)}** participantes selecionados.")

# --- Abas para Organização ---
tab1, tab2, tab3, tab4 = st.tabs(["Resumo da Amostra", "Análise de Obesidade", "Análise de Sedentarismo", "Conclusão e Risco"])

# --- ABA 1: RESUMO ---
with tab1:
    st.header("1. Resumo da Amostra")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Idade Média", f"{df_filtrado['idade_anos'].mean():.1f} anos")
    col2.metric("Idade Mínima", f"{df_filtrado['idade_anos'].min():.0f} anos")
    col3.metric("Idade Máxima", f"{df_filtrado['idade_anos'].max():.0f} anos")
    col4.metric("Desvio Padrão (Idade)", f"{df_filtrado['idade_anos'].std():.1f}")
    
    st.markdown("---")
    
    with st.expander("Gráficos de Distribuição Percentual", expanded=True):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.subheader("Distribuição por Gênero")
            genero_counts = df_filtrado['genero'].value_counts()
            fig_genero = px.pie(values=genero_counts.values, names=genero_counts.index, hole=0.3, color=genero_counts.index, color_discrete_map=COLOR_MAP)
            st.plotly_chart(fig_genero, use_container_width=True)
        with col_b:
            st.subheader("Percentual por Obesidade")
            obesidade_counts = df_filtrado['obesidade_class'].value_counts()
            fig_obesidade = px.pie(values=obesidade_counts.values, names=obesidade_counts.index, hole=0.3)
            st.plotly_chart(fig_obesidade, use_container_width=True)
        with col_c:
            st.subheader("Percentual de Sedentarismo")
            sedentarismo_counts = df_filtrado['sedentarismo_nivel'].value_counts()
            fig_sedentarismo = px.pie(values=sedentarismo_counts.values, names=sedentarismo_counts.index, hole=0.3)
            st.plotly_chart(fig_sedentarismo, use_container_width=True)

st.markdown("### Fontes de Dados")
st.markdown("- Base de dados NHANES [https://www.cdc.gov/nchs/nhanes/index.htm](https://www.cdc.gov/nchs/nhanes/index.htm)")

# --- ABA 2: OBESIDADE ---
with tab2:
    st.header("2. Análise de Obesidade")

    with st.expander("Distribuição de IMC por Gênero", expanded=True):
        fig_imc_genero = px.histogram(df_filtrado, x='obesidade_class', color='genero', barmode='group',
                                      category_orders={'obesidade_class': LABELS_IMC},
                                      color_discrete_map=COLOR_MAP)
        st.plotly_chart(fig_imc_genero, use_container_width=True)

    with st.expander("Tabelas e Gráficos de Associação com Obesidade"):
        def plotar_associacao(df, var_principal, var_secundaria, titulo):
            st.subheader(titulo)
            crosstab = pd.crosstab(df[var_principal], df[var_secundaria], normalize='index', dropna=False) * 100
            st.dataframe(crosstab.round(1))
            
            crosstab_plot = crosstab.reset_index()
            df_melted = crosstab_plot.melt(id_vars=var_principal, var_name=var_secundaria, value_name='Percentual')
            
            fig = px.bar(df_melted, x=var_principal, y='Percentual', color=var_secundaria, barmode='group', text_auto='.2s')
            st.plotly_chart(fig, use_container_width=True)
            
            csv = crosstab.to_csv().encode('utf-8')
            st.download_button(label=f"Exportar Tabela '{titulo}'", data=csv, file_name=f'obesidade_x_{var_secundaria}.csv', mime='text/csv')
            st.markdown("---")

        plotar_associacao(df_filtrado, 'obesidade_class', 'historico_pressao_alta_cat', 'Obesidade x Pressão Alta')
        plotar_associacao(df_filtrado, 'obesidade_class', 'historico_colesterol_alto_cat', 'Obesidade x Colesterol Alto')
        plotar_associacao(df_filtrado, 'obesidade_class', 'historico_doenca_cardiaca_cat', 'Obesidade x Doença Cardíaca')

    with st.expander("Boxplots de Perfil Lipídico por Classe de Obesidade"):
        col_box1, col_box2, col_box3 = st.columns(3)
        with col_box1:
            fig_hdl = px.box(df_filtrado, x='obesidade_class', y='hdl', color='obesidade_class', title="HDL")
            st.plotly_chart(fig_hdl, use_container_width=True)
        with col_box2:
            fig_ldl = px.box(df_filtrado, x='obesidade_class', y='ldl', color='obesidade_class', title="LDL")
            st.plotly_chart(fig_ldl, use_container_width=True)
        with col_box3:
            fig_tchol = px.box(df_filtrado, x='obesidade_class', y='colesterol_total', color='obesidade_class', title="Colesterol Total")
            st.plotly_chart(fig_tchol, use_container_width=True)

# --- ABA 3: SEDENTARISMO ---
with tab3:
    st.header("3. Análise de Sedentarismo")

    with st.expander("Associações com Sedentarismo"):
        plotar_associacao(df_filtrado, 'sedentarismo_nivel', 'obesidade_class', 'Sedentarismo x Obesidade')
        plotar_associacao(df_filtrado, 'sedentarismo_nivel', 'historico_pressao_alta_cat', 'Sedentarismo x Pressão Alta')
        plotar_associacao(df_filtrado, 'sedentarismo_nivel', 'historico_colesterol_alto_cat', 'Sedentarismo x Colesterol Alto')
    
    with st.expander("Boxplots de Perfil Lipídico por Nível de Sedentarismo"):
        col_box_sed1, col_box_sed2, col_box_sed3 = st.columns(3)
        with col_box_sed1:
            fig_hdl_sed = px.box(df_filtrado, x='sedentarismo_nivel', y='hdl', color='sedentarismo_nivel', title="HDL")
            st.plotly_chart(fig_hdl_sed, use_container_width=True)
        with col_box_sed2:
            fig_ldl_sed = px.box(df_filtrado, x='sedentarismo_nivel', y='ldl', color='sedentarismo_nivel', title="LDL")
            st.plotly_chart(fig_ldl_sed, use_container_width=True)
        with col_box_sed3:
            fig_tchol_sed = px.box(df_filtrado, x='sedentarismo_nivel', y='colesterol_total', color='sedentarismo_nivel', title="Colesterol Total")
            st.plotly_chart(fig_tchol_sed, use_container_width=True)

# --- ABA 4: CONCLUSÃO ---
with tab4:
    st.header("5. Conclusão e Segmento de Alto Risco")

    st.markdown("""
    ### Quem Apresenta Maior Risco Potencial?
    Com base na análise interativa dos dados, o grupo de maior risco é composto por **participantes obesos (especialmente Grau II e III) que também apresentam um alto nível de sedentarismo (mais de 8 horas sentados por dia).**
    Este grupo tende a exibir um perfil lipídico mais desfavorável e uma maior prevalência de histórico de pressão e colesterol altos, fatores associados a maior risco para eventos cardiovasculares.
    """)
    st.info("Dica: Use os filtros na barra lateral para explorar diferentes segmentos e validar estas conclusões.")
    st.markdown("---")

    st.subheader("Explorar Participantes com Alto Risco")
    
    if st.checkbox("Clique aqui para filtrar participantes com Obesidade Grau II/III E alto nível de sedentarismo"):
        
        df_alto_risco = df_filtrado[
            (df_filtrado['obesidade_class'].isin(['Obesidade Grau II', 'Obesidade Grau III'])) &
            (df_filtrado['sedentarismo_nivel'] == 'Alto (acima de 8h)')
        ]
        
        if not df_alto_risco.empty:
            st.success(f"**Encontrados {len(df_alto_risco)} participantes de alto risco dentro da seleção atual.**")
            
            colunas_risco = [
                'idade_anos', 'genero', 'imc', 'obesidade_class', 'tempo_sentado_min', 
                'sedentarismo_nivel', 'historico_pressao_alta_cat', 'historico_colesterol_alto_cat',
                'hdl', 'ldl', 'colesterol_total'
            ]
            st.dataframe(df_alto_risco[colunas_risco])
            
            csv_risco = df_alto_risco[colunas_risco].to_csv().encode('utf-8')
            st.download_button(
                label="Exportar Lista de Alto Risco como CSV",
                data=csv_risco,
                file_name='participantes_alto_risco.csv',
                mime='text/csv',
            )
        else:
            st.warning("Nenhum participante com este perfil de alto risco foi encontrado na seleção de filtros atual. Tente ampliar os filtros na barra lateral (faixa etária, etc.).")

