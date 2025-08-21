import streamlit as st
import pandas as pd

# -------------------------------------------------------------------
# Dicionário de tipos de pavimento + intervalo de coeficientes
# (conforme NBR 12721 – item 5.7.3)
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

    # === TELA INICIAL ===
    if "projeto_info" not in st.session_state:
        st.title("📐 Orçamento Paramétrico de Edifícios Residenciais")
        st.markdown("## Informações do Projeto")
        nome        = st.text_input("Nome do Projeto")
        area_terreno= st.number_input("Área do Terreno (m²)", min_value=0.0, format="%.2f")
        endereco    = st.text_area("Endereço")
        num_pav     = st.number_input(
            "Número de Pavimentos", min_value=1, max_value=50, value=1, step=1
        )

        if st.button("✅ Salvar Projeto"):
            st.session_state.projeto_info = {
                "nome": nome,
                "area_terreno": area_terreno,
                "endereco": endereco,
                "num_pavimentos": int(num_pav),
            }
            st.experimental_rerun()

    # === TELA DE ORÇAMENTO ===
    else:
        info = st.session_state.projeto_info

        # Cabeçalho e info do projeto
        st.title("📐 Orçamento Paramétrico de Edifícios Residenciais")
        st.header("🔍 Informações do Projeto")
        st.write(f"**Nome:** {info['nome']}")
        st.write(f"**Área do Terreno:** {info['area_terreno']:,.2f} m²")
        st.write(f"**Endereço:** {info['endereco']}")
        st.write(f"**Pavimentos:** {info['num_pavimentos']}")

        # Sidebar: custo
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

        # Entrada de dados dos pavimentos
        n = info["num_pavimentos"]
        st.markdown("### 🏢 Dados dos Pavimentos")

        # Cabeçalho da tabela
        col_nome, col_tipo, col_rep, col_coef, col_area, col_at = st.columns(
            [1.5, 3, 0.6, 1, 1, 1]
        )
        col_nome.markdown("**Nome**")
        col_tipo.markdown("**Tipo de Pavimento**")
        col_rep.markdown("**Rep.**")
        col_coef.markdown("**Coef.**")
        col_area.markdown("**Área (m²)**")
        col_at.markdown("**Área Total**")

        nomes, tipos, reps, coefs, areas, areas_total = [], [], [], [], [], []

        for i in range(1, n+1):
            c1, c2, c3, c4, c5, c6 = st.columns([1.5, 3, 0.6, 1, 1, 1])

            # 1) Nome do Pavimento
            nome_i = c1.text_input("", value=f"Pavimento {i}", key=f"nome_{i}")

            # 2) Tipo de Pavimento
            tipo_i = c2.selectbox("", list(TIPOS_PAVIMENTO.keys()), key=f"tipo_{i}")

            # 3) Repetição
            rep_i = c3.number_input("", value=1, min_value=1, step=1, key=f"rep_{i}")

            # 4) Coeficiente
            min_c, max_c = TIPOS_PAVIMENTO[tipo_i]
            if min_c == max_c:
                coef_i = c4.number_input(
                    "", value=min_c, format="%.2f", disabled=True, key=f"coef_{i}"
                )
            else:
                coef_i = c4.slider(
                    "", min_value=min_c, max_value=max_c,
                    value=(min_c+max_c)/2, step=0.01,
                    format="%.2f", key=f"coef_{i}"
                )

            # 5) Área
            area_i = c5.number_input(
                "", value=100.0, min_value=0.0, step=1.0,
                format="%.2f", key=f"area_{i}"
            )

            # 6) Área Total
            area_total_i = area_i * rep_i
            c6.markdown(f"**{area_total_i:,.2f}**")

            nomes.append(nome_i)
            tipos.append(tipo_i)
            reps.append(rep_i)
            coefs.append(coef_i)
            areas.append(area_i)
            areas_total.append(area_total_i)

        # Somatório de área total (após inputs)
        soma_area_total = sum(areas_total)
        st.markdown(f"**Somatório de Área Total:** {soma_area_total:,.2f} m²")

        # Monta DataFrame final
        df = pd.DataFrame({
            "Nome do Pavimento": nomes,
            "Tipo de Pavimento": tipos,
            "Repetição": reps,
            "Coeficiente": coefs,
            "Área (m²)": areas,
            "Área Total (m²)": areas_total
        })
        df["Área Equivalente (m²)"] = (
            df["Área (m²)"] * df["Coeficiente"] * df["Repetição"]
        )
        df["Custo do Pavimento (R$)"] = df["Área Equivalente (m²)"] * unit_cost

        # Cálculos agregados
        total_eq = df["Área Equivalente (m²)"].sum()
        total_custo = df["Custo do Pavimento (R$)"].sum()

        # Resultados
        st.markdown("## 📊 Resultados")
        st.write(f"- **Área equivalente total:** {total_eq:,.2f} m²")
        st.write(f"- **Orçamento estimado:** R$ {total_custo:,.2f}")

        # Detalhamento
        st.markdown("### 📋 Detalhamento por Pavimento")
        st.dataframe(df, use_container_width=True)

        # Download CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar Detalhamento (CSV)",
            data=csv,
            file_name="orcamento_parametrico.csv",
            mime="text/csv",
        )

if __name__ == "__main__":
    main()
