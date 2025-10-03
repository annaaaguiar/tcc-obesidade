import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(
    layout="wide",
    page_title="Dashboard de Saúde - Análise de Risco",
    page_icon="🧬",
)

# --- Constantes Globais ---
COLOR_MAP = {'Homem': '#1f77b4', 'Mulher': '#e377c2'}
LABELS_IMC = ['Abaixo do Peso', 'Peso Normal', 'Sobrepeso', 'Obesidade Grau I', 'Obesidade Grau II', 'Obesidade Grau III']
LABELS_SED = ['Baixo (até 5h)', 'Moderado (5h a 8h)', 'Alto (acima de 8h)', 'Não Informado']

# --- Carregamento e Processamento dos Dados (com Cache) ---
@st.cache_data
def load_data():
    """
    Carrega, une, limpa e pré-processa todos os dataframes usando a lógica de análise completa.
    """
    try:
        df_demo = pd.read_csv("DEMO.csv", on_bad_lines='skip', sep=';')
        df_bmx = pd.read_csv("BMX.csv", on_bad_lines='skip', sep=';')
        df_bpq = pd.read_csv("BPQ.csv", on_bad_lines='skip', sep=';')
        df_paq = pd.read_csv("PAQ.csv", on_bad_lines='skip', sep=';')
        df_tchol = pd.read_csv("TCHOL.csv", on_bad_lines='skip', sep=';')
        df_trigly = pd.read_csv("TRIGLY.csv", on_bad_lines='skip', sep=';')
        df_hdl = pd.read_csv("HDL.csv", on_bad_lines='skip', sep=';')
        df_ghb = pd.read_csv("GHB.csv", on_bad_lines='skip', sep=';')
        df_hscrp = pd.read_csv("HSCRP.csv", on_bad_lines='skip', sep=';')

        df_demo = df_demo.rename(columns={'SEQN': 'id_participante', 'RIDAGEYR': 'idade_anos', 'RIAGENDR': 'genero'})
        df_bmx = df_bmx.rename(columns={'SEQN': 'id_participante', 'BMXWT': 'peso_kg', 'BMXHT': 'altura_cm','BMXBMI': 'imc', 'BMXWAIST': 'circunferencia_cintura_cm'})
        df_paq = df_paq.rename(columns={'SEQN': 'id_participante', 'PAD680': 'tempo_sentado_min'})
        df_bpq = df_bpq.rename(columns={'SEQN': 'id_participante', 'BPQ020': 'historico_pressao_alta','BPQ080': 'historico_colesterol_alto', 'BPQ090D': 'historico_doenca_cardiaca'})
        df_tchol = df_tchol.rename(columns={'SEQN': 'id_participante', 'LBXTC': 'colesterol_total'})
        df_trigly = df_trigly.rename(columns={'SEQN': 'id_participante', 'LBDLDL': 'ldl'})
        df_hdl = df_hdl.rename(columns={'SEQN': 'id_participante', 'LBDHDD': 'hdl'})
        df_ghb = df_ghb.rename(columns={'SEQN': 'id_participante', 'LBXGH': 'ghb'})
        df_hscrp = df_hscrp.rename(columns={'SEQN': 'id_participante', 'LBXHSCRP': 'hscrp'})

        df_merged = df_demo.merge(df_bmx, on='id_participante', how='inner') \
            .merge(df_paq, on='id_participante', how='inner') \
            .merge(df_bpq, on='id_participante', how='inner') \
            .merge(df_tchol, on='id_participante', how='left') \
            .merge(df_trigly, on='id_participante', how='left') \
            .merge(df_hdl, on='id_participante', how='left') \
            .merge(df_ghb, on='id_participante', how='left') \
            .merge(df_hscrp, on='id_participante', how='left')

        df_merged['genero'] = df_merged['genero'].replace({1: 'Homem', 2: 'Mulher'})
        df_merged['historico_doenca_cardiaca'] = df_merged['historico_doenca_cardiaca'].fillna(9)
        df_merged['idade_anos'] = pd.to_numeric(df_merged['idade_anos'], errors='coerce')
        df_merged['tempo_sentado_min'] = pd.to_numeric(df_merged['tempo_sentado_min'], errors='coerce')
        df_merged['tempo_sentado_min'] = df_merged['tempo_sentado_min'].fillna(df_merged['tempo_sentado_min'].median())

        colunas_essenciais = ['imc', 'peso_kg', 'altura_cm', 'circunferencia_cintura_cm', 'colesterol_total', 'ldl', 'hdl', 'ghb', 'hscrp']
        df_merged.dropna(subset=[col for col in colunas_essenciais if col in df_merged.columns], inplace=True)

        bins_imc = [0, 18.5, 24.9, 29.9, 34.9, 39.9, float('inf')]
        df_merged['obesidade_class'] = pd.cut(df_merged['imc'], bins=bins_imc, labels=LABELS_IMC, right=False)

        def classificar_sedentarismo(minutos):
            if pd.isna(minutos):
                return 'Não Informado'
            if minutos < 300:
                return 'Baixo (até 5h)'
            elif 300 <= minutos < 480:
                return 'Moderado (5h a 8h)'
            else:
                return 'Alto (acima de 8h)'

        df_merged['sedentarismo_nivel'] = df_merged['tempo_sentado_min'].apply(classificar_sedentarismo)
        df_merged['sedentarismo_nivel'] = pd.Categorical(df_merged['sedentarismo_nivel'], categories=LABELS_SED, ordered=True)

        df_merged['historico_pressao_alta_cat'] = df_merged['historico_pressao_alta'].replace({1.0: 'Sim', 2.0: 'Não', 9.0: 'Não Sabe'})
        df_merged['historico_colesterol_alto_cat'] = df_merged['historico_colesterol_alto'].replace({1.0: 'Sim', 2.0: 'Não', 7.0: 'Não Sabe', 9.0: 'Não Sabe'}).fillna('Não Sabe')
        df_merged['historico_doenca_cardiaca_cat'] = df_merged['historico_doenca_cardiaca'].replace({1.0: 'Sim', 2.0: 'Não', 7.0: 'Não Sabe', 9.0: 'Não Sabe'}).fillna('Não Sabe')

        def classificar_colesterol_total(valor):
            if pd.isna(valor):
                return 'Não disponível'
            elif valor < 200:
                return 'Normal'
            elif valor < 240:
                return 'Limítrofe'
            else:
                return 'Alto'

        df_merged['colesterol_total_class'] = df_merged['colesterol_total'].apply(classificar_colesterol_total)

        def classificar_ldl(valor):
            if pd.isna(valor):
                return 'Não disponível'
            elif valor < 100:
                return 'Ótimo'
            elif valor < 130:
                return 'Próximo do ideal'
            elif valor < 160:
                return 'Limítrofe'
            elif valor < 190:
                return 'Alto'
            else:
                return 'Muito alto'

        df_merged['ldl_class'] = df_merged['ldl'].apply(classificar_ldl)

        def classificar_hdl(row):
            valor, genero = row['hdl'], row['genero']
            if pd.isna(valor):
                return 'Não disponível'
            if genero == 'Homem':
                if valor < 40:
                    return 'Baixo'
                else:
                    return 'Normal'
            else:  # Mulher
                if valor < 50:
                    return 'Baixo'
                else:
                    return 'Normal'

        df_merged['hdl_class'] = df_merged.apply(classificar_hdl, axis=1)
        return df_merged

    except FileNotFoundError as e:
        st.error(f"Erro ao carregar o arquivo: {e}. Certifique-se de que todos os arquivos CSV estão na mesma pasta que o script.")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("Nenhum dado encontrado após a aplicação dos filtros rigorosos. Verifique se todos os arquivos CSV necessários estão presentes.")
    st.stop()

# --- Barra Lateral de Filtros ---
st.sidebar.header("Filtros Interativos")

genero_selecionado = st.sidebar.multiselect(
    "Gênero",
    options=df['genero'].unique(),
    default=df['genero'].unique()
)

idade_min = int(df['idade_anos'].min())
idade_max = int(df['idade_anos'].max())
faixa_etaria = st.sidebar.slider(
    "Faixa Etária",
    min_value=idade_min,
    max_value=idade_max,
    value=(idade_min, idade_max)
)

obesidade_selecionada = st.sidebar.multiselect(
    "Classificação de Obesidade",
    options=df['obesidade_class'].cat.categories,
    default=df['obesidade_class'].cat.categories
)

sedentarismo_selecionado = st.sidebar.multiselect(
    "Nível de Sedentarismo",
    options=df['sedentarismo_nivel'].cat.categories,
    default=df['sedentarismo_nivel'].cat.categories
)

df_filtrado = df[
    (df['genero'].isin(genero_selecionado)) &
    (df['idade_anos'].between(faixa_etaria[0], faixa_etaria[1])) &
    (df['obesidade_class'].isin(obesidade_selecionada)) &
    (df['sedentarismo_nivel'].isin(sedentarismo_selecionado))
]

# --- Título Principal ---
st.title("Dashboard Interativo: Análise de Obesidade, Sedentarismo e Riscos Associados")
st.markdown(f"Analisando **{len(df_filtrado)}** participantes selecionados (base de dados completa).")

# --- Abas para Organização ---
tab1, tab2, tab3, tab4 = st.tabs(["Resumo da Amostra", "Análise de Obesidade", "Análise de Sedentarismo", "Conclusão e Risco"])

def plotar_associacao(df, var_principal, var_secundaria, titulo):
    st.subheader(titulo)
    crosstab = pd.crosstab(df[var_principal], df[var_secundaria], normalize='index', dropna=False) * 100
    crosstab_para_exibir = crosstab.reset_index()

    colunas_de_percentual = {col: '{:.1f}%' for col in crosstab.columns}
    st.dataframe(
        crosstab_para_exibir.style.format(colunas_de_percentual),
        hide_index=True
    )

    df_melted = crosstab_para_exibir.melt(id_vars=var_principal, var_name=var_secundaria, value_name='Percentual')
    
    fig_params = {
        'x': var_principal,
        'y': 'Percentual',
        'color': var_secundaria,
        'barmode': 'group',
    }
    if pd.api.types.is_categorical_dtype(df[var_principal]):
        fig_params['category_orders'] = {var_principal: df[var_principal].cat.categories.tolist()}

    fig = px.bar(df_melted, **fig_params)
    fig.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

    csv = crosstab.to_csv().encode('utf-8')
    st.download_button(
        label=f"Exportar Tabela '{titulo}'",
        data=csv,
        file_name=f'associacao_{var_principal}_x_{var_secundaria}.csv',
        mime='text/csv'
    )
    st.markdown("---")

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
            fig_genero = px.pie(
                values=genero_counts.values,
                names=genero_counts.index,
                hole=0.3,
                color=genero_counts.index,
                color_discrete_map=COLOR_MAP
            )
            st.plotly_chart(fig_genero, use_container_width=True)

        with col_b:
            st.subheader("Percentual por Obesidade")
            obesidade_counts = df_filtrado['obesidade_class'].value_counts()
            fig_obesidade = px.pie(
                values=obesidade_counts.values,
                names=obesidade_counts.index,
                hole=0.3
            )
            st.plotly_chart(fig_obesidade, use_container_width=True)

        with col_c:
            st.subheader("Percentual de Sedentarismo")
            sedentarismo_counts = df_filtrado['sedentarismo_nivel'].value_counts()
            fig_sedentarismo = px.pie(
                values=sedentarismo_counts.values,
                names=sedentarismo_counts.index,
                hole=0.3
            )
            st.plotly_chart(fig_sedentarismo, use_container_width=True)

    st.markdown("### Fontes de Dados")
    st.markdown("- Base de dados NHANES [https://www.cdc.gov/nchs/nhanes/index.htm](https://www.cdc.gov/nchs/nhanes/index.htm)")

with tab2:
    st.header("2. Análise de Obesidade")

    with st.expander("Distribuição de IMC por Gênero", expanded=True):
        fig_imc_genero = px.histogram(
            df_filtrado,
            x='obesidade_class',
            color='genero',
            barmode='group',
            category_orders={'obesidade_class': LABELS_IMC},
            color_discrete_map=COLOR_MAP
        )
        st.plotly_chart(fig_imc_genero, use_container_width=True)

    with st.expander("Tabelas e Gráficos de Associação com Obesidade"):
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

    with st.expander("Resumo do Tempo Sentado por Status de Obesidade", expanded=True):
        df_temp_obesidade = df_filtrado.copy()
        
        grupo_sobrepeso_obeso = ['Sobrepeso', 'Obesidade Grau I', 'Obesidade Grau II', 'Obesidade Grau III']
        grupo_normal_abaixo = ['Abaixo do Peso', 'Peso Normal']
        
        def agrupar_status_obesidade(classe):
            if classe in grupo_sobrepeso_obeso:
                return 'Sobrepeso ou Obesidade'
            elif classe in grupo_normal_abaixo:
                return 'Peso Normal ou Abaixo'
            return 'Outro'
            
        df_temp_obesidade['status_obesidade_agrupado'] = df_temp_obesidade['obesidade_class'].apply(agrupar_status_obesidade)
        
        df_para_analise = df_temp_obesidade[df_temp_obesidade['status_obesidade_agrupado'].isin(['Sobrepeso ou Obesidade', 'Peso Normal ou Abaixo'])]
        
        tabela_resumo = df_para_analise.groupby('status_obesidade_agrupado')['tempo_sentado_min'].describe()
        
        tabela_resumo = tabela_resumo[['count', 'mean', '50%', 'std']].rename(columns={
            'count': 'Nº de Participantes',
            'mean': 'Média (minutos)',
            '50%': 'Mediana (minutos)',
            'std': 'Desvio Padrão (minutos)'
        })
        
        tabela_resumo['Média (horas)'] = tabela_resumo['Média (minutos)'] / 60
        
        st.subheader("Análise do Tempo Sentado Diário por Grupo de Peso")
        st.dataframe(tabela_resumo.style.format({
            'Nº de Participantes': '{:,.0f}',
            'Média (minutos)': '{:.1f}',
            'Mediana (minutos)': '{:.1f}',
            'Desvio Padrão (minutos)': '{:.1f}',
            'Média (horas)': '{:.2f}'
        }))

    # <<< NOVO GRÁFICO ADICIONADO AQUI >>>
    with st.expander("Gráfico Combinado: Obesidade x Colesterol & Pressão", expanded=True):
        # Seleciona apenas as colunas necessárias
        df_comb = df_filtrado[['obesidade_class', 'historico_pressao_alta_cat', 'historico_colesterol_alto_cat']].copy()

        # Conta os percentuais por obesidade
        tabela_pressao = pd.crosstab(df_comb['obesidade_class'], df_comb['historico_pressao_alta_cat'], normalize='index') * 100
        tabela_colesterol = pd.crosstab(df_comb['obesidade_class'], df_comb['historico_colesterol_alto_cat'], normalize='index') * 100

        # Transforma em formato longo
        df_pressao = tabela_pressao.reset_index().melt(id_vars='obesidade_class', var_name='Resposta', value_name='Percentual')
        df_pressao['Indicador'] = 'Pressão Alta'

        df_colesterol = tabela_colesterol.reset_index().melt(id_vars='obesidade_class', var_name='Resposta', value_name='Percentual')
        df_colesterol['Indicador'] = 'Colesterol Alto'

        # Junta as duas bases
        df_final = pd.concat([df_pressao, df_colesterol])

        # Cria o gráfico
        fig = px.bar(
            df_final,
            x='obesidade_class',
            y='Percentual',
            color='Resposta',
            barmode='group',
            facet_col='Indicador',  # Cria um painel para cada indicador
            category_orders={'obesidade_class': LABELS_IMC},
            title="Obesidade x Colesterol Alto & Pressão Alta"
        )

        fig.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
        fig.update_layout(yaxis_title="Percentual (%)", xaxis_title="Classificação de Obesidade")

        st.plotly_chart(fig, use_container_width=True)

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

    with st.expander("Gráfico Combinado: Riscos por Nível de Sedentarismo", expanded=True):
        # Define as categorias de obesidade (Grau I, II ou III)
        categorias_obesidade = ['Obesidade Grau I', 'Obesidade Grau II', 'Obesidade Grau III']

        # Agrupa por nível de sedentarismo e calcula as métricas de interesse
        # O argumento 'observed=True' é importante para grupos categóricos
        df_risco_sedentarismo = df_filtrado.groupby('sedentarismo_nivel', observed=True).agg(
            percentual_obesidade=('obesidade_class', lambda x: x.isin(categorias_obesidade).mean() * 100),
            percentual_pressao_alta=('historico_pressao_alta_cat', lambda x: (x == 'Sim').mean() * 100)
        ).reset_index()

        # Reorganiza o dataframe para o formato "longo", ideal para o Plotly
        df_risco_melted = df_risco_sedentarismo.melt(
            id_vars='sedentarismo_nivel',
            value_vars=['percentual_obesidade', 'percentual_pressao_alta'],
            var_name='Condição de Risco',
            value_name='Percentual'
        )

        # Mapeia os nomes das variáveis para rótulos mais amigáveis para a legenda do gráfico
        df_risco_melted['Condição de Risco'] = df_risco_melted['Condição de Risco'].map({
            'percentual_obesidade': 'Obesidade (Grau I-III)',
            'percentual_pressao_alta': 'Pressão Alta (Histórico)'
        })

        # Cria o gráfico de barras agrupado
        fig_risco_combinado = px.bar(
            df_risco_melted,
            x='sedentarismo_nivel',
            y='Percentual',
            color='Condição de Risco',
            barmode='group',
            category_orders={'sedentarismo_nivel': LABELS_SED},
            title="Prevalência de Obesidade e Hipertensão por Nível de Sedentarismo"
        )
        fig_risco_combinado.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
        fig_risco_combinado.update_layout(yaxis_title="Percentual de Participantes (%)", xaxis_title="Nível de Sedentarismo")
        st.plotly_chart(fig_risco_combinado, use_container_width=True)


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
                'idade_anos', 'genero', 'imc', 'obesidade_class',
                'tempo_sentado_min', 'sedentarismo_nivel',
                'historico_pressao_alta_cat', 'historico_colesterol_alto_cat',
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
            st.warning("Nenhum participante com este perfil de alto risco foi encontrado na seleção de filtros atual. Tente ampliar os filtros na barra lateral.")
