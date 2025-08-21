import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# caminho do arquivo JSON
JSON_PATH = "projects.json"

# === FUNÇÕES DE ARMAZENAMENTO JSON ===

def init_storage():
    """Garante que o arquivo JSON exista."""
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def load_all_projects() -> list:
    """Carrega todos os projetos do JSON."""
    init_storage()
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_all_projects(projs: list):
    """Escreve a lista completa de projetos no JSON."""
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(projs, f, ensure_ascii=False, indent=2)

def list_projects() -> list:
    """Retorna lista de dicts com id, nome e created_at para listar."""
    projs = load_all_projects()
    return [{"id": p["id"], "nome": p["nome"], "created_at": p.get("created_at")} for p in projs]

def save_project(info: dict) -> int:
    """
    Insere ou atualiza um projeto.
    Se info tiver 'id', atualiza; senão, cria novo id e insere.
    Retorna o id do projeto.
    """
    projs = load_all_projects()
    now = datetime.utcnow().isoformat()
    if info.get("id"):
        pid = info["id"]
        for p in projs:
            if p["id"] == pid:
                p.update({
                    "nome": info["nome"],
                    "area_terreno": info["area_terreno"],
                    "endereco": info["endereco"],
                    "area_privativa": info["area_privativa"],
                    "num_unidades": info["num_unidades"],
                })
                break
    else:
        existing_ids = [p["id"] for p in projs] if projs else []
        pid = max(existing_ids) + 1 if existing_ids else 1
        novo = {
            "id": pid,
            "nome": info["nome"],
            "area_terreno": info["area_terreno"],
            "endereco": info["endereco"],
            "area_privativa": info["area_privativa"],
            "num_unidades": info["num_unidades"],
            "created_at": now
        }
        projs.append(novo)

    save_all_projects(projs)
    return pid

def load_project(pid: int) -> dict:
    """Retorna o projeto com aquele id, ou None."""
    projs = load_all_projects()
    for p in projs:
        if p["id"] == pid:
            return p
    return None

def delete_project(pid: int):
    """Remove o projeto com o id indicado."""
    projs = load_all_projects()
    projs = [p for p in projs if p["id"] != pid]
    save_all_projects(projs)


# === DICIONÁRIO DE COEFICIENTES (NBR 12721) ===

TIPOS_PAVIMENTO = {
    "Garagem (Subsolo)":               (0.50, 0.75),
    "Área Privativa (Autônoma)":       (1.00, 1.00),
    "Salas com Acabamento":            (1.00, 1.00),
    "Salas sem Acabamento":            (0.75, 0.90),
    "Loja sem Acabamento":             (0.40, 0.60),
    "Varandas":                        (0.75, 1.00),
    "Terraços / Áreas Descobertas":    (0.30, 0.60),
    "Estacionamento (terreno)":        (0.05, 0.10),
    "Projeção Terreno sem Benfeitoria":(0.00, 0.00),
    "Serviço (unifam. baixa, aberta)": (0.50, 0.50),
    "Barrilete":                       (0.50, 0.75),
    "Caixa D'água":                    (0.50, 0.75),
    "Casa de Máquinas":                (0.50, 0.75),
    "Piscinas":                        (0.50, 0.75),
    "Quintais / Calçadas / Jardins":   (0.10, 0.30),
}


def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="wide")
    init_storage()

    # === TELA INICIAL: carregar ou criar novo projeto ===
    if "projeto_info" not in st.session_state:
        st.title("🏢 Orçamento Paramétrico de Edifícios Residenciais")

        col1, col2 = st.columns(2)
        projetos = list_projects()
        sel = col1.selectbox(
            "Carregar Projeto Existente",
            ["— Novo Projeto —"] + [f"{p['id']}: {p['nome']}" for p in projetos]
        )

        if sel != "— Novo Projeto —":
            pid = int(sel.split(":")[0])
            st.session_state.projeto_info = load_project(pid)
            st.experimental_rerun()

        # campos para novo projeto
        with col1:
            nome = st.text_input("Nome do Projeto")
            area_terreno = st.number_input("Área do Terreno (m²)", min_value=0.0, format="%.2f")
            endereco = st.text_area("Endereço")
        with col2:
            area_privativa = st.number_input("Área Privativa Total (m²)", min_value=0.0, format="%.2f")
            num_unidades = st.number_input("Número de Unidades", min_value=1, step=1)

        if st.button("✅ Salvar Projeto"):
            info = {
                "nome": nome,
                "area_terreno": area_terreno,
                "endereco": endereco,
                "area_privativa": area_privativa,
                "num_unidades": num_unidades,
            }
            pid = save_project(info)
            info["id"] = pid
            st.session_state.projeto_info = info
            st.success("Projeto salvo com sucesso!")
            st.experimental_rerun()

        return  # interrompe o fluxo até criar/carregar

    # === TELA PRINCIPAL DE ORÇAMENTO ===
    info = st.session_state.projeto_info

    # sidebar com exclusão
    with st.sidebar:
        st.header("Projeto")
        st.write(f"**{info['nome']}**")
        if st.button("🗑️ Excluir Projeto"):
            delete_project(info["id"])
            del st.session_state.projeto_info
            st.success("Projeto excluído.")
            st.experimental_rerun()

    st.title("🏢 Orçamento Paramétrico de Edifícios Residenciais")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"Nome: {info['nome']}")
        st.info(f"Endereço: {info['endereco']}")
    with col2:
        st.info(f"Área do Terreno: {info['area_terreno']:, .2f} m²")
        st.info(f"Área Privativa: {info['area_privativa']:, .2f} m²")
    with col3:
        st.info(f"Nº Unidades: {info['num_unidades']}")

    unit_cost = st.sidebar.number_input(
        "Custo (R$/m² de Área Privativa)", 0.0, 100_000.0, 4500.0, 100.0, format="%.2f"
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2025 Sua Empresa")

    # coleta de dados de pavimentos
    n = st.number_input("Número de Pavimentos", 1, 50, 1, 1)
    st.markdown("### 🏢 Dados dos Pavimentos")
    cols = st.columns([1.3, 2.5, 0.5, 1, 1, 1, 0.7])
    for h, col in zip(
        ["Nome", "Tipo", "Rep.", "Coef.", "Área (m²)", "Área Total", "Constr."], cols
    ):
        col.markdown(f"**{h}**")

    registros = []
    for i in range(1, n + 1):
        c1, c2, c3, c4, c5, c6, c7 = st.columns([1.3,2.5,0.5,1,1,1,0.7])
        nome_i = c1.text_input("", f"Pavimento {i}", key=f"nome_{i}")
        tipo_i = c2.selectbox("", list(TIPOS_PAVIMENTO.keys()), key=f"tipo_{i}")
        rep_i = c3.number_input("", 1, 100, 1, key=f"rep_{i}")

        cmin, cmax = TIPOS_PAVIMENTO[tipo_i]
        if cmin == cmax:
            coef_i = c4.number_input("", cmin, cmax, cmin, format="%.2f", disabled=True, key=f"coef_{i}")
        else:
            coef_i = c4.slider("", cmin, cmax, (cmin + cmax) / 2, 0.01, format="%.2f", key=f"coef_{i}")

        area_i = c5.number_input("", 0.0, 1e6, 100.0, 1.0, format="%.2f", key=f"area_{i}")
        area_total_i = area_i * rep_i
        c6.markdown(f"<p style='text-align: right'>{area_total_i:,.2f}</p>", unsafe_allow_html=True)
        constr_i = c7.checkbox("", True, key=f"constr_{i}")

        registros.append({
            "nome": nome_i,
            "tipo": tipo_i,
            "rep": rep_i,
            "coef": coef_i,
            "area": area_i,
            "area_total": area_total_i,
            "constr": constr_i
        })

    # montagem do DataFrame e cálculos
    df = pd.DataFrame(registros)
    df["area_eq"] = df["area"] * df["coef"] * df["rep"]
    df["custo"]   = df["area_eq"] * unit_cost

    soma_area = df[df["constr"]]["area_total"].sum()
    st.markdown(f"<h4 style='text-align:right'>Somatório Área Construída: {soma_area:,.2f} m²</h4>",
                unsafe_allow_html=True)

    st.markdown("## 💰 Resumo do Orçamento")
    eq_tot   = df["area_eq"].sum()
    custo_tot= df["custo"].sum()
    c1, c2 = st.columns(2)
    c1.success(f"Área Equivalente Total: {eq_tot:,.2f} m²")
    c2.success(f"Custo Total do Projeto: R$ {custo_tot:,.2f}")

    st.markdown("### 📑 Detalhamento por Pavimento")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar CSV",
        data=csv,
        file_name="orcamento_parametrico.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
