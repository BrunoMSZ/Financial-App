from datetime import date,datetime
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import bcrypt
from config.database import (
    Base,
    BudgetCreate,
    BudgetModel,
    InvestimentoCreate,
    InvestimentoModel,
    LoginSchema,
    SessionLocal,
    TransacaoCreate,
    TransacaoModel,
    UserCreate,
    UserModel,
    engine,
)

app = FastAPI(title="Financial and Investment App", description="API for managing financial transactions", version="1.1.0")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TransactionSchema(BaseModel):
  id_user: int
  data: str
  tipo: str
  valor: float
  categoria: str
  sub_categoria: Optional[str] = ""
  metodo_pagamento: Optional[str] = "PIX"
  descricao: Optional[str] = ""

def hash_password(password: str) -> str:
  return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
      "utf-8"
  )


def verify_password(plain_password: str, hashed_password: str) -> bool:
  return bcrypt.checkpw(
      plain_password.encode("utf-8"), hashed_password.encode("utf-8")
  )

# -- Route API --
@app.post("/users/", status_code=201)
@app.post("/users", status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
  if db.query(UserModel).filter(UserModel.email == user.email).first():
    raise HTTPException(status_code=400, detail="Email already registered.")

  db_user = UserModel(
      nome=user.nome, email=user.email, senha=hash_password(user.senha)
  )
  db.add(db_user)
  db.commit()
  db.refresh(db_user)
  return {"id": db_user.id, "nome": db_user.nome, "email": db_user.email}


@app.get("/users/verify/{user_id}")
def verify_user(user_id: int, db: Session = Depends(get_db)):
  user = db.query(UserModel).filter(UserModel.id == user_id).first()
  if not user:
    raise HTTPException(status_code=404, detail="User not found in database.")
  return {"id": user.id, "nome": user.nome, "email": user.email}


@app.post("/login/")
@app.post("/login")
def login(credentials: LoginSchema, db: Session = Depends(get_db)):
  user = (
      db.query(UserModel)
      .filter(UserModel.email == credentials.email)
      .first()
  )
  if not user or not verify_password(credentials.senha, user.senha):
    raise HTTPException(
        status_code=400, detail="Invalid credentials or email/password."
    )
  return {"id": user.id, "nome": user.nome, "email": user.email}


# --- TRANSACTIONS ROUTES ---
@app.get("/transactions/{user_id}")
def list_transactions(user_id: int, db: Session = Depends(get_db)):
  return (
      db.query(TransacaoModel)
      .filter(TransacaoModel.id_user == user_id)
      .order_by(TransacaoModel.data.desc())
      .all()
  )


@app.post("/transactions/", status_code=201)
def create_transaction(
    transaction: TransactionSchema, db: Session = Depends(get_db)
):
  new_trans = TransacaoModel(**transaction.dict())
  db.add(new_trans)
  db.commit()
  db.refresh(new_trans)
  return new_trans


@app.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    data: TransactionSchema,
    db: Session = Depends(get_db),
):
  db_trans = (
      db.query(TransacaoModel)
      .filter(TransacaoModel.id == transaction_id)
      .first()
  )
  if not db_trans:
    raise HTTPException(status_code=404, detail="Transaction not found")

  for key, value in data.dict().items():
    setattr(db_trans, key, value)

  db.commit()
  db.refresh(db_trans)
  return db_trans


@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
  db_trans = (
      db.query(TransacaoModel)
      .filter(TransacaoModel.id == transaction_id)
      .first()
  )
  if not db_trans:
    raise HTTPException(status_code=404, detail="Transaction not found")
  db.delete(db_trans)
  db.commit()
  return {"detail": "Transaction deleted successfully"}


# --- INVESTMENTS ROUTES ---
@app.get("/investments/{user_id}")
def list_investments(user_id: int, db: Session = Depends(get_db)):
  return (
      db.query(InvestimentoModel)
      .filter(InvestimentoModel.id_user == user_id)
      .all()
  )


@app.post("/investments/", status_code=201)
def create_investment(
    investment: InvestimentoCreate, db: Session = Depends(get_db)
):
  try:
    inv_data = investment.dict()

    if isinstance(inv_data.get("data"), str):
      inv_data["data"] = datetime.strptime(
          inv_data["data"], "%Y-%m-%d"
      ).date()

    inv_data["valor_total"] = round(
        investment.quantidade * investment.valor, 2
    )

    new_inv = InvestimentoModel(**inv_data)
    db.add(new_inv)
    db.commit()
    db.refresh(new_inv)
    return new_inv
  except Exception as e:
    db.rollback()
    raise HTTPException(
        status_code=500, detail=f"Erro ao salvar investimento: {str(e)}"
    )


@app.put("/investments/{investment_id}")
def update_investment(
    investment_id: int,
    data: InvestimentoCreate,
    db: Session = Depends(get_db),
):
  db_inv = (
      db.query(InvestimentoModel)
      .filter(InvestimentoModel.id == investment_id)
      .first()
  )
  if not db_inv:
    raise HTTPException(status_code=404, detail="Investimento não encontrado.")

  try:
    inv_data = data.dict()

    if isinstance(inv_data.get("data"), str):
      inv_data["data"] = datetime.strptime(
          inv_data["data"], "%Y-%m-%d"
      ).date()

    inv_data["valor_total"] = round(data.quantidade * data.valor, 2)

    for key, value in inv_data.items():
      setattr(db_inv, key, value)

    db.commit()
    db.refresh(db_inv)
    return db_inv
  except Exception as e:
    db.rollback()
    raise HTTPException(
        status_code=500, detail=f"Erro ao atualizar investimento: {str(e)}"
    )


@app.delete("/investments/{investment_id}")
def delete_investment(investment_id: int, db: Session = Depends(get_db)):
  db_inv = (
      db.query(InvestimentoModel)
      .filter(InvestimentoModel.id == investment_id)
      .first()
  )
  if not db_inv:
    raise HTTPException(status_code=404, detail="Investimento não encontrado.")
  db.delete(db_inv)
  db.commit()
  return {"detail": "Investimento excluído com sucesso."}


# --- BUDGET ROUTES ---
@app.get("/budget/{user_id}/{month_year}")
def get_budget(
    user_id: int, month_year: str, db: Session = Depends(get_db)
):
  return (
      db.query(BudgetModel)
      .filter(
          BudgetModel.id_user == user_id,
          BudgetModel.mes_ano == month_year,
      )
      .all()
  )


@app.post("/budget/auto-generate/{user_id}/{month_year}")
def auto_generate_budget(
    user_id: int, month_year: str, db: Session = Depends(get_db)
):
  incomes = (
      db.query(TransacaoModel)
      .filter(
          TransacaoModel.id_user == user_id,
          TransacaoModel.tipo.ilike("entrada%"),
      )
      .all()
  )

  if not incomes:
    raise HTTPException(
        status_code=400,
        detail="Nenhuma entrada cadastrada para gerar o orçamento.",
    )

  VR_VA_KEYWORDS = [
      "vr",
      "va",
      "refeição",
      "refeicao",
      "alimentação",
      "alimentacao",
  ]
  VT_KEYWORDS = ["vt", "transporte", "combustível", "combustivel"]

  vr_va_total = 0.0
  vt_total = 0.0
  salary_total = 0.0

  for t in incomes:
    text = f"{t.categoria} {t.sub_categoria or ''} {t.descricao or ''}".lower()
    if any(k in text for k in VR_VA_KEYWORDS):
      vr_va_total += t.valor
    elif any(k in text for k in VT_KEYWORDS):
      vt_total += t.valor
    else:
      salary_total += t.valor

  if salary_total <= 0 and vr_va_total <= 0 and vt_total <= 0:
    raise HTTPException(
        status_code=400,
        detail="Nenhuma entrada com valor positivo encontrada.",
    )

  BASE_WEIGHTS = {
      "Moradia": 0.30,
      "Alimentação": 0.20,
      "Transporte": 0.15,
      "Saúde": 0.10,
      "Educação": 0.10,
      "Lazer": 0.10,
      "Outros": 0.05,
  }

  final_budgets = {}

  if vr_va_total > 0:
    final_budgets["Alimentação"] = round(vr_va_total, 2)

  if vt_total > 0:
    final_budgets["Transporte"] = round(vt_total, 2)

  remaining_categories = {
      cat: weight
      for cat, weight in BASE_WEIGHTS.items()
      if cat not in final_budgets
  }

  total_remaining_weight = sum(remaining_categories.values())

  if salary_total > 0 and total_remaining_weight > 0:
    for cat, weight in remaining_categories.items():
      normalized_weight = weight / total_remaining_weight
      final_budgets[cat] = round(salary_total * normalized_weight, 2)
  else:
    for cat in remaining_categories:
      final_budgets[cat] = 0.0

  created_budgets = []
  for cat, limit in final_budgets.items():
    existing = (
        db.query(BudgetModel)
        .filter(
            BudgetModel.id_user == user_id,
            BudgetModel.mes_ano == month_year,
            BudgetModel.categoria == cat,
        )
        .first()
    )

    if existing:
      existing.valor_limite = limit
      created_budgets.append(existing)
    else:
      new_b = BudgetModel(
          id_user=user_id,
          categoria=cat,
          sub_categoria="Geral",
          mes_ano=month_year,
          valor_limite=limit,
      )
      db.add(new_b)
      created_budgets.append(new_b)

  db.commit()

  msg_details = []
  if vr_va_total > 0:
    msg_details.append(f"VR/VA (R$ {vr_va_total:,.2f}) -> Alimentação")
  if vt_total > 0:
    msg_details.append(f"VT (R$ {vt_total:,.2f}) -> Transporte")

  beneficios_str = (
      f" ({', '.join(msg_details)})" if msg_details else " (Sem benefícios)"
  )

  return {
      "status": "success",
      "message": (
          f"Orçamento gerado com sucesso! Salário base de R$"
          f" {salary_total:,.2f} distribuído{beneficios_str}."
      ),
  }


@app.post("/budget/", status_code=201)
def save_budget(budget: BudgetCreate, db: Session = Depends(get_db)):
  existing = (
      db.query(BudgetModel)
      .filter(
          BudgetModel.id_user == budget.id_user,
          BudgetModel.mes_ano == budget.mes_ano,
          BudgetModel.categoria == budget.categoria,
      )
      .first()
  )

  if existing:
    existing.valor_limite = budget.valor_limite
    db.commit()
    db.refresh(existing)
    return existing

  new_budget = BudgetModel(**budget.dict())
  db.add(new_budget)
  db.commit()
  db.refresh(new_budget)
  return new_budget