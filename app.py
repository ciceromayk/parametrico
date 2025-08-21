import streamlit as st
import pandas as pd

# (Mantive o dicionário de tipos de pavimento igual ao anterior)
TIPOS_PAVIMENTO = {
    "Garagem (Subsolo)":              (0.50, 0.75),
    # ... (demais tipos mantidos)
}

def main():
    st.set_page_config(page_title="Orçamento Paramétrico", layout="wide")

    # (Mantive a lógica inicial de projeto igual)
    if "projeto_info" not in st.session_state:
        # ... (código da tela inicial mantido)

    else:
        info = st.session_state.projeto_info
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

        # --- Dados dos Pavimentos ---
        n = info["num_pavimentos"]
        st.markdown("### 🏢 Dados dos Pavimentos")

        # Cabeçalho com colunas ajustadas
        h1, h2, h3, h4, h5, h6 = st.columns([1, 2, 0.5, 1, 1, 1])
        h1.markdown("**Nome**")
        h2.markdown("**Tipo de Pavimento**")
        h3.markdown("**Rep.**")
        h4.markdown("**Coef.**")
        h5.markdown("**Área (m²)**")
        h6.markdown("**Área Total**")

        nomes, tipos, reps, coefs, areas, areas_total = [], [], [], [], [], []

        for i in range(1, n + 1):
            c1, c2, c3, c4, c5, c6 = st.columns([1, 2, 0.5, 1, 1, 1])

            # 1) Nome do Pavimento
            nome = c1.text_input("", value=f"Pav {i}", key=f"nome_{i}")

            # 2) Tipo de pavimento
            tipo = c2.selectbox(
                "", options=list(TIPOS_PAVIMENTO.keys()), key=f"tipo_{i}"
            )

            # 3) Repetição (coluna mais estreita)
            rep = c3.number_input(
                "", value=1, min_value=1, step=1, key=f"rep_{i}"
            )

            # 4) Coeficiente
            min_c, max_c = TIPOS_PAVIMENTO[tipo]
            if min_c == max_c:
                coef = c4.number_input(
                    "", value=min_c, format="%.2f", disabled=True, key=f"coef_{i}"
                )
            else:
                coef = c4.slider(
                    "", min_value=min_c, max_value=max_c,
                    value=(min_c + max_c) / 2, step=0.01,
                    format="%.2f", key=f"coef_{i}"
                )

            # 5) Área
            area = c5.number_input(
                "", value=100.0, min_value=0.0, step=1.0,
                format="%.2f", key=f"area_{i}"
            )

            # 6) Área Total (área x repetição)
            area_total = area * rep
            c6.markdown(f"**{area_total:,.2f}**")

            # Armazena dados
            nomes.append(nome)
            tipos.append(tipo)
            reps.append(rep)
            coefs.append(coef)
            areas.append(area)
            areas_total.append(area_total)

        # Monta DataFrame
        df = pd.DataFrame({
            "Nome do Pavimento": nomes,
            "Tipo de Pavimento": tipos,
            "Repetição": reps,
            "Coeficiente": coefs,
            "Área (m²)": areas,
            "Área Total (m²)": areas_total
        })

        # Cálculo de Área Equivalente
        df["Área Equivalente (m²)"] = (
            df["Área (m²)"] * df["Coeficiente"] * df["Repetição"]
        )
        df["Custo do Pavimento (R$)"] = df["Área Equivalente (m²)"] * unit_cost

        # Somatórios
        total_area = df["Área Total (m²)"].sum()
        total_equiv = df["Área Equivalente (m²)"].sum()
        total_custo = df["Custo do Pavimento (R$)"].sum()

        # Resultados
        st.markdown("## 📊 Resultados")
        st.write(f"- **Área total:** {total_area:,.2f} m²")
        st.write(f"- **Área equivalente total:** {total_equiv:,.2f} m²")
        st.write(f"- **Orçamento estimado:** R$ {total_custo:,.2f}")

        # Detalhamento
        st.markdown("### 📋 Detalhamento por Pavimento")
        st.dataframe(df, use_container_width=True)

        # Botão CSV
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar Detalhamento (CSV)",
            data=csv,
            file_name="orcamento_parametrico.csv",
            mime="text/csv",
        )

if __name__ == "__main__":
    main()
