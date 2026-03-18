import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import io
import os
from datetime import datetime

# ==============================================================================
# 1. CONFIGURAÇÕES DE CAMINHO (VERSÃO CLOUD)
# ==============================================================================
st.set_page_config(page_title="PyTríade Master", page_icon="🏢", layout="wide")

# MUDANÇA AQUI: O banco agora fica na raiz do GitHub, sem pastas.
db_path = 'PyTriade_Master.db'

def get_db_connection():
    return sqlite3.connect(db_path, timeout=30)

def gerar_excel_download(df, cod, qtd, bdi):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Orcamento', index=False, startrow=4)
        workbook = writer.book
        worksheet = writer.sheets['Orcamento']
        fmt_money = workbook.add_format({'num_format': 'R$ #,##0.00'})
        worksheet.write('A1', 'RELATÓRIO EXECUTIVO - PYTRÍADE ENGINE', workbook.add_format({'bold': True}))
        worksheet.set_column('B:B', 45)
        worksheet.set_column('E:F', 18, fmt_money)
    return output.getvalue()

# ==============================================================================
# 2. INTERFACE DO USUÁRIO
# ==============================================================================
st.title("🏢 PyTríade Master Engine")
st.caption(f"Versão Cloud | {datetime.now().strftime('%d/%m/%Y')}")
st.divider()

# Verificação: O arquivo subiu mesmo?
if not os.path.exists(db_path):
    st.error(f"❌ Banco de dados '{db_path}' não encontrado no repositório!")
    st.stop()

tab_orc, tab_abc, tab_ldb = st.tabs(["📊 ORÇAMENTO", "📈 ESTRATÉGIA ABC", "⏱️ PLANEJAMENTO"])

with tab_orc:
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: serv_id = st.text_input("Código do Serviço", value="1.1.1.1")
    with c2: qtd = st.number_input("Quantidade", value=100.0)
    with c3: bdi = st.number_input("BDI (%)", value=25.0)

    if st.button("🚀 CALCULAR AGORA", use_container_width=True):
        conn = get_db_connection()
        query = "SELECT insumo.tipo, insumo.descricao, insumo.unidade, cpu.coeficiente, insumo.preco_unitario FROM master_cpu AS cpu LEFT JOIN master_insumos AS insumo ON cpu.cod_insumo = insumo.codigo WHERE cpu.cod_servico = ?"
        df = pd.read_sql_query(query, conn, params=(serv_id,))
        conn.close()

        if not df.empty:
            df['custo_parcial'] = df['coeficiente'] * df['preco_unitario'].fillna(0)
            direto = df['custo_parcial'].sum() * qtd
            venda = direto * (1 + (bdi/100))

            m1, m2 = st.columns(2)
            m1.metric("Custo Direto", f"R$ {direto:,.2f}")
            m2.metric("Preço de Venda", f"R$ {venda:,.2f}")

            st.dataframe(df, use_container_width=True)
            
            # Botão de Exportação
            excel = gerar_excel_download(df, serv_id, qtd, bdi)
            st.download_button("📥 BAIXAR EXCEL", excel, f"Orc_{serv_id}.xlsx", use_container_width=True)
        else:
            st.warning("Serviço não encontrado.")

with tab_abc:
    st.subheader("Pareto de Insumos")
    conn = get_db_connection()
    df_abc = pd.read_sql_query("SELECT descricao, preco_unitario FROM master_insumos WHERE preco_unitario > 0", conn)
    conn.close()
    df_abc = df_abc.sort_values(by='preco_unitario', ascending=False).head(15)
    st.plotly_chart(px.bar(df_abc, x='preco_unitario', y='descricao', orientation='h'), use_container_width=True)

with tab_ldb:
    st.subheader("Planejamento")
    prazo = st.slider("Prazo (Dias)", 1, 60, 20)
    prod = st.number_input("H/un", value=1.5)
    equipe = ((qtd * prod) / 8.8) / prazo
    st.metric("Equipe Necessária", f"{int(equipe) + 1} Operários")
