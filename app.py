import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

# --- 1. CONFIGURAÇÃO E GESTÃO DE DADOS ---
JSON_PATH = "projects.json"

# --- DADOS E COEFICIENTES DO NEGÓCIO ---
TIPOS_PAVIMENTO = {
    "Área Privativa (Autônoma)": (1.00, 1.00), "Áreas de lazer ambientadas": (2.00, 4.00), "Varandas": (0.75, 1.00),
    "Terraços / Áreas Descobertas": (0.30, 0.60), "Garagem (Subsolo)": (0.50, 0.75), "Estacionamento (terreno)": (0.05, 0.10),
    "Salas com Acabamento": (1.00, 1.00), "Salas sem Acabamento": (0.75, 0.90), "Loja sem Acabamento": (0.40, 0.60),
    "Serviço (unifam. baixa, aberta)": (0.50, 0.50), "Barrilete / Cx D'água / Casa Máquinas": (0.50, 0.75),
    "Piscinas": (0.50, 0.75), "Quintais / Calçadas / Jardins": (0.10, 0.30), "Projeção Terreno sem Benfeitoria": (0.00, 0.00),
}
DEFAULT_PAVIMENTO = {"nome": "Pavimento Tipo", "tipo": "Área Privativa (Autônoma)", "rep": 1, "coef": 1.00, "area": 100.0, "constr": True}
ETAPAS_OBRA = {
    "Serviços Preliminares e Fundações": 8.0, "Estrutura (Supraestrutura)": 16.0, "Vedações (Alvenaria)": 10.0,
    "Cobertura e Impermeabilização": 5.0, "Revestimentos de Fachada": 6.0, "Instalações (Elétrica e Hidráulica)": 15.0,
    "Esquadrias (Portas e Janelas)": 8.0, "Revestimentos de Piso": 10.0, "Revestimentos de Parede": 8.0,
    "Revestimentos de Forro": 4.0, "Pintura": 5.0, "Serviços Complementares e Externos": 5.0
}
DEFAULT_CUSTOS_INDIRETOS = {
    "IRPJ/CS/PIS/COFINS (sobre VGV-RET)": 4.8, "Corretagem (sobre VGV)": 3.61, "Publicidade (sobre VGV)": 0.9,
    "Manutenção (sobre VGV)": 0.5, "Custo Fixo da Construtora / Incorporadora": 4.0, "Assessoria Técnica (sobre VGV)": 0.7,
    "Projetos (sobre VGV)": 0.52, "Licenças e Incorporação (sobre VGV)": 0.2, "Outorga Onerosa (sobre VGV)": 0.0,
    "Condomínio (sobre o VGV)": 0.0, "IPTU (sobre o VGV)": 0.07, "Preparação do Terreno (sobre o VGV)": 0.33,
    "Financiamento Bancário (R$)": 5500000.0, "Juros Financiamento (R$)": 5500000.0
}


# --- FUNÇÕES AUXILIARES ---
def init_storage():
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
# ... (Copie todas as outras funções auxiliares aqui: load_all_projects, save_project, etc.)
# (Para manter a resposta concisa, vou omitir as funções que não mudaram, mas você deve mantê-las no seu código)
def load_all_projects():
    init_storage()
    with open(JSON_PATH, "r", encoding="utf-8") as f: return json.load(f)
def save_all_projects(projs):
    with open(JSON_PATH, "w", encoding="utf-8") as f: json.dump(projs, f, ensure_ascii=False, indent=4)
def list_projects():
    return [{"id": p["id"], "nome": p["nome"]} for p in load_all_projects()]
def save_project(info):
    projs = load_all_projects()
    if info.get("id"):
        projs = [p if p["id"] != info["id"] else info for p in projs]
    else:
        pid = (max(p["id"] for p in projs) + 1) if projs else 1
        info["id"] = pid
        info["created_at"] = datetime.utcnow().isoformat()
        projs.append(info)
    save_all_projects(projs)
def load_project(pid):
    return next((p for p in load_all_projects() if p["id"] == pid), None)
def delete_project(pid):
    projs = [p for p in load_all_projects() if p["id"] != pid]
    save_all_projects(projs)
def fmt_br(valor):
    s = f"{valor:,.2f}"; return s.replace(",", "X").replace(".", ",").replace("X", ".")
def render_metric_card(title, value, color="#31708f"):
    return f"""<div style="background-color:{color}; border-radius:6px; padding:15px; text-align:center; height:100%;"><div style="color:#fff; font-size:16px; margin-bottom:4px;">{title}</div><div style="color:#fff; font-size:28px; font-weight:bold;">{value}</div></div>"""
def handle_percentage_redistribution(etapas_key='etapas_percentuais'):
    if 'previous_etapas' not in st.session_state: st.session_state.previous_etapas = st.session_state[etapas_key].copy()
    current, previous = st.session_state[etapas_key], st.session_state.previous_etapas
    if current == previous: return
    changed_etapa = next((e for e, p in current.items() if p != previous.get(e)), None)
    if changed_etapa:
        delta = current[changed_etapa] - previous[changed_etapa]
        total_others = sum(v for k, v in previous.items() if k != changed_etapa)
        if total_others > 0:
            for e, p in current.items():
                if e != changed_etapa: current[e] = max(0, p - (delta * (previous[e] / total_others)))
        factor = 100 / sum(current.values())
        for e in current: current[e] *= factor
    st.session_state.previous_etapas = current.copy(); st.rerun()


# --- PÁGINA 1: ORÇAMENTO DIRETO ---
def page_budget_tool():
    # (Copie aqui a função page_budget_tool completa da versão anterior)
    # ...
    pass # Placeholder

# --- PÁGINA 2: ANÁLISE DE VIABILIDADE ---
def page_viability_analysis():
    st.title("📊 Análise de Viabilidade do Empreendimento")
    info = st.session_state.projeto_info

    # --- Cálculos Preliminares (Puxados do Orçamento Direto) ---
    pavimentos_df = pd.DataFrame(info.get('pavimentos', []))
    custo_direto_total = 0; area_construida_total = 0; area_privativa_total = info.get('area_privativa', 0)
    if not pavimentos_df.empty:
        custos_config = info.get('custos_config', {})
        cub = custos_config.get('cub', 4500.0)
        custo_contencao_m2 = custos_config.get('custo_contencao_m2', 400.0)
        pavimentos_df["area_total"] = pavimentos_df["area"] * pavimentos_df["rep"]
        pavimentos_df["area_eq"] = pavimentos_df["area_total"] * pavimentos_df["coef"]
        pavimentos_df["area_constr"] = pavimentos_df.apply(lambda r: r["area_total"] if r["constr"] else 0.0, axis=1)
        pavimentos_df["custo_direto"] = pavimentos_df["area_eq"] * cub
        custo_direto_obra = pavimentos_df["custo_direto"].sum()
        area_subsolo = pavimentos_df[pavimentos_df['tipo'].str.contains("Garagem \(Subsolo\)", regex=True)]["area_total"].sum()
        custo_contencao = area_subsolo * custo_contencao_m2
        custo_direto_total = custo_direto_obra + custos_config.get('outros', 0.0) + custo_contencao
        area_construida_total = pavimentos_df["area_constr"].sum()

    # --- 1. SEÇÃO DE VGV ---
    st.header("Receitas / VGV")
    with st.container(border=True):
        st.subheader("Composição de Unidades e VGV")
        if 'unidades_vgv' not in info: info['unidades_vgv'] = []
        edited_unidades = st.data_editor(
            pd.DataFrame(info['unidades_vgv']), num_rows="dynamic", use_container_width=True, key="editor_unidades",
            column_config={
                "Tipo": st.column_config.TextColumn(required=True),
                "Quant.": st.column_config.NumberColumn(required=True, min_value=1, step=1),
                "Área Privativa (m²)": st.column_config.NumberColumn(required=True, format="%.2f m²"),
                "Valor Médio de Venda (R$)": st.column_config.NumberColumn(required=True, format="R$ %.2f"),
            })
        info['unidades_vgv'] = edited_unidades.to_dict('records')
        unidades_df = pd.DataFrame(info['unidades_vgv'])
        vgv_total = (unidades_df['Quant.'] * unidades_df['Valor Médio de Venda (R$)']).sum() if not unidades_df.empty else 0
        st.metric("VGV (Valor Geral de Vendas) Total", f"R$ {fmt_br(vgv_total)}")

    # --- 2. SEÇÃO DE CUSTOS ---
    st.header("Detalhamento de Custos Totais")
    with st.container(border=True):
        st.metric("Custo Direto Total (Obra + Contenção + Outros)", f"R$ {fmt_br(custo_direto_total)}")
        st.divider()
        st.subheader("Custos Indiretos")
        if 'custos_indiretos' not in info: info['custos_indiretos'] = DEFAULT_CUSTOS_INDIRETOS.copy()
        custos_indiretos = info['custos_indiretos']
        cols = st.columns(3)
        i = 0
        custo_indireto_calculado = 0
        for key, value in custos_indiretos.items():
            with cols[i % 3]:
                label, base = (key.split('(')[0].strip(), key.split('(')[1].split(')')[0]) if '(' in key else (key, None)
                if base and "VGV" in base:
                    percent = st.number_input(f"{label} (%)", value=float(value), format="%.2f", key=key)
                    custos_indiretos[key] = percent
                    custo_indireto_calculado += vgv_total * (percent / 100.0)
                else:
                    valor_fixo = st.number_input(label, value=float(value), format="%.2f", key=key)
                    custos_indiretos[key] = valor_fixo
                    custo_indireto_calculado += valor_fixo
            i += 1
        st.metric("Custo Indireto Total (Calculado)", f"R$ {fmt_br(custo_indireto_calculado)}")

        st.divider()
        st.subheader("Custo do Terreno")
        custos_config = info.get('custos_config', {})
        custos_config['custo_terreno_m2'] = st.number_input("Custo do Terreno por m² (R$)", value=custos_config.get('custo_terreno_m2', 2500.0), format="%.2f")
        custo_terreno_total = info.get('area_terreno', 0) * custos_config['custo_terreno_m2']
        st.metric("Custo Total do Terreno", f"R$ {fmt_br(custo_terreno_total)}")
        info['custos_config'] = custos_config

    # --- 3. CÁLCULO TOTAL E RESULTADOS ---
    valor_total_despesas = custo_direto_total + custo_indireto_calculado + custo_terreno_total
    lucratividade_valor = vgv_total - valor_total_despesas
    lucratividade_percentual = (lucratividade_valor / vgv_total) * 100 if vgv_total > 0 else 0

    st.header("Resultados e Indicadores Chave")
    with st.container(border=True):
        res_cols = st.columns(4)
        res_cols[0].metric("VGV Total", f"R$ {fmt_br(vgv_total)}")
        res_cols[1].metric("Custo Total do Empreendimento", f"R$ {fmt_br(valor_total_despesas)}")
        res_cols[2].metric("Lucro Bruto", f"R$ {fmt_br(lucratividade_valor)}")
        res_cols[3].metric("Margem de Lucro", f"{lucratividade_percentual:.2f}%")

        st.divider()
        st.subheader("Indicadores por Área")
        indicadores_data = {
            'TERRENO %': [f"{(custo_terreno_total / valor_total_despesas * 100 if valor_total_despesas > 0 else 0):.2f}%"],
            'CUSTO DIRETO (R$/m²)': [f"R$ {fmt_br(custo_direto_total / area_construida_total if area_construida_total > 0 else 0)}"],
            'CUSTO INDIRETO (R$/m²)': [f"R$ {fmt_br(custo_indireto_calculado / area_construida_total if area_construida_total > 0 else 0)}"],
            'CUSTO TOTAL (R$/m²)': [f"R$ {fmt_br(valor_total_despesas / area_construida_total if area_construida_total > 0 else 0)}"]
        }
        st.table(pd.DataFrame(indicadores_data))


# --- CONTROLE PRINCIPAL DA APLICAÇÃO ---
def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="wide")
    init_storage()

    if "projeto_info" not in st.session_state:
        # TELA DE SELEÇÃO DE PROJETO
        # (Copie aqui a função page_project_selection completa da versão anterior)
        # ...
        pass # Placeholder
    else:
        info = st.session_state.projeto_info
        st.sidebar.title(f"Projeto: {info['nome']}")
        st.sidebar.markdown(f"ID: {info['id']}")
        
        # --- NAVEGAÇÃO PRINCIPAL ---
        page = st.sidebar.radio("Navegar", ["Orçamento Direto", "Análise de Viabilidade"])
        
        st.sidebar.divider()
        if st.sidebar.button("💾 Salvar Todas as Alterações", use_container_width=True, type="primary"):
            save_project(st.session_state.projeto_info)
            st.sidebar.success("Projeto salvo com sucesso!")
        
        if st.sidebar.button("Mudar de Projeto", use_container_width=True):
            # Limpa o estado da sessão para evitar vazamento de dados entre projetos
            keys_to_delete = ["projeto_info", "pavimentos", "etapas_percentuais", "previous_etapas"]
            for key in keys_to_delete:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        if page == "Orçamento Direto":
            page_budget_tool() # Chama a função da primeira página
        elif page == "Análise de Viabilidade":
            page_viability_analysis() # Chama a função da nova página


if __name__ == "__main__":
    # Para a resposta final, você precisará copiar o conteúdo das funções 
    # page_budget_tool e page_project_selection da nossa versão anterior 
    # para os locais indicados como #Placeholder
    main()
