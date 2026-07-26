from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Float, Date,ForeignKey
from typing import Optional
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel

SQLALCHEMY_DATABASE_URL = "sqlite:///financial_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --CREATE --

class UserModel(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    senha = Column(String) #hash

    #Relationships
    transacoes = relationship("TransacaoModel", back_populates="usuario")
    investimentos = relationship("InvestimentoModel", back_populates="usuario")
    budget = relationship("BudgetModel", back_populates="usuario")

class TransacaoModel(Base):
    __tablename__ = "transacoes"
    id = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("usuarios.id"), index=True)
    data = Column(String)
    tipo = Column(String)
    valor = Column(Float)
    categoria = Column(String)
    sub_categoria = Column(String, nullable=True)
    metodo_pagamento = Column(String, default="PIX")
    descricao = Column(String, nullable=True)

    #Relationships
    usuario = relationship("UserModel", back_populates="transacoes")

class BudgetModel(Base):
    __tablename__ = "budget"
    id = Column(Integer,primary_key = True, index = True)
    id_user = Column(Integer, ForeignKey("usuarios.id"))
    categoria = Column(String, index=True)
    sub_categoria = Column(String, nullable=True)
    mes_ano = Column(String,index=True)
    valor_limite = Column(Float)

    #Relationships
    usuario = relationship("UserModel",back_populates="budget")

class InvestimentoModel(Base):
    __tablename__ = "investimentos"
    id = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("usuarios.id"), index=True)
    data = Column(Date, default=date.today)
    ativo = Column(String)
    classe = Column(String)
    quantidade = Column(Float)
    valor = Column(Float)
    valor_total = Column(Float) # Quantidade * valor

    #Relationships
    usuario = relationship("UserModel", back_populates="investimentos")



Base.metadata.create_all(bind=engine)

# -- Dataset Validation --

class UserCreate(BaseModel):
    nome:str
    email:str
    senha:str

class TransacaoCreate(BaseModel):
    id_user: int
    data: date
    descricao: Optional[str] = ""
    categoria: str
    sub_categoria: str
    tipo: str
    valor: float

class InvestimentoCreate(BaseModel):
    id_user: int
    data: date
    ativo: str
    classe: str
    quantidade: float
    valor: float
    valor_total: Optional[float] = None

class BudgetCreate(BaseModel):
    id_user: int
    categoria: str
    sub_categoria: str
    mes_ano: str
    valor_limite: float

class LoginSchema(BaseModel):
  email: str
  senha: str