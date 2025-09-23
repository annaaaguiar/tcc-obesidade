import pandas as pd
import plotly.express as px

# Upload
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

# Renomear
df_demo = df_demo.rename(columns={'SEQN': 'id_participante', 'RIDAGEYR': 'idade_anos', 'RIAGENDR': 'genero'})
df_bmx = df_bmx.rename(columns={'SEQN': 'id_participante', 'BMXWT': 'peso_kg', 'BMXHT': 'altura_cm', 'BMXBMI': 'imc', 'BMXWAIST': 'circunferencia_cintura_cm'})
df_paq = df_paq.rename(columns={'SEQN': 'id_participante', 'PAD680': 'tempo_sentado_min', 'PAQ610': 'freq_atividade_vigorosa', 'PAQ625': 'freq_atividade_moderada'})
df_bpq = df_bpq.rename(columns={'SEQN': 'id_participante', 'BPQ020': 'historico_pressao_alta', 'BPQ080': 'historico_colesterol_alto', 'BPQ090D': 'historico_doenca_cardiaca'})
df_tchol = df_tchol.rename(columns={'SEQN': 'id_participante', 'LBXTC': 'colesterol_total', 'LBDTCSI': 'colesterol_total_status'})
df_trigly = df_trigly.rename(columns={'SEQN': 'id_participante', 'LBDLDL': 'ldl', 'LBDLDLM': 'ldl_meio', 'LBDLDMSI': 'ldl_status', 'LBDLDLN': 'ldl_num', 'LBDLDNSI': 'ldl_num_status'})
df_hdl = df_hdl.rename(columns={'SEQN': 'id_participante', 'LBDHDD': 'hdl', 'LBDHDDSI': 'hdl_status'})
df_ghb = df_ghb.rename(columns={'SEQN': 'id_participante', 'LBXGH': 'ghb'})
df_hscrp = df_hscrp.rename(columns={'SEQN': 'id_participante', 'LBXHSCRP': 'hscrp', 'LBDHRPLC': 'hscrp_status'})
df_tst = df_tst.rename(columns={'SEQN': 'id_participante', 'WTTSTPP': 'peso_pp'})

print("Colunas renomeadas")

# Unir df
df_merged = df_demo.merge(df_bmx, on='id_participante', how='inner') \
    .merge(df_paq, on='id_participante', how='inner') \
    .merge(df_bpq, on='id_participante', how='inner') \
    .merge(df_tchol, on='id_participante', how='left') \
    .merge(df_trigly, on='id_participante', how='left') \
    .merge(df_hdl, on='id_participante', how='left') \
    .merge(df_ghb, on='id_participante', how='left') \
    .merge(df_hscrp, on='id_participante', how='left') \
    .merge(df_tst, on='id_participante', how='left')

# Padronização de dados
df_merged['genero'] = df_merged['genero'].replace({1: 'Homem', 2: 'Mulher'})
df_merged['historico_doenca_cardiaca'] = df_merged['historico_doenca_cardiaca'].fillna(9)
df_merged['freq_atividade_vigorosa'] = df_merged['freq_atividade_vigorosa'].fillna(0)
df_merged['freq_atividade_moderada'] = df_merged['freq_atividade_moderada'].fillna(0)
df_merged['idade_anos'] = pd.to_numeric(df_merged['idade_anos'], errors='coerce')
df_merged['tempo_sentado_min'] = pd.to_numeric(df_merged['tempo_sentado_min'], errors='coerce')
df_merged['tempo_sentado_min'] = df_merged['tempo_sentado_min'].fillna(df_merged['tempo_sentado_min'].median())

# Limpeza
colunas_essenciais = ['imc', 'peso_kg', 'altura_cm', 'circunferencia_cintura_cm', 'colesterol_total', 'ldl', 'hdl', 'ghb', 'hscrp']
df_merged = df_merged.dropna(subset=[col for col in colunas_essenciais if col in df_merged.columns])

# Remover colunas desnecessárias se existirem
df_merged = df_merged.drop(columns=[col for col in ['BMIWT', 'BMIHT'] if col in df_merged.columns])

print("\nDataFrame após limpeza e ajustes:")
print(df_merged.info())

# Classificações

# Estatísticas de idade
idade_media = df_merged['idade_anos'].mean()
idade_std = df_merged['idade_anos'].std()
idade_min = df_merged['idade_anos'].min()
idade_max = df_merged['idade_anos'].max()

print(f"Idade média: {idade_media:.1f} anos")
print(f"Desvio padrão da idade: {idade_std:.1f}")
print(f"Idade mínima: {idade_min} anos")
print(f"Idade máxima: {idade_max} anos")

# Classificação Sedentarismo
sedentary_bins = [0, 300, 480, float('inf')]
sedentary_labels = ['Baixo', 'Moderado', 'Alto']
df_merged['sedentarismo_nivel'] = pd.cut(df_merged['tempo_sentado_min'], bins=sedentary_bins, labels=sedentary_labels, right=False)

tempo_medio_sentado = df_merged['tempo_sentado_min'].mean()
print(f"Tempo médio sentado diário: {tempo_medio_sentado:.1f} minutos")

distribuicao_sedentarismo = df_merged['sedentarismo_nivel'].value_counts(normalize=True) * 100
print("\nDistribuição de sedentarismo (%):")
print(distribuicao_sedentarismo)

# Obesidade
bins_imc = [0, 18.5, 24.9, 29.9, 34.9, 39.9, float('inf')]
labels_imc = ['Abaixo do Peso', 'Peso Normal', 'Sobrepeso', 'Obesidade Grau I', 'Obesidade Grau II', 'Obesidade Grau III']
df_merged['obesidade_class'] = pd.cut(df_merged['imc'], bins=bins_imc, labels=labels_imc, right=False)

# Sedentarismo
bins_sed = [0, 300, 480, float('inf')]
labels_sed = ['Baixo', 'Moderado', 'Alto']
df_merged['sedentarismo_nivel'] = pd.cut(df_merged['tempo_sentado_min'], bins=bins_sed, labels=labels_sed, right=False)

# Pressão alta
df_merged['historico_pressao_alta_cat'] = df_merged['historico_pressao_alta'].replace({1.0: 'Sim', 2.0: 'Não', 9.0: 'Não Sabe'})

# Colesterol alto
df_merged['historico_colesterol_alto_cat'] = df_merged['historico_colesterol_alto'].replace({1.0: 'Sim', 2.0: 'Não', 7.0: 'Não Sabe', 9.0: 'Não Sabe'}).fillna('Não Sabe')

# Doença cardíaca
df_merged['historico_doenca_cardiaca_cat'] = df_merged['historico_doenca_cardiaca'].replace({1.0: 'Sim', 2.0: 'Não', 7.0: 'Não Sabe', 9.0: 'Não Sabe'}).fillna('Não Sabe')

# Colesterol total
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

# LDL
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

# HDL
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

# TABELAS

# Obesidade
tabela_obesidade = {
    "Pressão Alta": pd.crosstab(df_merged['obesidade_class'], df_merged['historico_pressao_alta_cat'], normalize='index') * 100,
    "Colesterol Alto": pd.crosstab(df_merged['obesidade_class'], df_merged['historico_colesterol_alto_cat'], normalize='index') * 100,
    "Doença Cardíaca": pd.crosstab(df_merged['obesidade_class'], df_merged['historico_doenca_cardiaca_cat'], normalize='index') * 100,
    "HDL": pd.crosstab(df_merged['obesidade_class'], df_merged['hdl_class'], normalize='index') * 100,
    "LDL": pd.crosstab(df_merged['obesidade_class'], df_merged['ldl_class'], normalize='index') * 100,
    "Colesterol Total": pd.crosstab(df_merged['obesidade_class'], df_merged['colesterol_total_class'], normalize='index') * 100
}

# Sedentarismo
tabela_sedentarismo = {
    "Pressão Alta": pd.crosstab(df_merged['sedentarismo_nivel'], df_merged['historico_pressao_alta_cat'], normalize='index') * 100,
    "Colesterol Alto": pd.crosstab(df_merged['sedentarismo_nivel'], df_merged['historico_colesterol_alto_cat'], normalize='index') * 100,
    "Obesidade": pd.crosstab(df_merged['sedentarismo_nivel'], df_merged['obesidade_class'], normalize='index') * 100,
    "HDL": pd.crosstab(df_merged['sedentarismo_nivel'], df_merged['hdl_class'], normalize='index') * 100,
    "LDL": pd.crosstab(df_merged['sedentarismo_nivel'], df_merged['ldl_class'], normalize='index') * 100,
    "Colesterol Total": pd.crosstab(df_merged['sedentarismo_nivel'], df_merged['colesterol_total_class'], normalize='index') * 100
}

# Gênero
tabela_genero = {
    "Obesidade": pd.crosstab(df_merged['genero'], df_merged['obesidade_class'], normalize='index') * 100,
    "HDL": pd.crosstab(df_merged['genero'], df_merged['hdl_class'], normalize='index') * 100,
    "LDL": pd.crosstab(df_merged['genero'], df_merged['ldl_class'], normalize='index') * 100,
    "Colesterol Total": pd.crosstab(df_merged['genero'], df_merged['colesterol_total_class'], normalize='index') * 100
}

# HDL x LDL
tabela_hdl_ldl = pd.crosstab(df_merged['hdl_class'], df_merged['ldl_class'], normalize='index') * 100

print("\nDataFrame final organizado e pronto para análise e gráficos.")

# Exibir tabelas
print("\n--- Tabelas de Associação: Obesidade ---")
for chave, tabela in tabela_obesidade.items():
    print(f"\nObesidade x {chave} (%):")
    print(tabela.round(2))

print("\n--- Tabelas de Associação: Sedentarismo ---")
for chave, tabela in tabela_sedentarismo.items():
    print(f"\nSedentarismo x {chave} (%):")
    print(tabela.round(2))

print("\n--- Tabelas de Associação: Gênero ---")
for chave, tabela in tabela_genero.items():
    print(f"\nGênero x {chave} (%):")
    print(tabela.round(2))

print("\n--- HDL x LDL (%) ---")
print(tabela_hdl_ldl.round(2))
