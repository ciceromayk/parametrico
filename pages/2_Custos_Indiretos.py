import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

def card_metric_pro(label, value, delta=None, icon_name="cash-coin"):
    st.markdown(f"""
    <div style="
        border: 1px solid #e1e1e1;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background: linear-gradient(145deg, #f0f0f0, #ffffff);
        box-shadow: 5px 5px 10px #d1d1d1, -5px -5px 10px #ffffff;
    ">
        <div style="display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
            <i class="bi bi-{icon_name}" style="font-size: 1.5em; margin-right: 10px; color: #007bff;"></i>
            <h3 style="margin: 0; color: #333; font-size: 1.2em;">{label}</h3>
        </div>
        <p style="font-size: 2.5em; font-weight: bold; margin: 0; color: #007bff;">{value}</p>
        {f'<p style="color: {"green" if delta and delta > 0 else "red"}; font-size: 1em;">{f"+{delta}%" if delta else ""}</p>' if delta is not None else ''}
    </div>
    """, unsafe_allow_html=True)

def configure_grid(df):
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Formatador de moeda
    jscode_formatador_moeda = JsCode("""
        function(params) {
            if (params.value === null || params.value === undefined) { return ''; }
            return 'R$ ' + params.value.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }
    """)
    
    # Formatador condicional de cores
    jscode_color_percentual = JsCode("""
        function(params) {
            if (params.value < 3) return {'color': 'green'};
            if (params.value >= 3 && params.value < 6) return {'color': 'orange'};
            return {'color': 'red'};
        }
    """)
    
    gb.configure_column("Item", headerName="Item", flex=5, resizable=True)
    gb.configure_column("%", 
        headerName="%", 
        editable=True, 
        cellStyle=jscode_color_percentual,
        type=["numericColumn", "numberColumnFilter"],
        precision=2
    )
    gb.configure_column("Custo (R$)", 
        headerName="Custo (R$)", 
        valueFormatter=jscode_formatador_moeda, 
        flex=1, 
        resizable=False
    )
    
    return gb.build()

# Resto do código permanece similar...


    # SUGESTÃO DE DESIGN: Centralizar a tabela
    
    _ , col_tabela, _ = st.columns([3, 2, 3])
    with col_tabela:
        grid_response = AgGrid(
            df,
            gridOptions=gridOptions,
            height=450,
            width=1000,
            update_mode='MODEL_CHANGED',
            allow_unsafe_jscode=True,
            try_convert_numeric_dtypes=True,
            theme='streamlit'
        )
    
    # PASSO 3: Usar os Dados Editados
    edited_df = grid_response['data']
    
    edited_df["Custo (R$)"] = vgv_total * (pd.to_numeric(edited_df["%"], errors='coerce').fillna(0) / 100)
    custo_indireto_calculado = edited_df["Custo (R$)"].sum()

    for index, row in edited_df.iterrows():
        item_nome = row["Item"]
        novo_percentual = row["%"]
        st.session_state.custos_indiretos_percentuais[item_nome]['percentual'] = novo_percentual

    # --- ALTERAÇÃO NO LAYOUT DO CARD FINAL ---

    # Adicionamos um espaçamento vertical para separar a tabela do card
    st.write("<br>", unsafe_allow_html=True)
    
    # Usamos colunas para centralizar o card, alinhando-o com a tabela
    # A proporção [2, 1, 2] significa: 2 partes vazias, 1 parte para o card, 2 partes vazias
    _, col_metrica, _ = st.columns([3, 6, 3])
    
    with col_metrica:
        card_metric(
            label="Custo Indireto Total",
            value=f"R$ {fmt_br(custo_indireto_calculado)}",
            icon_name="cash-coin"
        )
