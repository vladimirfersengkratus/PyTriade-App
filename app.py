import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import io
import os
from datetime import datetime

# 1. Configurações de Página
st.set_page_config(page_title="PyTríade Master", page_icon="🏢", layout="wide")

# CAMINHO NA NUVEM: Procura o banco na pasta 'database' dentro do projeto
db_path = os.path.join(os.getcwd(), 'database', 'PyTriade_Master.db')

def get_db_connection():
    return sqlite3.connect(db_path, timeout=20)

def gerar_excel_download(df, cod, qtd, bdi):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Orcamento', index=False, startrow=4)
        workbook = writer.book
        worksheet = writer.sheets['Orcamento']
        fmt_money = workbook.add_format({'num_format': 'R$ #,##0.00'})
        worksheet.write('A1', 'RELATÓRIO EXECUTIVO - PYTRÍADE ENGINE', workbook.add_format({'bold': True}))
        worksheet.set_column('B:B', 40)
        worksheet.set_column('E:F', 15, fmt_money)
    return output.getvalue()

st.title("🏢 PyTríade Master Engine")
st.caption(f"Versão Cloud | {datetime.now().strftime('%d/%m/%Y')}")
st.divider()

tab_orc, tab_abc, tab_ldb = st.tabs(["📊 ORÇAMENTO EXECUTIVO", "📈 ESTRATÉGIA ABC", "⏱️ PLANEJAMENTO LDB"])

with tab_orc:
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1: servico_id = st.text_input("Código do Serviço (EAP)", value="1.1.1.1")
    with c2: qtd_input = st.number_input("Quantidade Total", value=100.0)
    with c3: bdi_input = st.number_input("BDI (%)", value=25.0)

    if st.button("🚀 PROCESSAR ORÇAMENTO", use_container_width=True):
        try:
            conn = get_db_connection()
            query = """
                SELECT insumo.tipo as TIPO, insumo.descricao as DESCRICAO, insumo.unidade as UND,
                       cpu.coeficiente as CONSUMO, insumo.preco_unitario as PRECO_UNIT
                FROM master_cpu AS cpu
                LEFT JOIN master_insumos AS insumo ON cpu.cod_insumo = insumo.codigo
                WHERE cpu.cod_servico = ?
            """
            df_res = pd.read_sql_query(query, conn, params=(servico_id,))
            conn.close()

            if not df_res.empty:
                df_res['CUSTO_TOTAL'] = df_res['CONSUMO'] * df_res['PRECO_UNIT']
                total_direto = df_res['CUSTO_TOTAL'].sum() * qtd_input
                total_venda = total_direto * (1 + (bdi_input/100))

                m1, m2, m3 = st.columns(3)
                m1.metric("Custo Direto", f"R$ {total_direto:,.2f}")
                m2.metric("Preço de Venda", f"R$ {total_venda:,.2f}")
                m3.metric("BDI", f"{bdi_input}%")

                st.dataframe(df_res, use_container_width=True)

                excel_data = gerar_excel_download(df_res, servico_id, qtd_input, bdi_input)
                st.download_button(
                    label="📥 DESCARREGAR EXCEL FORMATADO",
                    data=excel_data,
                    file_name=f"Orcamento_{servico_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Erro no banco: {e}")

with tab_abc:
    st.subheader("Pareto de Insumos")
    try:
        conn = get_db_connection()
        df_abc = pd.read_sql_query("SELECT descricao, preco_unitario FROM master_insumos WHERE preco_unitario > 0", conn)
        conn.close()
        df_abc = df_abc.sort_values(by='preco_unitario', ascending=False).head(20)
        st.plotly_chart(px.bar(df_abc, x='descricao', y='preco_unitario'), use_container_width=True)
    except: st.info("Base de dados a carregar...")

with tab_ldb:
    st.subheader("Planeamento")
    p = st.slider("Prazo (Dias)", 1, 60, 15)
    prod = st.number_input("Produtividade (H/un)", value=1.5)
    equipe = ((qtd_input * prod) / 8.8) / p
    st.metric("Equipa Sugerida", f"{int(equipe) + 1} Operários")
