    # … trecho acima permanece igual …

    # “Área Total Equivalente” (area_eq) e “Área Total Construída” (area_construida)
    df = pd.DataFrame(registros)
    df["area_eq"] = df["area"] * df["coef"] * df["rep"]
    df["area_construida"] = df["area_eq"].where(df["constr"], 0.0)
    df["custo"] = df["area_eq"] * unit_cost

    # Exibição refinada da tabela
    st.markdown("### 📑 Detalhamento por Pavimento")
    df_display = (
        df
        .rename(columns={
            "nome": "Nome",
            "tipo": "Tipo",
            "rep": "Rep.",
            "coef": "Coef.",
            "area": "Área (m²)",
            "area_eq": "Área Total Equivalente",
            "area_construida": "Área Total Construída",
            "custo": "Custo (R$)"
        })
        # Ordene/filtre as colunas que quer mostrar:
        [["Nome", "Tipo", "Rep.", "Coef.", "Área (m²)",
          "Área Total Equivalente", "Área Total Construída", "Custo (R$)"]]
    )
    st.dataframe(df_display, use_container_width=True)

    # Resumo abaixo da tabela: somatórios de Área Equivalente e Área Construída
    total_eq = df["area_eq"].sum()
    total_constr = df["area_construida"].sum()
    rc1, rc2 = st.columns(2)
    rc1.markdown(f"""
        <div style="background-color:#31708f;padding:12px;border-radius:6px;text-align:center;">
          <div style="color:#fff;font-size:14px;">Área Total Equivalente</div>
          <div style="color:#fff;font-size:24px;font-weight:bold;">{fmt_br(total_eq)} m²</div>
        </div>
    """, unsafe_allow_html=True)
    rc2.markdown(f"""
        <div style="background-color:#8a6d3b;padding:12px;border-radius:6px;text-align:center;">
          <div style="color:#fff;font-size:14px;">Área Total Construída</div>
          <div style="color:#fff;font-size:24px;font-weight:bold;">{fmt_br(total_constr)} m²</div>
        </div>
    """, unsafe_allow_html=True)

    # botão de download do CSV (continua incluindo a nova coluna)
    csv = df.to_csv(index=False, sep=";").encode("utf-8")
    st.download_button(
        "⬇️ Baixar CSV",
        data=csv,
        file_name="orcamento_parametrico.csv",
        mime="text/csv"
    )

    # … resumo final (fica abaixo, igual antes, mas ajustamos o terceiro cartão) …
    st.markdown("---")
    st.markdown("## 💰 Resumo Final")

    total_cust     = df["custo"].sum()
    priv_area      = info["area_privativa"] or 1.0
    razao_ac_pri   = total_constr / priv_area  # adimensional
    custo_por_ac   = total_cust / total_constr if total_constr > 0 else 0.0

    sc1, sc2, sc3, sc4 = st.columns(4)
    # Área Equivalente Total
    sc1.markdown(f"""
        <div style="background-color:#31708f;padding:15px;border-radius:6px;text-align:center;">
          <div style="color:#fff;font-size:16px;">Área Equivalente Total</div>
          <div style="color:#fff;font-size:28px;font-weight:bold;">{fmt_br(total_eq)} m²</div>
        </div>
    """, unsafe_allow_html=True)
    # Custo Total
    sc2.markdown(f"""
        <div style="background-color:#a94442;padding:15px;border-radius:6px;text-align:center;">
          <div style="color:#fff;font-size:16px;">Custo Total do Projeto</div>
          <div style="color:#fff;font-size:28px;font-weight:bold;">R$ {fmt_br(total_cust)}</div>
        </div>
    """, unsafe_allow_html=True)
    # A.C / A.Privativa (adimensional, sem %)
    sc3.markdown(f"""
        <div style="background-color:#8a6d3b;padding:15px;border-radius:6px;text-align:center;">
          <div style="color:#fff;font-size:16px;">A.C / A.Privativa</div>
          <div style="color:#fff;font-size:28px;font-weight:bold;">{razao_ac_pri:.2f}</div>
        </div>
    """, unsafe_allow_html=True)
    # Custo / m² A.C
    sc4.markdown(f"""
        <div style="background-color:#3c763d;padding:15px;border-radius:6px;text-align:center;">
          <div style="color:#fff;font-size:16px;">Custo / m² A.C</div>
          <div style="color:#fff;font-size:28px;font-weight:bold;">R$ {fmt_br(custo_por_ac)}</div>
        </div>
    """, unsafe_allow_html=True)

    # … restante (botão de excluir etc.) continua igual …
