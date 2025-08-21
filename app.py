import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# === Configurações do Banco de Dados ===
DB_PATH = "projects.db"

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            area_terreno REAL,
            endereco TEXT,
            area_privativa REAL,
            num_unidades INTEGER,
            created_at TEXT
        )
    """)
    db.commit()

def save_project(info: dict) -> int:
    db = get_db()
    now = datetime.utcnow().isoformat()
    if info.get("id"):
        # Atualiza projeto existente
        db.execute("""
            UPDATE projects
            SET nome=?, area_terreno=?, endereco=?, area_privativa=?, num_unidades=?
            WHERE id=?
        """, (
            info["nome"],
            info["area_terreno"],
            info["endereco"],
            info["area_privativa"],
            info["num_unidades"],
            info["id"],
        ))
        pid = info["id"]
    else:
        # Insere novo projeto
        cursor = db.execute("""
            INSERT INTO projects (
                nome, area_terreno, endereco, area_privativa, num_unidades, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            info["nome"],
            info["area_terreno"],
            info["endereco"],
            info["area_privativa"],
            info["num_unidades"],
            now,
        ))
        pid = cursor.lastrowid
    db.commit()
    return pid

def list_projects() -> list:
    db = get_db()
    rows = db.execute("""
        SELECT id, nome, created_at
        FROM projects
        ORDER BY created_at DESC
    """).fetchall()
    return [dict(r) for r in rows]

def load_project(pid: int) -> dict:
    db = get_db()
    row = db.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    return dict(row) if row else None


# === Dicionário de Tipos de Pavimento + Coeficientes (NBR 12721) ===
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
    # Inicializa o DB e configura a página
    init_db()
    st.set_page_config(page_title="Orçamento Paramétrico", layout="wide")

    # === TELA INICIAL: Carregar ou Criar Projeto ===
    if "projeto_info" not in st.session_state:
        st.title("🏢 Orçamento Paramétrico de Edifícios Residenciais")
        col1, col2 = st.columns(2)

        # Lista de projetos existentes
        projetos = list_projects()
        options = ["— Novo Projeto —"] + [f"{p['id']}: {p['nome']}" for p in projetos]
        sel = st.selectbox("Carregar Projeto Existente", options)

        if sel != "— Novo Projeto —":
            pid = int(sel.split(":")[0])
            info = load_project(pid)
            info["id"] = pid
            st.session_state.projeto_info = info
            st.experimental_rerun()

        # Campos para novo projeto
        with col1:
            nome = st.text_input("Nome do Projeto")
            area_terreno = st.number_input(
                "Área do Terreno (m²)", min_value=0.0, format="%.2f"
            )
            endereco = st.text_area("Endereço")
        with col2:
            area_privativa = st.number_input(
                "Área Total Privativa (m²)", min_value=0.0, format="%.2f"
            )
            num_unidades = st.number_input(
                "Número de Unidades", min_value=1, step=1
            )

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
        return  # mantém nesta tela até criar/carregar

    # === TELA PRINCIPAL DE ORÇAMENTO ===
    info = st.session_state.projeto_info

    # Botão para excluir projeto
    with st.sidebar:
        st.header("Projeto")
        st.write(f"**{info['nome']}**")
        if info.get("id"):
            if st.button("🗑️ Excluir Projeto"):
                db = get_db()
                db.execute("DELETE FROM projects WHERE id=?", (info["id"],))
                db.commit()
                del st.session_state.projeto_info
                st.success("Projeto excluído.")
                st.experimental_rerun()

    # Cabeçalho e informações básicas
    st.title("🏢 Orçamento Paramétrico de Edifícios Residenciais")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"Nome: {info['nome']}")
        st.info(f"Endereço: {info['endereco']}")
    with col2:
        st.info(f"Área do Terreno: {info['area_terreno']:,.2f} m²")
        st.info(f"Área Privativa: {info['area_privativa']:,.2f} m²")
    with col3:
        st.info(f"Nº Unidades: {info['num_unidades']}")

    # Parâmetros de cálculo na sidebar
    st.sidebar.header("⚙️ Parâmetros de Cálculo")
    unit_cost = st.sidebar.number_input(
        "Custo de Área Privativa (R$/m²)",
        min_value=0.0,
        value=4500.0,
        step=100.0,
        format="%.2f",
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2025 Sua Empresa")

    # Dados dos pavimentos
    n = st.number_input(
        "Número de Pavimentos", min_value=1, max_value=50, value=1, step=1
    )
    st.markdown("### 🏢 Dados dos Pavimentos")

    # Cabeçalho da tabela
    cols = st.columns([1.3, 2.5, 0.5, 1, 1, 1, 0.7])
    headers = ["Nome", "Tipo de Pavimento", "Rep.", "Coef.", "Área (m²)", "Área Total", "Constr."]
    for col, head in zip(cols, headers):
        col.markdown(f"**{head}**")

    # Coleta de dados
    nomes, tipos, reps, coefs, areas, areas_total, constr = [], [], [], [], [], [], []
    for i in range(1, n + 1):
        c1, c2, c3, c4, c5, c6, c7 = st.columns([1.3, 2.5, 0.5, 1, 1, 1, 0.7])
        nome_i = c1.text_input("", value=f"Pavimento {i}", key=f"nome_{i}")
        tipo_i = c2.selectbox("", list(TIPOS_PAVIMENTO.keys()), key=f"tipo_{i}")
        rep_i = c3.number_input("", value=1, min_value=1, step=1, key=f"rep_{i}")

        min_c, max_c = TIPOS_PAVIMENTO[tipo_i]
        if min_c == max_c:
            coef_i = c4.number_input(
                "", value=min_c, format="%.2f", disabled=True, key=f"coef_{i}"
            )
        else:
            coef_i = c4.slider(
                "", min_value=min_c, max_value=max_c,
                value=(min_c + max_c) / 2, step=0.01,
                format="%.2f", key=f"coef_{i}"
            )

        area_i = c5.number_input(
            "", value=100.0, min_value=0.0, step=1.0,
            format="%.2f", key=f"area_{i}"
        )

        area_total_i = area_i * rep_i
        c6.markdown(
            f"<p style='text-align: right;'>{area_total_i:,.2f}</p>",
            unsafe_allow_html=True
        )

        constr_i = c7.checkbox("", value=True, key=f"constr_{i}")

        nomes.append(nome_i)
        tipos.append(tipo_i)
        reps.append(rep_i)
        coefs.append(coef_i)
        areas.append(area_i)
        areas_total.append(area_total_i)
        constr.append(constr_i)

    # Monta DataFrame e cálculos
    df = pd.DataFrame({
        "Nome do Pavimento": nomes,
        "Tipo de Pavimento": tipos,
        "Repetição": reps,
        "Coeficiente": coefs,
        "Área (m²)": areas,
        "Área Total (m²)": areas_total,
        "Área Construída": constr,
    })
    df["Área Equivalente (m²)"] = df["Área (m²)"] * df["Coeficiente"] * df["Repetição"]
    df["Custo do Pavimento (R$)"] = df["Área Equivalente (m²)"] * unit_cost

    # Somatório de área construída
    soma_area_total = df[df["Área Construída"]]["Área Total (m²)"].sum()
    st.markdown(
        f"<h4 style='text-align: right;'>"
        f"Somatório de Área Total Construída: {soma_area_total:,.2f} m²"
        f"</h4>",
        unsafe_allow_html=True
    )

    # Resumo do orçamento
    total_eq = df["Área Equivalente (m²)"].sum()
    total_custo = df["Custo do Pavimento (R$)"].sum()

    st.markdown("## 💰 Resumo do Orçamento", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.success(f"Área Equivalente Total: {total_eq:,.2f} m²")
    with c2:
        st.success(f"Custo Total do Projeto: R$ {total_custo:,.2f}")

    # Detalhamento e download
    st.markdown("### 📑 Detalhamento por Pavimento")
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Baixar Detalhamento (CSV)",
        data=csv,
        file_name="orcamento_parametrico.csv",
        mime="text/csv",
    )

if __name__ == "__main__":
    main()
