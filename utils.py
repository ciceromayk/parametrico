# utils.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from weasyprint import HTML

# --- CONSTANTES GLOBAIS e outras funções ---

def fmt_br(valor):
    """
    Formata um valor numérico para a moeda brasileira (R$) de forma independente do locale.
    """
    if pd.isna(valor) or valor is None:
        return "0,00"
    s = f"{valor:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")

JSON_PATH = "projects.json"
HISTORICO_DIRETO_PATH = "historico_direto.json"
HISTORICO_INDIRETO_PATH = "historico_indireto.json"

TIPOS_PAVIMENTO = {
    "Área Privativa (Autônoma)": (1.00, 1.00), "Áreas de lazer ambientadas": (2.00, 4.00), "Varandas": (0.75, 1.00),
    "Terraços / Áreas Descobertas": (0.30, 0.60), "Garagem (Subsolo)": (0.50, 0.75), "Estacionamento (terreno)": (0.05, 0.10),
    "Salas com Acabamento": (1.00, 1.00), "Salas sem Acabamento": (0.75, 0.90), "Loja sem Acabamento": (0.40, 0.60),
    "Serviço (unifam. baixa, aberta)": (0.50, 0.50), "Barrilete / Cx D'água / Casa Máquinas": (0.50, 0.75),
    "Piscinas": (0.50, 0.75), "Quintais / Calçadas / Jardins": (0.10, 0.30), "Projeção Terreno sem Benfeitoria": (0.00, 0.00),
}
DEFAULT_PAVIMENTO = {"nome": "Pavimento Tipo", "tipo": "Área Privativa (Autônoma)", "rep": 1, "coef": 1.00, "area": 100.0, "constr": True}

ETAPAS_OBRA = {
    "Serviços Prelimimnares e Fundações":        (7.0, 8.0, 9.0),
    "Estrutura (Supraestrutura)":               (14.0, 16.0, 22.0),
    "Vedações (Alvenaria)":                     (8.0, 10.0, 15.0),
    "Cobertura e Impermeabilização":            (4.0, 5.0, 8.0),
    "Revestimentos de Fachada":                 (5.0, 6.0, 10.0),
    "Instalações (Elétrica e Hidráulica)":      (12.0, 15.0, 18.0),
    "Esquadrias (Portas e Janelas)":            (6.0, 8.0, 12.0),
    "Revestimentos de Piso":                    (8.0, 10.0, 15.0),
    "Revestimentos de Parede":                  (6.0, 8.0, 12.0),
    "Revestimentos de Forro":                   (3.0, 4.0, 6.0),
    "Pintura":                                  (4.0, 5.0, 8.0),
    "Serviços Complementares e Externos":       (3.0, 5.0, 10.0)
}

DEFAULT_CUSTOS_INDIRETOS = {
    "IRPJ/ CS/ PIS/ COFINS":        (3.0, 4.0, 6.0),
    "Corretagem":                   (3.0, 3.61, 5.0),
    "Publicidade":                  (0.5, 0.9, 2.0),
    "Manutenção":                   (0.3, 0.5, 1.0),
    "Custo Fixo da Incorporadora": (3.0, 4.0, 6.0),
    "Assessoria Técnica":           (0.5, 0.7, 1.5),
    "Projetos":                     (0.4, 0.52, 1.5),
    "Licenças e Incorporação":      (0.1, 0.2, 0.5),
    "Outorga Onerosa":              (0.0, 0.0, 10.0),
    "Condomínio":                   (0.0, 0.0, 0.5),
    "IPTU":                         (0.05, 0.07, 0.2),
    "Preparação do Terreno":        (0.2, 0.33, 1.0),
    "Financiamento Bancário":       (1.0, 1.9, 3.0),
}
DEFAULT_CUSTOS_INDIRETOS_FIXOS = {}

def init_storage(path):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f: json.dump([], f, ensure_ascii=False, indent=4)
def load_json(path):
    init_storage(path);
    with open(path, "r", encoding="utf-8") as f: return json.load(f)
def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
def list_projects():
    return load_json(JSON_PATH)
def save_project(info):
    projs = load_json(JSON_PATH)
    if info.get("id"):
        projs = [p if p["id"] != info["id"] else info for p in projs]
    else:
        pid = (max(p["id"] for p in projs) + 1) if projs else 1
        info["id"] = pid; info["created_at"] = datetime.utcnow().isoformat(); projs.append(info)
    save_json(projs, JSON_PATH)
def load_project(pid):
    project_data = next((p for p in load_json(JSON_PATH) if p["id"] == pid), None)
    if project_data and 'etapas_percentuais' in project_data:
        etapas = project_data['etapas_percentuais']
        if etapas and isinstance(list(etapas.values())[0], (int, float)):
            project_data['etapas_percentuais'] = {k: {"percentual": v, "fonte": "Manual"} for k, v in etapas.items()}
    if project_data and 'custos_indiretos_percentuais' in project_data:
        custos = project_data['custos_indiretos_percentuais']
        if custos and isinstance(list(custos.values())[0], (int, float)):
            project_data['custos_indiretos_percentuais'] = {k: {"percentual": v, "fonte": "Manual"} for k, v in custos.items()}
    return project_data
def delete_project(pid):
    projs = [p for p in load_json(JSON_PATH) if p["id"] != pid]; save_json(projs, JSON_PATH)
def save_to_historico(info, tipo_custo):
    path = HISTORICO_DIRETO_PATH if tipo_custo == 'direto' else HISTORICO_INDIRETO_PATH
    session_key = 'etapas_percentuais' if tipo_custo == 'direto' else 'custos_indiretos_percentuais'
    historico = load_json(path)
    percentuais = {k: v['percentual'] for k, v in info[session_key].items()}
    nova_entrada = { "id": (max(p["id"] for p in historico) + 1) if historico else 1, "nome": info["nome"],
        "data": datetime.now().strftime("%Y-%m-%d"), "percentuais": percentuais }
    historico.append(nova_entrada)
    save_json(historico, path)
    st.toast(f"Custos {tipo_custo} de '{info['nome']}' arquivados no histórico!", icon="📚")

def render_metric_card(title, value, color="#31708f"):
    return f"""<div style="background-color:{color}; border-radius:6px; padding:15px; text-align:center; height:100%;"><div style="color:#fff; font-size:16px; margin-bottom:4px;">{title}</div><div style="color:#fff; font-size:28px; font-weight:bold;">{value}</div></div>"""

def handle_percentage_redistribution(session_key, constants_dict):
    previous_key = f"previous_{session_key}"
    if previous_key not in st.session_state: st.session_state[previous_key] = {k: v.copy() for k, v in st.session_state[session_key].items()}
    current, previous = st.session_state[session_key], st.session_state[previous_key]
    if current == previous: return
    changed_item_key = next((k for k, v in current.items() if v['percentual'] != previous.get(k, {}).get('percentual')), None)
    if not changed_item_key: return
    st.session_state.redistribution_occured = True
    delta = current[changed_item_key]['percentual'] - previous[changed_item_key]['percentual']
    total_others = sum(v['percentual'] for k, v in previous.items() if k != changed_item_key)
    if total_others > 0:
        for item, values in current.items():
            if item != changed_item_key:
                min_val, _, max_val = constants_dict[item]
                proportion = previous[item]['percentual'] / total_others
                new_percent = values['percentual'] - (delta * proportion)
                current[item]['percentual'] = max(min_val, min(new_percent, max_val))
    st.session_state[previous_key] = {k: v.copy() for k, v in current.items()}; st.rerun()

def render_sidebar(form_key):
    st.sidebar.title("Estudo de Viabilidade")
    st.sidebar.divider()
    st.sidebar.page_link("Início.py", label="Início", icon="🏠")
    st.sidebar.page_link("pages/1_Custos_Diretos.py", label="Custos Diretos", icon="🏗️")
    st.sidebar.page_link("pages/2_Custos_Indiretos.py", label="Custos Indiretos", icon="💸")
    st.sidebar.page_link("pages/3_Resultados_e_Indicadores.py", label="Resultados e Indicadores", icon="📈")
    st.sidebar.divider()
    if "projeto_info" in st.session_state:
        info = st.session_state.projeto_info
        st.sidebar.subheader(f"Projeto: {info['nome']}")
        with st.sidebar.expander("📝 Dados Gerais do Projeto"):
            with st.form(key=f"edit_form_sidebar_{form_key}"):
                info['nome'] = st.text_input("Nome", value=info['nome'])
                info['area_terreno'] = st.number_input("Área Terreno (m²)", value=info['area_terreno'], format="%.2f")
                info['area_privativa'] = st.number_input("Área Privativa (m²)", value=info['area_privativa'], format="%.2f")
                info['num_unidades'] = st.number_input("Unidades", value=info['num_unidades'], step=1)
                st.form_submit_button("Atualizar")
        with st.sidebar.expander("📈 Configurações de Mercado"):
                custos_config = info.get('custos_config', {})
                custos_config['preco_medio_venda_m2'] = st.number_input("Preço Médio Venda (R$/m² privativo)", min_value=0.0, value=custos_config.get('preco_medio_venda_m2', 10000.0), format="%.2f")
                info['custos_config'] = custos_config
        with st.sidebar.expander("💰 Configuração de Custos"):
            custos_config = info.get('custos_config', {})
            custos_config['custo_terreno_m2'] = st.number_input("Custo do Terreno por m² (R$)", min_value=0.0, value=custos_config.get('custo_terreno_m2', 2500.0), format="%.2f")
            custos_config['custo_area_privativa'] = st.number_input("Custo de Construção (R$/m² privativo)", min_value=0.0, value=custos_config.get('custo_area_privativa', 4500.0), step=100.0, format="%.2f")
            info['custos_config'] = custos_config
        st.sidebar.divider()
        if st.sidebar.button("💾 Salvar Todas as Alterações", use_container_width=True, type="primary"):
            if 'etapas_percentuais' in st.session_state: info['etapas_percentuais'] = st.session_state.etapas_percentuais
            if 'custos_indiretos_percentuais' in st.session_state: info['custos_indiretos_percentuais'] = st.session_state.custos_indiretos_percentuais
            save_project(st.session_state.projeto_info); st.sidebar.success("Projeto salvo com sucesso!")
        with st.sidebar.expander("📚 Arquivar no Histórico"):
            if st.button("Arquivar Custos Diretos", use_container_width=True):
                info['etapas_percentuais'] = st.session_state.etapas_percentuais; save_to_historico(info, 'direto')
            if st.button("Arquivar Custos Indiretos", use_container_width=True):
                info['custos_indiretos_percentuais'] = st.session_state.custos_indiretos_percentuais; save_to_historico(info, 'indireto')
        if st.sidebar.button("Mudar de Projeto", use_container_width=True):
            keys_to_delete = ["projeto_info", "pavimentos", "etapas_percentuais", "previous_etapas_percentuais", "custos_indiretos_percentuais", "previous_custos_indiretos_percentuais"]
            for key in keys_to_delete:
                if key in st.session_state: del st.session_state[key]
            st.switch_page("Início.py")

def generate_pdf_report(info, vgv_total, valor_total_despesas, lucratividade_valor, lucratividade_percentual,
                       custo_direto_total, custo_indireto_calculado, custo_terreno_total, area_construida_total,
                       custos_config, custos_indiretos_percentuais):

    def create_html_card(title, value, color):
        return f"""
        <td style="background-color: {color}; color: white; border-radius: 8px; padding: 15px; text-align: center; width: 25%;">
            <div style="font-size: 14px; font-weight: bold; margin-bottom: 5px;">{title}</div>
            <div style="font-size: 22px; font-weight: bold;">{value}</div>
        </td>
        """

    relacao_ac_priv = area_construida_total / info.get('area_privativa', 1) if info.get('area_privativa', 1) > 0 else 0

    # Construir a tabela de custos indiretos
    tabela_custos_indiretos_html = ""
    for item, values in custos_indiretos_percentuais.items():
        percentual = values.get('percentual', 0)
        custo = vgv_total * (float(percentual) / 100)
        tabela_custos_indiretos_html += f"""
        <tr>
            <td>{item}</td>
            <td style="text-align: right;">{percentual:.2f}%</td>
            <td style="text-align: right;">R$ {fmt_br(custo)}</td>
        </tr>
        """

    html_string = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
        <style>
            @page {{
                size: A4;
                margin: 1.5cm;
                @top-center {{
                    content: "Relatório de Viabilidade - {info.get('nome', 'N/A')}";
                    font-family: 'Roboto', sans-serif;
                    font-size: 10px;
                    color: #888;
                }}
                @bottom-right {{
                    content: "Página " counter(page) " de " counter(pages);
                    font-family: 'Roboto', sans-serif;
                    font-size: 10px;
                    color: #888;
                }}
            }}
            body {{
                font-family: 'Roboto', sans-serif;
                color: #333;
            }}
            .cover-page {{
                page-break-after: always;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100%;
                text-align: center;
            }}
            .cover-page h1 {{
                font-size: 36px;
                color: #1a5276;
                margin-bottom: 20px;
            }}
            .cover-page h2 {{
                font-size: 28px;
                color: #1f618d;
                margin-bottom: 40px;
            }}
            .cover-page p {{
                font-size: 16px;
                color: #555;
            }}
            h2.section-title {{
                color: #1f618d;
                border-bottom: 2px solid #aed6f1;
                padding-bottom: 5px;
                margin-top: 30px;
                margin-bottom: 20px;
            }}
            table.card-container {{
                width: 100%;
                border-spacing: 10px;
                margin-bottom: 20px;
            }}
            table.data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            table.data-table th, table.data-table td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            table.data-table th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="cover-page">
            <h1>Relatório de Viabilidade de Empreendimento</h1>
            <h2>{info.get('nome', 'N/A')}</h2>
            <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>

        <h2 class="section-title">Dados de Área e Venda</h2>
        <table class="card-container">
            <tr>
                {create_html_card("Área Privativa", f"{fmt_br(info.get('area_privativa', 0))} m²", "#1f77b4")}
                {create_html_card("Área Construída", f"{fmt_br(area_construida_total)} m²", "#ff7f0e")}
                {create_html_card("Preço Venda / m²", f"R$ {fmt_br(custos_config.get('preco_medio_venda_m2', 0))}", "#2ca02c")}
                {create_html_card("Relação AC/AP", f"{relacao_ac_priv:.2f}", "#d62728")}
            </tr>
        </table>

        <h2 class="section-title">Resultados Financeiros</h2>
        <table class="card-container">
             <tr>
                {create_html_card("VGV Total", f"R$ {fmt_br(vgv_total)}", "#00829d")}
                {create_html_card("Custo Total", f"R$ {fmt_br(valor_total_despesas)}", "#6a42c1")}
                {create_html_card("Lucro Bruto", f"R$ {fmt_br(lucratividade_valor)}", "#3c763d")}
                {create_html_card("Margem de Lucro", f"{lucratividade_percentual:.2f}%", "#a94442")}
            </tr>
        </table>

        <h2 class="section-title">Composição do Custo Total</h2>
        <table class="card-container">
            <tr>
                {create_html_card(f"Custo Direto ({(custo_direto_total / valor_total_despesas * 100) if valor_total_despesas > 0 else 0:.2f}%)", f"R$ {fmt_br(custo_direto_total)}", "#31708f")}
                {create_html_card(f"Custo Indireto ({(custo_indireto_calculado / valor_total_despesas * 100) if valor_total_despesas > 0 else 0:.2f}%)", f"R$ {fmt_br(custo_indireto_calculado)}", "#8a6d3b")}
                {create_html_card(f"Custo do Terreno ({(custo_terreno_total / valor_total_despesas * 100) if valor_total_despesas > 0 else 0:.2f}%)", f"R$ {fmt_br(custo_terreno_total)}", "#6f42c1")}
            </tr>
        </table>

        <h2 class="section-title">Indicadores por Área Construída</h2>
        <table class="card-container">
            <tr>
                {create_html_card("Terreno / Custo Total", f"{(custo_terreno_total / valor_total_despesas * 100) if valor_total_despesas > 0 else 0:.2f}%", "#fd7e14")}
                {create_html_card("Custo Direto / m²", f"R$ {fmt_br(custo_direto_total / area_construida_total if area_construida_total > 0 else 0)}", "#20c997")}
                {create_html_card("Custo Indireto / m²", f"R$ {fmt_br(custo_indireto_calculado / area_construida_total if area_construida_total > 0 else 0)}", "#31708f")}
                {create_html_card("Custo Total / m²", f"R$ {fmt_br(valor_total_despesas / area_construida_total if area_construida_total > 0 else 0)}", "#8a6d3b")}
            </tr>
        </table>

        <h2 class="section-title">Detalhamento dos Custos Indiretos</h2>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Item</th>
                    <th style="text-align: right;">Percentual (%)</th>
                    <th style="text-align: right;">Custo (R$)</th>
                </tr>
            </thead>
            <tbody>
                {tabela_custos_indiretos_html}
            </tbody>
        </table>
    </body>
    </html>
    """
    return HTML(string=html_string).write_pdf()
