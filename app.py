import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import io
import os
from datetime import datetime

# ==============================================================================
# 1. CONFIGURAÇÕES DE ALTA PERFORMANCE E UI
# ==============================================================================
st.set_page_config(page_title="PyTríade Master Engine", page_icon="🏢", layout="wide")

# Estilo Customizado para Ar de Software Profissional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Caminho do Banco (Raiz do GitHub)
db_path = 'PyTriade_Master.db'

def get_db_connection():
    """Conexão segura para ambiente Cloud"""
    return sqlite3.connect(db_path, check_same_thread=False, timeout=30)

def gerar_excel_download(df, cod, qtd, bdi):
    """Gerador de Relatório Executivo Formatado"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Orcamento_Executivo', index=False, startrow=4)
        workbook = writer.book
        worksheet = writer.sheets['Orcamento_Executivo']
        
        # Formatos
        fmt_header = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#1E3A8A'})
        fmt_money = workbook.add_format({'num_format': 'R$ #,##0.00'})
        
        # Cabeçalho do Relatório
        worksheet.write('A1', 'PYTRÍADE MASTER ENGINE - RELATÓRIO DE ORÇAMENTO', fmt_header)
        worksheet.write('A2', f'Serviço: {cod} | Quantidade: {qtd} | BDI Aplicado: {bdi}%')
        worksheet.write('A3', f'Data de Emissão: {datetime.now().strftime("%d/%m/%Y %H:%M")}')
        
        worksheet.set_column('B:B', 50)  # Descrição larga
        worksheet.set_column('E:F', 18, fmt_money) # Preços formatados
    return output.getvalue()

# ==============================================================================
# 2. BARRA LATERAL (STATUS E SINCRONIZAÇÃO)
# ==============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4342/4342728.png", width=100)
    st.title("Painel de Controlo")
    
    if os.path.exists(db_path):
        mtime = datetime.fromtimestamp(os.path.getmtime(db_path))
        st.success("✅ Base de Dados Conectada")
        st.info(f"📅 Última Sincronização:\n{mtime.strftime('%d/%m/%Y %H:%M:%S')}")
    else:
        st.error("❌ Base de Dados não encontrada")
    
    st.divider()
    st.caption("PyTríade Engine v1.0\nEngenheiro Vladimir Fersengkratus")

# ==============================================================================
# 3. INTERFACE PRINCIPAL
# ==============================================================================
st.title("🏢 PyTríade Master Engine")
st.markdown("### Sistema Inteligente de Orçamentação e Planeamento")
st.divider()

if not os.path.exists(db_path):
    st.warning("Aguardando o primeiro 'Push' de dados do Google Colab...")
    st.stop()

# Abas Estratégicas
tab_orc, tab_abc, tab_ldb = st.tabs(["📊 ORÇAMENTO EXECUTIVO", "📈 ESTRATÉGIA ABC", "⏱️ PLANEAMENTO LDB"])

# --- ABA 1: ORÇAMENTO ---
with tab_orc:
    col_input1, col_input2, col_input3 = st.columns([2, 1, 1])
    with col_input1:
        servico_id = st.text_input("Código do Serviço (EAP)", value="1.1.1.1", help="Insira o código da CPU conforme a sua planilha.")
    with col_input2:
        qtd_total = st.number_input("Quantidade da Tarefa", value=100.0, step=10.0)
    with col_input3:
        bdi_val = st.number_input("BDI (%)", value=25.0, step=0.5)

    if st.button("🚀 PROCESSAR ENGENHARIA DE CUSTOS", use_container_width=True):
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
            # Cálculos de Motor de Engenharia
            df_res['CUSTO_UNIT_TOTAL'] = df_res['CONSUMO'] * df_res['PRECO_UNIT'].fillna(0)
            total_direto = df_res['CUSTO_UNIT_TOTAL'].sum() * qtd_total
            total_venda = total_direto * (1 + (bdi_val/100))
            preco_unit_venda = total_venda / qtd_total

            # Exibição de Métricas de Alto Nível
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Custo Direto (Total)", f"R$ {total_direto:,.2f}")
            m2.metric("Preço de Venda (Total)", f"R$ {total_venda:,.2f}")
            m3.metric("Preço Unit. Venda", f"R$ {preco_unit_venda:,.2f}")
            m4.metric("Lucro Bruto Est.", f"R$ {(total_venda - total_direto):,.2f}")

            st.subheader("Composição de Preços Unitários (CPU)")
            st.dataframe(df_res.style.format({'CONSUMO': '{:.4f}', 'PRECO_UNIT': 'R$ {:.2f}', 'CUSTO_UNIT_TOTAL': 'R$ {:.2f}'}), use_container_width=True)

            # Botão de Exportação Profissional
            excel_data = gerar_excel_download(df_res, servico_id, qtd_total, bdi_val)
            st.download_button(
                label="📥 DESCARREGAR PROPOSTA COMERCIAL (EXCEL)",
                data=excel_data,
                file_name=f"Orcamento_PyTriade_{servico_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.error(f"O serviço '{servico_id}' não foi encontrado na base sincronizada.")

# --- ABA 2: CURVA ABC ---
with tab_abc:
    st.subheader("📊 Análise de Pareto dos Insumos (Curva ABC)")
    conn = get_db_connection()
    df_abc = pd.read_sql_query("SELECT tipo, descricao, preco_unitario FROM master_insumos WHERE preco_unitario > 0", conn)
    conn.close()

    if not df_abc.empty:
        df_abc = df_abc.sort_values(by='preco_unitario', ascending=False).head(20)
        fig = px.bar(df_abc, x='preco_unitario', y='descricao', orientation='h',
                     color='tipo', title="Top 20 Insumos de Maior Impacto Financeiro",
                     labels={'preco_unitario': 'Preço Unitário (R$)', 'descricao': 'Insumo'},
                     color_discrete_map={'MAT': '#1E3A8A', 'MO': '#10B981', 'EQP': '#F59E0B'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sincronize os dados para visualizar a Curva ABC.")

# --- ABA 3: PLANEAMENTO LDB ---
with tab_ldb:
    st.subheader("⏱️ Dimensionamento de Equipas e Prazos")
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        prazo_meta = st.slider("Prazo Desejado (Dias Úteis)", 1, 120, 22)
        produtividade = st.number_input("H/un (Produtividade da Equipa)", value=1.5, help="Quantas horas de mão de obra para cada unidade de serviço.")
    with c_p2:
        jornada = st.number_input("Jornada Diária (Horas)", value=8.8)
        folga_est = st.slider("Margem de Segurança (%)", 0, 30, 10)
        
    # Lógica de Cálculo LDB
    horas_totais = (qtd_total * produtividade) * (1 + (folga_est/100))
    equipa_necessaria = (horas_totais / jornada) / prazo_meta
    
    st.divider()
    res1, res2, res3 = st.columns(3)
    res1.metric("Mão de Obra Total", f"{horas_totais:,.0f} Horas")
    res2.metric("Equipa Recomendada", f"{int(equipe_necessaria) + 1} Operários")
    res3.metric("Ritmo de Produção", f"{qtd_total/prazo_meta:.2f} un/dia")
