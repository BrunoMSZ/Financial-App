from datetime import date, datetime
import time
import extra_streamlit_components as stx
import pandas as pd
import plotly.express as px
import requests
import os
import streamlit as st

st.set_page_config(
    page_title="Finanças Pessoais",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "https://financial-app-g2ja.onrender.com"

CATEGORIES_MAP = {
    "Alimentação": [
        "Supermercado",
        "Restaurante",
        "Delivery / iFood",
        "Lanches & Cafés",
    ],
    "Moradia": [
        "Aluguel / Condomínio",
        "Energia Elétrica",
        "Água & Gás",
        "Internet & TV",
        "Manutenção",
    ],
    "Transporte": [
        "Combustível",
        "Uber / Táxi",
        "Transporte Público",
        "Manutenção / IPVA",
    ],
    "Lazer": ["Viagens", "Streaming", "Cinema / Shows", "Hobbies & Jogos"],
    "Saúde": [
        "Farmácia",
        "Consultas & Exames",
        "Plano de Saúde",
        "Academia / Esporte",
    ],
    "Educação": ["Cursos & Treinamentos", "Livros", "Faculdade / Escola"],
    "Renda / Entradas": [
        "Salário",
        "Vale Refeição (VR)",
        "Vale Alimentação (VA)",
        "Vale Transporte (VT)",
        "Freelance",
        "Rendimentos / Dividendos",
        "Outros Ganhos",
    ],
    "Outros": ["Diversos / Inesperados"],
}

PAYMENT_METHODS = [
    "PIX",
    "Cartão de Crédito",
    "Cartão de Débito",
    "Dinheiro",
    "Boleto Bancário",
    "Transferência (TED/DOC)",
]

# --- COOKIE MANAGER ---
cookie_manager = stx.CookieManager(key="cookie_manager")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0e1117;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* --- SIDEBAR SMOOTH STYLE --- */
    section[data-testid="stSidebar"] {
        background-color: #1a1d24 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Esconde a label principal do Radio */
    div[data-testid="stSidebar"] div[data-testid="stRadio"] > label {
        display: none;
    }
    
    /* REMOVE A BOLINHA VERMELHA / CIRCULO DO RADIO BUTTON */
    div[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }
    
    div[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 6px;
    }
    
    /* Estilo dos Botões do Menu Lateral */
    div[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label {
        background-color: transparent;
        color: #8b92a5 !important;
        border-radius: 10px;
        padding: 12px 18px;
        font-weight: 500;
        transition: all 0.25s ease-in-out;
        cursor: pointer;
        border-left: 4px solid transparent;
        display: flex;
        align-items: center;
        margin-bottom: 2px;
        width: 100%;
    }
    
    div[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background-color: #262a36;
        color: #ffffff !important;
    }
    
    /* Item Selecionado (Ativo) Estilo Dashboard Smooth */
    div[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(90deg, #0073aa 0%, #005177 100%) !important;
        color: #ffffff !important;
        border-left: 4px solid #00a0d2;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0, 115, 170, 0.3);
    }
    
    /* Cards de Métricas */
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(4px);
        margin-bottom: 15px;
    }
    .metric-title {
        color: #8b92a5;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 5px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

if "autenticado" not in st.session_state:
  st.session_state.autenticado = False
  st.session_state.id_user = None
  st.session_state.nome_user = ""

if "ocultar_valores" not in st.session_state:
  st.session_state["ocultar_valores"] = False


def format_curr(valor: float) -> str:
  """Formata valores respeitando o estado de privacidade."""
  if st.session_state.get("ocultar_valores", False):
    return "R$ •••••"
  return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


user_cookie = cookie_manager.get(cookie="financial_app_user")
if user_cookie and not st.session_state.autenticado:
  try:
    dados_c = (
        user_cookie
        if isinstance(user_cookie, dict)
        else eval(str(user_cookie))
    )
    u_id = dados_c.get("id")

    res_verify = requests.get(f"{API_URL}/users/verify/{u_id}")
    if res_verify.status_code == 200:
      st.session_state.autenticado = True
      st.session_state.id_user = u_id
      st.session_state.nome_user = res_verify.json().get("nome")
    else:
      cookie_manager.delete("financial_app_user")
      st.session_state.autenticado = False
      st.session_state.id_user = None
  except Exception:
    cookie_manager.delete("financial_app_user")
    st.session_state.autenticado = False
    st.session_state.id_user = None

# --- LOGIN SCREEN ---
if not st.session_state.autenticado:
  st.markdown(
      "<h1 style='text-align: center; color: #0073aa;'>💳 Finanças"
      " Pessoais</h1>",
      unsafe_allow_html=True,
  )
  _, login_container, _ = st.columns([1, 2, 1])

  with login_container:
    aba_login, aba_cadastro = st.tabs(["🔑 Entrar", "✨ Criar Conta"])

    with aba_login:
      with st.form("form_login"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        lembrar = st.checkbox("Lembrar de mim por 1 dia", value=True)
        btn_login = st.form_submit_button("Entrar", use_container_width=True)

        if btn_login:
          res = requests.post(
              f"{API_URL}/login", json={"email": email, "senha": senha}
          )
          if res.status_code == 200:
            user = res.json()
            st.session_state.autenticado = True
            st.session_state.id_user = user["id"]
            st.session_state.nome_user = user["nome"]

            if lembrar:
              cookie_manager.set(
                  "financial_app_user",
                  {"id": user["id"], "nome": user["nome"]},
                  max_age=86400,
              )

            st.toast(
                f"Bem-vindo(a) de volta, {user['nome']}! 🎉", icon="✅"
            )
            time.sleep(0.5)
            st.rerun()
          else:
            st.error("Credenciais inválidas. Verifique seu e-mail e senha.")

    with aba_cadastro:
      with st.form("form_cadastro"):
        nome = st.text_input("Nome Completo")
        email_cad = st.text_input("E-mail para cadastro")
        senha_cad = st.text_input("Senha", type="password")
        btn_cad = st.form_submit_button("Cadastrar", use_container_width=True)

        if btn_cad:
          res = requests.post(
              f"{API_URL}/users",
              json={"nome": nome, "email": email_cad, "senha": senha_cad},
          )
          if res.status_code in [200, 201]:
            st.toast("Conta criada com sucesso!", icon="🚀")
            st.success("Conta criada! Faça login para continuar.")
          else:
            st.error(res.json().get("detail", "Erro ao realizar cadastro."))

  st.stop()

st.sidebar.markdown(f"### 👤 **{st.session_state.nome_user}**")

st.sidebar.toggle("👁️ Ocultar Valores", key="ocultar_valores")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegação",
    ["📊 Dashboard", "💸 Transações", "📈 Investimentos", "🎯 Definir Orçamento"],
    key="nav_menu",
)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Sair", use_container_width=True):
  cookie_manager.delete("financial_app_user")
  st.session_state.autenticado = False
  st.session_state.id_user = None
  st.toast("Sessão encerrada.", icon="👋")
  time.sleep(0.5)
  st.rerun()


def load_transactions():
  res = requests.get(f"{API_URL}/transactions/{st.session_state.id_user}")
  if res.status_code == 200 and res.json():
    df = pd.DataFrame(res.json())
    df["data"] = pd.to_datetime(df["data"]).dt.strftime("%Y-%m-%d")
    return df
  return pd.DataFrame()


def load_investments():
  res = requests.get(f"{API_URL}/investments/{st.session_state.id_user}")
  if res.status_code == 200 and res.json():
    return pd.DataFrame(res.json())
  return pd.DataFrame()



if menu == "📊 Dashboard":
  st.title("📊 Painel Financeiro")

  df_trans = load_transactions()
  df_inv = load_investments()

  entradas = (
      df_trans[
          df_trans["tipo"].astype(str).str.lower().isin(["entrada", "ganho"])
      ]["valor"].sum()
      if not df_trans.empty
      else 0.0
  )
  saidas = (
      df_trans[
          df_trans["tipo"].astype(str).str.lower().isin(["saida", "saída"])
      ]["valor"].sum()
      if not df_trans.empty
      else 0.0
  )
  patrimonio_inv = df_inv["valor_total"].sum() if not df_inv.empty else 0.0
  saldo_atual = entradas - saidas

  col1, col2, col3, col4 = st.columns(4)

  with col1:
    st.markdown(
        f'<div class="metric-card"><div class="metric-title">Entradas</div><div'
        ' class="metric-value"'
        f' style="color:#4CAF50;">{format_curr(entradas)}</div></div>',
        unsafe_allow_html=True,
    )
  with col2:
    st.markdown(
        f'<div class="metric-card"><div class="metric-title">Saídas</div><div'
        ' class="metric-value"'
        f' style="color:#FF5252;">{format_curr(saidas)}</div></div>',
        unsafe_allow_html=True,
    )
  with col3:
    st.markdown(
        '<div class="metric-card"><div class="metric-title">Saldo em'
        ' Conta</div><div class="metric-value"'
        f' style="color:#2196F3;">{format_curr(saldo_atual)}</div></div>',
        unsafe_allow_html=True,
    )
  with col4:
    st.markdown(
        '<div class="metric-card"><div'
        ' class="metric-title">Investimentos</div><div class="metric-value"'
        f' style="color:#FFD700;">{format_curr(patrimonio_inv)}</div></div>',
        unsafe_allow_html=True,
    )

  st.divider()

  col_g1, col_g2 = st.columns(2)

  with col_g1:
    st.subheader("Gastos por Categoria💸")
    if (
        not df_trans.empty
        and not df_trans[
            df_trans["tipo"].astype(str).str.lower().isin(["saida", "saída"])
        ].empty
    ):
      df_saidas = df_trans[
          df_trans["tipo"].astype(str).str.lower().isin(["saida", "saída"])
      ]
      fig_cat = px.pie(
          df_saidas,
          values="valor",
          names="categoria",
          hole=0.4,
          color_discrete_sequence=px.colors.qualitative.Set3,
      )
      st.plotly_chart(fig_cat, use_container_width=True)
    else:
      st.info("Nenhum gasto registrado ainda.")

  with col_g2:
    st.subheader("📈 Diversificação de Investimentos")
    if not df_inv.empty:
      df_inv_grouped = (
          df_inv.groupby("classe")["valor_total"].sum().reset_index()
      )
      fig_inv = px.pie(
          df_inv_grouped,
          values="valor_total",
          names="classe",
          hole=0.4,
          color_discrete_sequence=px.colors.qualitative.Pastel,
      )
      st.plotly_chart(fig_inv, use_container_width=True)
    else:
      st.info("Nenhum investimento registrado na carteira.")

  st.divider()

  col_rec1, col_rec2 = st.columns(2)

  with col_rec1:
    st.subheader("🕒 Últimas Saídas Registradas")
    if (
        not df_trans.empty
        and not df_trans[
            df_trans["tipo"].astype(str).str.lower().isin(["saida", "saída"])
        ].empty
    ):
      df_rec_saidas = (
          df_trans[
              df_trans["tipo"].astype(str).str.lower().isin(["saida", "saída"])
          ]
          .head(5)[
              [
                  "data",
                  "categoria",
                  "sub_categoria",
                  "valor",
                  "metodo_pagamento",
              ]
          ]
          .copy()
      )

      if st.session_state.get("ocultar_valores", False):
        df_rec_saidas["valor"] = "R$ •••••"
      else:
        df_rec_saidas["valor"] = df_rec_saidas["valor"].apply(
            lambda x: f"R$ {x:,.2f}"
        )
      st.dataframe(df_rec_saidas, use_container_width=True, hide_index=True)
    else:
      st.info("Sem movimentações de saída recentes.")

  with col_rec2:
    st.subheader("🚀 Últimos Aportes / Investimentos")
    if not df_inv.empty:
      df_rec_inv = (
          df_inv.head(5)[
              ["data", "ativo", "classe", "quantidade", "valor_total"]
          ]
          .copy()
      )

      if st.session_state.get("ocultar_valores", False):
        df_rec_inv["valor_total"] = "R$ •••••"
      else:
        df_rec_inv["valor_total"] = df_rec_inv["valor_total"].apply(
            lambda x: f"R$ {x:,.2f}"
        )
      st.dataframe(df_rec_inv, use_container_width=True, hide_index=True)
    else:
      st.info("Sem investimentos recentes.")


elif menu == "💸 Transações":
  st.title("💸 Gestão de Transações")

  aba_add, aba_gerenciar = st.tabs(["➕ Nova Transação", "✏️ Editar / Excluir"])

  with aba_add:
    st.markdown("##### Preencha os dados da nova transação:")

    col_a, col_b = st.columns(2)
    with col_a:
      tipo_t = st.selectbox("Tipo de Transação", ["Saída", "Entrada"])
      cat_t = st.selectbox("Categoria", list(CATEGORIES_MAP.keys()))
      subcats_disponiveis = CATEGORIES_MAP.get(cat_t, ["Geral"])
      subcat_t = st.selectbox("Subcategoria", subcats_disponiveis)

    with col_b:
      metodo_t = st.selectbox("Método de Pagamento", PAYMENT_METHODS)
      data_t = st.date_input("Data da Operação", date.today())

    st.markdown("---")
    with st.form("form_nova_transacao_valores"):
      col_val1, col_val2 = st.columns(2)
      with col_val1:
        valor_t = st.number_input(
            "Valor (R$)", min_value=0.01, step=5.0, format="%.2f"
        )
      with col_val2:
        desc_t = st.text_input(
            "Descrição / Observação",
            placeholder="Ex: Salário, VR, VA, VT, etc.",
        )

      btn_salvar = st.form_submit_button(
          "💾 Confirmar & Salvar Transação", use_container_width=True
      )

      if btn_salvar:
        payload = {
            "id_user": st.session_state.id_user,
            "data": str(data_t),
            "tipo": tipo_t,
            "valor": valor_t,
            "categoria": cat_t,
            "sub_categoria": subcat_t,
            "metodo_pagamento": metodo_t,
            "descricao": desc_t,
        }
        res = requests.post(f"{API_URL}/transactions/", json=payload)
        if res.status_code == 201:
          st.toast("Transação registrada com sucesso! 💸", icon="✅")
          st.success("Transação registrada!")
          time.sleep(0.8)
          st.rerun()
        else:
          st.error("Não foi possível salvar a transação.")

  with aba_gerenciar:
    df_trans = load_transactions()
    if not df_trans.empty:
      df_exibicao = df_trans.drop(columns=["id_user"], errors="ignore").copy()

      opcoes_trans = {
          f"{row['data']} | {row['tipo']} | {row['categoria']} | R$"
          f" {row['valor']:.2f}": row["id"]
          for _, row in df_trans.iterrows()
      }

      selecionado = st.selectbox(
          "Escolha a transação para editar/excluir:", list(opcoes_trans.keys())
      )
      trans_id = opcoes_trans[selecionado]
      registro_atual = df_trans[df_trans["id"] == trans_id].iloc[0]

      cat_index = (
          list(CATEGORIES_MAP.keys()).index(registro_atual["categoria"])
          if registro_atual["categoria"] in CATEGORIES_MAP
          else 0
      )
      metodo_index = (
          PAYMENT_METHODS.index(registro_atual.get("metodo_pagamento", "PIX"))
          if registro_atual.get("metodo_pagamento") in PAYMENT_METHODS
          else 0
      )

      col_e1, col_e2 = st.columns(2)
      with col_e1:
        edit_tipo = st.selectbox(
            "Tipo",
            ["Saída", "Entrada"],
            index=0 if registro_atual["tipo"].lower() == "saída" else 1,
            key="edit_tipo",
        )
        edit_cat = st.selectbox(
            "Categoria",
            list(CATEGORIES_MAP.keys()),
            index=cat_index,
            key="edit_cat",
        )
        subcats_edit = CATEGORIES_MAP.get(edit_cat, ["Geral"])
        edit_subcat = st.selectbox(
            "Subcategoria", subcats_edit, key="edit_subcat"
        )
      with col_e2:
        edit_metodo = st.selectbox(
            "Método de Pagamento",
            PAYMENT_METHODS,
            index=metodo_index,
            key="edit_metodo",
        )
        edit_data = st.date_input(
            "Data",
            datetime.strptime(registro_atual["data"], "%Y-%m-%d"),
            key="edit_data",
        )

      with st.form("form_editar_transacao"):
        col_ev1, col_ev2 = st.columns(2)
        with col_ev1:
          edit_valor = st.number_input(
              "Valor (R$)",
              value=float(registro_atual["valor"]),
              format="%.2f",
          )
        with col_ev2:
          edit_desc = st.text_input(
              "Descrição", value=str(registro_atual.get("descricao", ""))
          )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
          btn_atualizar = st.form_submit_button(
              "✏️ Atualizar Transação", use_container_width=True
          )
        with col_btn2:
          btn_deletar = st.form_submit_button(
              "🗑️ Excluir Transação", use_container_width=True
          )

        if btn_atualizar:
          payload = {
              "id_user": st.session_state.id_user,
              "data": str(edit_data),
              "tipo": edit_tipo,
              "valor": edit_valor,
              "categoria": edit_cat,
              "sub_categoria": edit_subcat,
              "metodo_pagamento": edit_metodo,
              "descricao": edit_desc,
          }
          res = requests.put(
              f"{API_URL}/transactions/{trans_id}", json=payload
          )
          if res.status_code == 200:
            st.toast("Transação atualizada!", icon="✏️")
            time.sleep(0.8)
            st.rerun()

        if btn_deletar:
          res = requests.delete(f"{API_URL}/transactions/{trans_id}")
          if res.status_code == 200:
            st.toast("Transação excluída!", icon="🗑️")
            time.sleep(0.8)
            st.rerun()

      st.divider()
      if st.session_state.get("ocultar_valores", False):
        df_exibicao["valor"] = "R$ •••••"
      st.dataframe(
          df_exibicao.drop(columns=["id"], errors="ignore"),
          use_container_width=True,
      )
    else:
      st.info("Nenhuma transação encontrada no sistema.")


elif menu == "📈 Investimentos":
  st.title("📈 Carteira de Investimentos")

  aba_add_inv, aba_ger_inv = st.tabs(["➕ Novo Ativo", "✏️ Editar / Excluir"])
  CLASSES_INVESTIMENTO = ["Ações", "FIIs", "Renda Fixa", "Cripto", "ETFs"]

  with aba_add_inv:
    col_i1, col_i2 = st.columns(2)
    with col_i1:
      classe_i = st.selectbox("Classe do Ativo", CLASSES_INVESTIMENTO)
    with col_i2:
      data_inv = st.date_input("Data de Aporte", date.today())

    with st.form("form_novo_inv"):
      col_if1, col_if2 = st.columns(2)
      with col_if1:
        ativo_i = st.text_input("Código / Ticker do Ativo (ex: ITUB4, HGLG11)")
        qtd_i = st.number_input(
            "Quantidade", min_value=0.0001, value=1.0, step=1.0, format="%.4f"
        )
      with col_if2:
        valor_i = st.number_input(
            "Preço Unitário (R$)", min_value=0.01, value=10.0, format="%.2f"
        )

      btn_salvar_inv = st.form_submit_button(
          "💾 Adicionar à Carteira", use_container_width=True
      )

      if btn_salvar_inv:
        if not ativo_i:
          st.error("Informe o código/nome do ativo.")
        else:
          payload = {
              "id_user": st.session_state.id_user,
              "data": str(data_inv),
              "ativo": ativo_i.upper(),
              "classe": classe_i,
              "quantidade": qtd_i,
              "valor": valor_i,
              "valor_total": qtd_i * valor_i,
          }
          res = requests.post(f"{API_URL}/investments/", json=payload)
          if res.status_code == 201:
            st.toast("Ativo adicionado! 📈", icon="💰")
            time.sleep(0.8)
            st.rerun()

  with aba_ger_inv:
    df_inv = load_investments()
    if not df_inv.empty:
      df_inv_exib = df_inv.copy()
      opcoes_inv = {
          f"{row['ativo']} ({row['classe']}) - Qtd: {row['quantidade']} | Total:"
          f" R$ {row['valor_total']:.2f}": row["id"]
          for _, row in df_inv.iterrows()
      }

      selecionado_inv = st.selectbox(
          "Selecione o Ativo:", list(opcoes_inv.keys())
      )
      inv_id = opcoes_inv[selecionado_inv]
      inv_atual = df_inv[df_inv["id"] == inv_id].iloc[0]

      classe_idx = (
          CLASSES_INVESTIMENTO.index(inv_atual["classe"])
          if inv_atual["classe"] in CLASSES_INVESTIMENTO
          else 0
      )
      e_classe = st.selectbox(
          "Classe do Ativo",
          CLASSES_INVESTIMENTO,
          index=classe_idx,
          key="edit_classe_inv",
      )

      with st.form("form_editar_inv"):
        col_ie1, col_ie2 = st.columns(2)
        with col_ie1:
          e_ativo = st.text_input("Ativo / Ticker", value=inv_atual["ativo"])
          e_qtd = st.number_input(
              "Quantidade",
              value=float(inv_atual["quantidade"]),
              format="%.4f",
          )
        with col_ie2:
          e_val = st.number_input(
              "Preço Unitário (R$)",
              value=float(inv_atual["valor"]),
              format="%.2f",
          )

        col_ib1, col_ib2 = st.columns(2)
        with col_ib1:
          btn_up_inv = st.form_submit_button(
              "✏️ Atualizar Ativo", use_container_width=True
          )
        with col_ib2:
          btn_del_inv = st.form_submit_button(
              "🗑️ Remover Ativo", use_container_width=True
          )

        if btn_up_inv:
          payload = {
              "id_user": st.session_state.id_user,
              "data": str(date.today()),
              "ativo": e_ativo.upper(),
              "classe": e_classe,
              "quantidade": e_qtd,
              "valor": e_val,
              "valor_total": e_qtd * e_val,
          }
          res = requests.put(f"{API_URL}/investments/{inv_id}", json=payload)
          if res.status_code == 200:
            st.toast("Investimento atualizado! 🔄", icon="✅")
            time.sleep(0.8)
            st.rerun()

        if btn_del_inv:
          res = requests.delete(f"{API_URL}/investments/{inv_id}")
          if res.status_code == 200:
            st.toast("Investimento removido!", icon="🗑️")
            time.sleep(0.8)
            st.rerun()

      st.divider()
      if st.session_state.get("ocultar_valores", False):
        df_inv_exib["valor"] = "R$ •••••"
        df_inv_exib["valor_total"] = "R$ •••••"
      st.dataframe(
          df_inv_exib.drop(columns=["id", "id_user"], errors="ignore"),
          use_container_width=True,
      )
    else:
      st.info("Nenhum investimento registrado.")


elif menu == "🎯 Definir Orçamento":
  st.title("🎯 Definição de Orçamento (Budget)")

  mes_ano = st.text_input(
      "Mês/Ano de Referência", value=date.today().strftime("%Y-%m")
  )

  col_b1, col_b2 = st.columns(2)

  with col_b1:
    st.markdown("###Cálculo Automático Inteligente")
    st.write(
        "Aloca VR/VA diretamente em Alimentação e VT em Transporte. O salário"
        " base será distribuído proporcionalmente entre as outras categorias."
    )
    if st.button("Gerar Orçamento Automático", use_container_width=True):
      res = requests.post(
          f"{API_URL}/budget/auto-generate/{st.session_state.id_user}/{mes_ano}"
      )
      if res.status_code == 200:
        msg = res.json().get("message", "Orçamento gerado com sucesso!")
        st.toast("Orçamento gerado! 📊", icon="🤖")
        st.success(msg)
        time.sleep(1.5)
        st.rerun()
      elif res.status_code == 400:
        detalhe = res.json().get("detail")
        st.toast("Atenção ao gerar orçamento", icon="⚠️")
        st.warning(f"⚠️ {detalhe}")
      else:
        st.error("Erro ao gerar orçamento automático.")

  with col_b2:
    st.markdown("### ✏️ Ajuste Manual")
    cat_b = st.selectbox("Categoria", list(CATEGORIES_MAP.keys()), key="cat_b")

    with st.form("form_manual_budget"):
      limite_b = st.number_input(
          "Limite Máximo de Gasto (R$)",
          min_value=1.0,
          value=500.0,
          step=50.0,
          format="%.2f",
      )
      btn_salvar_b = st.form_submit_button(
          "💾 Salvar Limite", use_container_width=True
      )

      if btn_salvar_b:
        payload = {
            "id_user": st.session_state.id_user,
            "categoria": cat_b,
            "sub_categoria": "",
            "mes_ano": mes_ano,
            "valor_limite": limite_b,
        }
        res = requests.post(f"{API_URL}/budget/", json=payload)
        if res.status_code in [200, 201]:
          st.toast("Limite salvo!", icon="🎯")
          time.sleep(0.8)
          st.rerun()

  st.divider()
  st.subheader(f"📊 Limites Definidos para {mes_ano}")
  res_atual = requests.get(
      f"{API_URL}/budget/{st.session_state.id_user}/{mes_ano}"
  )
  if res_atual.status_code == 200 and res_atual.json():
    df_b_atual = pd.DataFrame(res_atual.json())
    if st.session_state.get("ocultar_valores", False):
      df_b_atual["valor_limite"] = "R$ •••••"
    st.dataframe(
        df_b_atual.drop(columns=["id", "id_user"], errors="ignore"),
        use_container_width=True,
    )
  else:
    st.info("Nenhum orçamento configurado para este período.")