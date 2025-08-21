import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# —————— Configurações e helpers ——————

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
    return [
        {"id": p["id"], "nome": p["nome"], "created_at": p.get("created_at")}
        for p in load_all_projects()
    ]

def save_project(info: dict) -> int:
    projs = load_all_projects()
    if info.get("id"):
        pid = info["id"]
        for p in projs:
            if p["id"] == pid:
                p.update(info)
                break
    else:
        existing = [p["id"] for p in projs] if projs else []
        pid = max(existing) + 1 if existing else 1
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

def fmt_br(valor: float) -> str:
    s = f"{valor:,.2f}"
    s = s.replace(",", "_").replace(".", ",").replace("_", ".")
    return s

def safe_rerun():
    """
    Tenta usar st.experimental_rerun(); se não existir,
    recarrega a página via JS.
    """
    try:
        st.experimental_rerun()
    except Exception:
        st.markdown("<script>window.location.reload()</script>", unsafe_allow_html=True)
        st.stop()


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


# —————— App ——————

def main():
    st.set_page_config(
        page_title="Orçamento Paramétrico",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    init_storage()

    # — Tela Inicial de Seleção/Criação de Projeto ——
    if "projeto_info" not in st.session_state:
        st.header("🏢 Orçamento Paramétrico – Gestão de Projetos")
        projetos = list_projects()
        escolha = st.selectbox(
            "📂 Selecione um projeto ou crie um novo",
            ["➕ Novo Projeto"] +
            [f"{p['id']}  –  {p['nome']}" for p in projetos],
            key="sel_proj"
        )

        if escolha != "➕ Novo Projeto":
            pid = int(escolha.split("–")[0].strip())
            st.session_state.projeto_info = load_project(pid)
            safe_rerun()

        st.markdown("---")
        c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 1])
        nome           = c1.text_input("Nome do Projeto", key="new_nome")
        area_terreno   = c2.number_input(
            "Área Terreno (m²)",
            min_value=0.0, format="%0.2f",
            key="new_area_terreno"
        )
        area_privativa = c3.number_input(
            "Área Privativa (m²)",
            min_value=0.0, format="%0.2f",
            key="new_area_privativa"
        )
        num_unidades   = c4.number_input(
            "Unidades",
            min_value=1, step=1,
            format="%d",
            key="new_num_unidades"
        )
        endereco = st.text_input("Endereço", key="new_endereco")

        if st.button("💾 Salvar Projeto", use_container_width=True):
            info = {
                "nome": nome,
                "area_terreno": area_terreno,
                "area_privativa": area_privativa,
                "num_unidades": num_unidades,
                "endereco": endereco
            }
            pid = save_project(info)
            info["id"] = pid
            st.session_state.projeto_info = info
            safe_rerun()

        return  # para não cair no fluxo principal sem projeto

    # — Fluxo Principal (Orçamento) ——
    info = st.session_state.projeto_info

    # Título
    st.title("🏗️ Orçamento Paramétrico de Edifícios Residenciais")

    # → Destaque colorido dos indicadores principais
    labels = ["Nome", "Área Terreno (m²)", "Área Privativa (m²)", "Unidades"]
    valores = [
        info["nome"],
        fmt_br(info["area_terreno"]),
        fmt_br(info["area_privativa"]),
        str(info["num_unidades"])
    ]
    cores = ["#31708f", "#3c763d", "#8a6d3b", "#a94442"]
    cols = st.columns(4)
    for col, lbl, val, cor in zip(cols, labels, valores, cores):
        col.markdown(
            f"""
            <div style="
                background-color:{cor};
                border-radius:6px;
                padding:12px;
                text-align:center;
            ">
              <div style="color:#fff;font-size:14px;margin-bottom:4px;">{lbl}</div>
              <div style="color:#fff;font-size:24px;font-weight:bold;">{val}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Parâmetro de custo no sidebar
    unit_cost = st.sidebar.number_input(
        "Custo de área privativa (R$/m²)",
        min_value=0.0,
        value=4_500.0,
        step=100.0,
        format="%0.2f"
    )
    st.sidebar.caption("© 2025 Sua Empresa")

    st.markdown("---")

    # — Entrada de Pavimentos —
    st.markdown("#### 🏢 Dados dos Pavimentos")
    col_pav, _ = st.columns([1, 11])
    qtd = col_pav.number_input(
        "Nº de Pavimentos",
        min_value=1,
        max_value=50,
        value=1,
        step=1,
        key="num_pavimentos"
    )

    # Cabeçalho mais elegante
    headers = ["Nome", "Tipo", "Rep.", "Coef.", "Área (m²)", "Área Total", "Incluir"]
    hcols = st.columns([2, 3, 1, 1, 1, 1, 1])
    for hc, title in zip(hcols, headers):
        hc.markdown(
            f"""<div style="
                  background-color:#f0f2f6;
                  padding:8px;
                  border-radius:4px;
                  text-align:center;
                  color:#333;
                  font-weight:600;
               ">{title}</div>""",
            unsafe_allow_html=True
        )

    # Linhas de entrada
    registros = []
    for i in range(1, qtd + 1):
        c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 3, 1, 1, 1, 1, 1])
        nome_i = c1.text_input(f"", value=f"Pavimento {i}", key=f"nome_{i}")
        tipo_i = c2.selectbox("", list(TIPOS_PAVIMENTO.keys()), key=f"tipo_{i}")
        rep_i  = c3.number_input("", min_value=1, value=1, step=1, key=f"rep_{i}")
        min_c, max_c = TIPOS_PAVIMENTO[tipo_i]
        if min_c == max_c:
            coef_i = c4.number_input(
                "", min_value=min_c, max_value=max_c,
                value=min_c, format="%0.2f",
                disabled=True, key=f"coef_{i}"
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
        total_i = area_i * rep_i
        c6.markdown(
            f"<div style='text-align:right;color:#333;font-weight:500'>{fmt_br(total_i)}</div>",
            unsafe_allow_html=True
        )
        constr_i = c7.checkbox("", value=True, key=f"constr_{i}")

        registros.append({
            "nome": nome_i,
            "tipo": tipo_i,
            "rep": rep_i,
            "coef": coef_i,
            "area": area_i,
            "area_total": total_i,
            "constr": constr_i
        })

    # — DataFrame e Download —
    df = pd.DataFrame(registros)
    df["area_eq"] = df["area"] * df["coef"] * df["rep"]
    df["custo"]   = df["area_eq"] * unit_cost

    st.markdown("### 📑 Detalhamento por Pavimento")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False, sep=";").encode("utf-8")
    st.download_button(
        "⬇️ Baixar CSV",
        data=csv,
        file_name="orcamento_parametrico.csv",
        mime="text/csv"
    )

    # — Resumo Final em destaque —
    st.markdown("---")
    st.markdown("## 💰 Resumo Final")

    total_eq   = df["area_eq"].sum()
    total_cust = df["custo"].sum()
    sc1, sc2 = st.columns(2)
    sc1.markdown(
        f"""
        <div style="
          background-color:#31708f;
          padding:15px;
          border-radius:6px;
          text-align:center;
        ">
          <div style="color:#fff;font-size:16px;">Área Equivalente Total</div>
          <div style="color:#fff;font-size:28px;font-weight:bold;">{fmt_br(total_eq)} m²</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    sc2.markdown(
        f"""
        <div style="
          background-color:#a94442;
          padding:15px;
          border-radius:6px;
          text-align:center;
        ">
          <div style="color:#fff;font-size:16px;">Custo Total do Projeto</div>
          <div style="color:#fff;font-size:28px;font-weight:bold;">
            R$ {fmt_br(total_cust)}
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # — Botão Excluir Projeto lá embaixo ——
    st.markdown("---")
    if st.button("🗑️ Excluir Projeto", help="Apaga o projeto atual e recarrega"):
        delete_project(info["id"])
        del st.session_state.projeto_info
        safe_rerun()


if __name__ == "__main__":
    main()
