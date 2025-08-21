import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# —————— Configuração do arquivo JSON ——————
JSON_PATH = "projects.json"

def init_storage():
    if not os.path.exists(JSON_PATH):
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)

def load_all_projects() -> list:
    init_storage()
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_all_projects(projs: list):
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(projs, f, ensure_ascii=False, indent=2)

def list_projects() -> list:
    projs = load_all_projects()
    return [{"id": p["id"], "nome": p["nome"], "created_at": p.get("created_at")} for p in projs]

def save_project(info: dict) -> int:
    projs = load_all_projects()
    if info.get("id"):
        # Atualiza existente
        pid = info["id"]
        for p in projs:
            if p["id"] == pid:
                p.update(info)
                break
    else:
        # Cria novo
        existing_ids = [p["id"] for p in projs] if projs else []
        pid = max(existing_ids) + 1 if existing_ids else 1
        info["id"] = pid
        info["created_at"] = datetime.utcnow().isoformat()
        projs.append(info)
    save_all_projects(projs)
    return pid

def load_project(pid: int) -> dict:
    for p in load_all_projects():
        if p["id"] == pid:
            return p
    return None

def delete_project(pid: int):
    projs = [p for p in load_all_projects() if p["id"] != pid]
    save_all_projects(projs)

# —————— Coeficientes por NBR 12721 ——————
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

# —————— Função para formatar números no padrão BR ——————
def fmt_br(valor: float) -> str:
    s = f"{valor:,.2f}"            # ex: 1234567.89 -> "1,234,567.89"
    s = s.replace(",", "_")        # "1_234_567.89"
    s = s.replace(".", ",")        # "1_234_567,89"
    s = s.replace("_", ".")        # "1.234.567,89"
    return s

# —————— Função principal ——————
def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="wide")
    init_storage()

    # ——— Tela Inicial ———
    if "projeto_info" not in st.session_state:
        st.header("🏢 Orçamento Paramétrico – Gestão de Projetos")
        projetos = list_projects()
        escolha = st.selectbox(
            "📂 Selecione um projeto ou crie um novo",
            ["➕ Novo Projeto"] + [f"{p['id']} – {p['nome']}" for p in projetos],
            key="sel_proj"
        )

        if escolha != "➕ Novo Projeto":
            pid = int(escolha.split("–")[0].strip())
            st.session_state.projeto_info = load_project(pid)
            # tenta recarregar imediatamente
            try:
                st.experimental_rerun()
            except Exception:
                st.stop()

        st.markdown("---")
        c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 1])
        nome            = c1.text_input("Nome", key="new_nome")
        area_terreno    = c2.number_input(
            "Área Terreno (m²)",
            min_value=0.0,
            format="%0.2f",
            key="new_area_terreno"
        )
        area_privativa  = c3.number_input(
            "Área Privativa (m²)",
            min_value=0.0,
            format="%0.2f",
            key="new_area_privativa"
        )
        num_unidades    = c4.number_input(
            "Unidades",
            min_value=1,
            step=1,
            format="%d",
            key="new_num_unidades"
        )
        endereco = st.text_input("Endereço", key="new_endereco")

        if st.button("💾 Salvar Projeto"):
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
            try:
                st.experimental_rerun()
            except Exception:
                st.success("✅ Projeto salvo! Atualize a página para continuar.")
                st.stop()

        return  # interrompe o fluxo até haver projeto_info

    # ——— Tela de Orçamento ———
    info = st.session_state.projeto_info

    # Sidebar: informações do projeto + excluir
    with st.sidebar:
        st.subheader("Projeto Ativo")
        st.write(f"**{info['nome']}**")
        if st.button("🗑️ Excluir Projeto"):
            delete_project(info["id"])
            del st.session_state.projeto_info
            try:
                st.experimental_rerun()
            except Exception:
                st.success("✅ Projeto excluído! Atualize a página.")
                st.stop()

    # Cabeçalho resumido
    st.title("🏗️ Orçamento Paramétrico de Edifícios Residenciais")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Nome", info["nome"])
    m2.metric("Área Terreno (m²)", fmt_br(info["area_terreno"]))
    m3.metric("Área Privativa (m²)", fmt_br(info["area_privativa"]))
    m4.metric("Unidades", str(info["num_unidades"]))

    # Parâmetro de custo
    unit_cost = st.sidebar.number_input(
        "Custo por m² (R$)",
        min_value=0.0,
        value=4500.0,
        step=100.0,
        format="%0.2f"
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("© 2025 Sua Empresa")

    # Entrada de pavimentos
    qtd = st.number_input(
        "Número de Pavimentos",
        min_value=1,
        max_value=50,
        value=1,
        step=1
    )
    st.markdown("#### 🏢 Dados dos Pavimentos")
    header_cols = st.columns([2,3,1,1,1,1,1])
    for title, col in zip(
        ["Nome","Tipo","Rep.","Coef.","Área (m²)","Área Total","Incluir"],
        header_cols
    ):
        col.markdown(f"**{title}**")

    registros = []
    for i in range(1, qtd + 1):
        c1, c2, c3, c4, c5, c6, c7 = st.columns([2,3,1,1,1,1,1])
        nome_i = c1.text_input(f"", value=f"Pavimento {i}", key=f"nome_{i}")
        tipo_i = c2.selectbox("", list(TIPOS_PAVIMENTO.keys()), key=f"tipo_{i}")
        rep_i  = c3.number_input("", min_value=1, value=1, step=1, key=f"rep_{i}")

        min_c, max_c = TIPOS_PAVIMENTO[tipo_i]
        if min_c == max_c:
            coef_i = c4.number_input(
                "", min_value=min_c, max_value=max_c,
                value=min_c, format="%0.2f", disabled=True,
                key=f"coef_{i}"
            )
        else:
            coef_i = c4.slider(
                "", min_value=min_c, max_value=max_c,
                value=(min_c + max_c) / 2,
                step=0.01, format="%0.2f",
                key=f"coef_{i}"
            )

        area_i = c5.number_input(
            "", min_value=0.0, value=100.0,
            step=1.0, format="%0.2f",
            key=f"area_{i}"
        )
        area_total_i = area_i * rep_i
        c6.markdown(
            f"<p style='text-align:right;'>{fmt_br(area_total_i)}</p>",
            unsafe_allow_html=True
        )

        constr_i = c7.checkbox("", value=True, key=f"constr_{i}")

        registros.append({
            "nome": nome_i,
            "tipo": tipo_i,
            "rep": rep_i,
            "coef": coef_i,
            "area": area_i,
            "area_total": area_total_i,
            "constr": constr_i
        })

    # DataFrame e cálculos
    df = pd.DataFrame(registros)
    df["area_eq"] = df["area"] * df["coef"] * df["rep"]
    df["custo"]   = df["area_eq"] * unit_cost

    soma_area = df[df["constr"]]["area_total"].sum()
    st.markdown(
        f"<h4 style='text-align:right;'>"
        f"Somatório Área Construída: {fmt_br(soma_area)} m²"
        f"</h4>",
        unsafe_allow_html=True
    )

    # Resumo
    total_eq   = df["area_eq"].sum()
    total_cust = df["custo"].sum()
    st.markdown("## 💰 Resumo do Orçamento")
    r1, r2 = st.columns(2)
    r1.success(f"Área Equivalente Total: {fmt_br(total_eq)} m²")
    r2.success(f"Custo Total do Projeto: R$ {fmt_br(total_cust)}")

    # Detalhamento e download
    st.markdown("### 📑 Detalhamento por Pavimento")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False, sep=";").encode("utf-8")
    st.download_button(
        "⬇️ Baixar CSV",
        data=csv,
        file_name="orcamento_parametrico.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
