import pandas as pd
import plotly.express as px
import streamlit as st

df_demo = pd.read_csv("DEMO.csv", on_bad_lines='skip', sep=';')
df_bmx = pd.read_csv("BMX.csv", on_bad_lines='skip', sep=';')
df_bpq = pd.read_csv("BPQ.csv", on_bad_lines='skip', sep=';')
df_paq = pd.read_csv("PAQ.csv", on_bad_lines='skip', sep=';')
df_whq = pd.read_csv("WHQ.csv", on_bad_lines='skip', sep=';')
df_whqmec = pd.read_csv("WHQMEC.csv", on_bad_lines='skip', sep=';')
df_tchol = pd.read_csv("TCHOL.csv", on_bad_lines='skip', sep=';')
df_trigly = pd.read_csv("TRIGLY.csv", on_bad_lines='skip', sep=';')
df_tst = pd.read_csv("TST.csv", on_bad_lines='skip', sep=';')
df_hscrp = pd.read_csv("HSCRP.csv", on_bad_lines='skip', sep=';')
df_hdl = pd.read_csv("HDL.csv", on_bad_lines='skip', sep=';')
df_ghb = pd.read_csv("GHB.csv", on_bad_lines='skip', sep=';')

df_demo = df_demo.rename(
    columns={'SEQN': 'id_participante', 'RIDAGEYR': 'idade_anos', 'RIAGENDR': 'genero'})
df_bmx = df_bmx.rename(columns={
    'SEQN': 'id_participante', 'BMXWT': 'peso_kg', 'BMXHT': 'altura_cm', 'BMXBMI': 'imc',
    'BMXWAIST': 'circunferencia_cintura_cm'
})
df_paq = df_paq.rename(columns={
    'SEQN': 'id_participante', 'PAD680': 'tempo_sentado_min', 'PAQ610': 'freq_atividade_vigorosa',
    'PAQ625': 'freq_atividade_moderada'
})
df_bpq = df_bpq.rename(columns={
    'SEQN': 'id_participante', 'BPQ020': 'historico_pressao_alta', 'BPQ080': 'historico_colesterol_alto',
    'BPQ090D': 'historico_doenca_cardiaca'
})
df_tchol = df_tchol.rename(
    columns={'SEQN': 'id_participante', 'LBXTC': 'colesterol_total', 'LBDTCSI': 'colesterol_total_status'})
df_trigly = df_trigly.rename(columns={
    'SEQN': 'id_participante', 'LBDLDL': 'ldl', 'LBDLDLM': 'ldl_meio', 'LBDLDMSI': 'ldl_status',
    'LBDLDLN': 'ldl_num', 'LBDLDNSI': 'ldl_num_status'
})
df_hdl = df_hdl.rename(columns={'SEQN': 'id_participante', 'LBDHDD': 'hdl', 'LBDHDDSI': 'hdl_status'})
df_ghb = df_ghb.rename(columns={'SEQN': 'id_participante', 'LBXGH': 'ghb'})
df_hscrp = df_hscrp.rename(columns={'SEQN': 'id_participante', 'LBXHSCRP': 'hscrp', 'LBDHRPLC': 'hscrp_status'})
df_tst = df_tst.rename(columns={'SEQN': 'id_participante', 'WTTSTPP': 'peso_pp'})

df_merged = df_demo.merge(df_bmx, on='id_participante', how='inner') \
    .merge(df_paq, on='id_participante', how='inner') \
    .merge(df_bpq, on='id_participante', how='inner') \
    .merge(df_tchol, on='id_participante', how='left') \
    .merge(df_trigly, on='id_participante', how='left') \
    .merge(df_hdl, on='id_participante', how='left') \
    .merge(df_ghb, on='id_participante', how='left') \
    .merge(df_hscrp, on='id_participante', how='left') \
    .merge(df_tst, on='id_participante', how='left')

colunas_essenciais = [
    'imc', 'peso_kg', 'altura_cm', 'circunferencia_cintura_cm', 'colesterol_total',
    'ldl', 'hdl', 'ghb', 'hscrp'
]
df_merged = df_merged.dropna(subset=[col for col in colunas_essenciais if col in df_merged.columns])

df_merged = df_merged.drop(columns=[col for col in ['BMIWT', 'BMIHT'] if col in df_merged.columns])

df_merged['genero'] = df_merged['genero'].replace({1: 'Homem', 2: 'Mulher'})
df_merged['historico_doenca_cardiaca'] = df_merged['historico_doenca_cardiaca'].fillna(9)
df_merged['freq_atividade_vigorosa'] = df_merged['freq_atividade_vigorosa'].fillna(0)
df_merged['freq_atividade_moderada'] = df_merged['freq_atividade_moderada'].fillna(0)
df_merged['idade_anos'] = pd.to_numeric(df_merged['idade_anos'], errors='coerce')
df_merged['tempo_sentado_min'] = pd.to_numeric(df_merged['tempo_sentado_min'], errors='coerce')
df_merged['tempo_sentado_min'] = df_merged['tempo_sentado_min'].fillna(df_merged['tempo_sentado_min'].median())

sedentary_bins = [0, 300, 480, float('inf')]
sedentary_labels = ['Baixo', 'Moderado', 'Alto']
df_merged['sedentarismo_nivel'] = pd.cut(
    df_merged['tempo_sentado_min'], bins=sedentary_bins, labels=sedentary_labels, right=False
)

bins_imc = [0, 18.5, 24.9, 29.9, 34.9, 39.9, float('inf')]
labels_imc = ['Abaixo do Peso', 'Peso Normal', 'Sobrepeso', 'Obesidade Grau I', 'Obesidade Grau II', 'Obesidade Grau III']
df_merged['obesidade_class'] = pd.cut(df_merged['imc'], bins=bins_imc, labels=labels_imc, right=False)

df_merged['historico_pressao_alta_cat'] = df_merged['historico_pressao_alta'].replace(
    {1.0: 'Sim', 2.0: 'Não', 9.0: 'Não Sabe'}
)
df_merged['historico_colesterol_alto_cat'] = df_merged['historico_colesterol_alto'].replace(
    {1.0: 'Sim', 2.0: 'Não', 7.0: 'Não Sabe', 9.0: 'Não Sabe'}
).fillna('Não Sabe')
df_merged['historico_doenca_cardiaca_cat'] = df_merged['historico_doenca_cardiaca'].replace(
    {1.0: 'Sim', 2.0: 'Não', 7.0: 'Não Sabe', 9.0: 'Não Sabe'}
).fillna('Não Sabe')

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
        return 'Próximo do ideal / Acima do ideal'
    elif valor < 160:
        return 'Limítrofe'
    elif valor < 190:
        return 'Alto'
    else:
        return 'Muito alto'
df_merged['ldl_class'] = df_merged['ldl'].apply(classificar_ldl)

def classificar_hdl(row):
    valor = row['hdl']
    genero = row['genero']
    if pd.isna(valor):
        return 'Não disponível'
    if genero == 'Homem':
        if valor < 40:
            return 'Baixo'
        elif valor < 60:
            return 'Normal'
        else:
            return 'Alto'
    else:
        if valor < 50:
            return 'Baixo'
        elif valor < 60:
            return 'Normal'
        else:
            return 'Alto'
df_merged['hdl_class'] = df_merged.apply(classificar_hdl, axis=1)

tabela_obesidade = {
    "Pressão Alta": pd.crosstab(df_merged['obesidade_class'], df_merged['historico_pressao_alta_cat'], normalize='index') * 100,
    "Colesterol Alto": pd.crosstab(df_merged['obesidade_class'], df_merged['historico_colesterol_alto_cat'], normalize='index') * 100,
    "Doença Cardíaca": pd.crosstab(df_merged['obesidade_class'], df_merged['historico_doenca_cardiaca_cat'], normalize='index') * 100,
    "HDL": pd.crosstab(df_merged['obesidade_class'], df_merged['hdl_class'], normalize='index') * 100,
    "LDL": pd.crosstab(df_merged['obesidade_class'], df_merged['ldl_class'], normalize='index') * 100,
    "Colesterol Total": pd.crosstab(df_merged['obesidade_class'], df_merged['colesterol_total_class'], normalize='index') * 100
}

tabela_sedentarismo = {
    "Pressão Alta": pd.crosstab(df_merged['sedentarismo_nivel'], df_merged['historico_pressao_alta_cat'], normalize='index') * 100,
    "Colesterol Alto": pd.crosstab(df_merged['sedentarismo_nivel'], df_merged['historico_colesterol_alto_cat'], normalize='index') * 100,
    "Obesidade": pd.crosstab(df_merged['sedentarismo_nivel'], df_merged['obesidade_class'], normalize='index') * 100,
    "HDL": pd.crosstab(df_merged['sedentarismo_nivel'], df_merged['hdl_class'], normalize='index') * 100,
    "LDL": pd.crosstab(df_merged['sedentarismo_nivel'], df_merged['ldl_class'], normalize='index') * 100,
    "Colesterol Total": pd.crosstab(df_merged['sedentarismo_nivel'], df_merged['colesterol_total_class'], normalize='index') * 100
}

tabela_genero = {
    "Obesidade": pd.crosstab(df_merged['genero'], df_merged['obesidade_class'], normalize='index') * 100,
    "HDL": pd.crosstab(df_merged['genero'], df_merged['hdl_class'], normalize='index') * 100,
    "LDL": pd.crosstab(df_merged['genero'], df_merged['ldl_class'], normalize='index') * 100,
    "Colesterol Total": pd.crosstab(df_merged['genero'], df_merged['colesterol_total_class'], normalize='index') * 100
}

tabela_hdl_ldl = pd.crosstab(df_merged['hdl_class'], df_merged['ldl_class'], normalize='index') * 100

st.set_page_config(layout="wide")
st.title("Dashboard de Análise de Fatores de Risco Cardiovascular")

st.header("Análises Descritivas Gerais")

col1, col2 = st.columns(2)

with col1:
    fig_idade = px.histogram(df_merged, x="idade_anos", nbins=50, title="Distribuição de Idade dos Participantes")
    st.plotly_chart(fig_idade, use_container_width=True)
    
    fig_imc = px.histogram(df_merged, x="imc", nbins=50, title="Distribuição de IMC (Índice de Massa Corporal)")
    st.plotly_chart(fig_imc, use_container_width=True)

with col2:
    df_genero = df_merged['genero'].value_counts().reset_index()
    df_genero.columns = ['genero', 'contagem']
    fig_genero = px.pie(df_genero, names='genero', values='contagem', title="Distribuição por Gênero")
    st.plotly_chart(fig_genero, use_container_width=True)

    df_obesidade = df_merged['obesidade_class'].value_counts().reset_index()
    df_obesidade.columns = ['obesidade_class', 'contagem']
    fig_obesidade_dist = px.bar(df_obesidade, x='obesidade_class', y='contagem', title="Distribuição da Classificação de Obesidade")
    fig_obesidade_dist.update_xaxes(categoryorder='array', categoryarray=labels_imc)
    st.plotly_chart(fig_obesidade_dist, use_container_width=True)

st.header("Relação entre Obesidade e Fatores de Risco")
for chave, tabela in tabela_obesidade.items():
    fig = px.bar(
        tabela, 
        barmode='group',
        title=f"Obesidade vs {chave} (%)",
        labels={'value': 'Percentual (%)', 'obesidade_class': 'Classificação de Obesidade'}
    )
    st.plotly_chart(fig, use_container_width=True)

st.header("Relação entre Sedentarismo e Fatores de Risco")
for chave, tabela in tabela_sedentarismo.items():
    fig = px.bar(
        tabela, 
        barmode='group',
        title=f"Sedentarismo vs {chave} (%)",
        labels={'value': 'Percentual (%)', 'sedentarismo_nivel': 'Nível de Sedentarismo'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
st.header("Análise de Marcadores de Colesterol")
col3, col4 = st.columns(2)

with col3:
    st.subheader("Relação entre Níveis de HDL e LDL (%)")
    fig_hdl_ldl = px.imshow(
        tabela_hdl_ldl, 
        text_auto=True, 
        aspect="auto", 
        color_continuous_scale='RdYlGn_r',
        labels=dict(x="Classificação LDL", y="Classificação HDL", color="Percentual (%)")
    )
    st.plotly_chart(fig_hdl_ldl, use_container_width=True)

with col4:
    st.subheader("Análises por Gênero (%)")
    for chave, tabela in tabela_genero.items():
        st.write(f"**Gênero vs {chave}**")
        st.dataframe(tabela.round(2))

if st.checkbox("Mostrar DataFrame Final Processado"):
    st.header("Dados Completos")
    st.dataframe(df_merged)