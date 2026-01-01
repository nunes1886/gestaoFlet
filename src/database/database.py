from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import datetime

# Cria o arquivo do banco de dados (SQLite)
DATABASE_URL = "sqlite:///gestaopro_2026.db"

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

def get_session():
    return Session()

# --- TABELAS DE SISTEMA (LOGIN E CONFIG) ---

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nome = Column(String)
    usuario = Column(String, unique=True, nullable=False)
    # CORREÇÃO: Mudado de 'senha' para 'senha_hash' para bater com o main.py
    senha_hash = Column(String, nullable=False) 

class Configuracao(Base):
    __tablename__ = 'configuracoes'
    id = Column(Integer, primary_key=True)
    chave = Column(String, unique=True)
    valor = Column(String)

# --- TABELAS DE VENDAS E CLIENTES ---

class Cliente(Base):
    __tablename__ = 'clientes'
    id = Column(Integer, primary_key=True)
    nome_empresa = Column(String, nullable=False)
    telefone = Column(String)
    email = Column(String)
    documento = Column(String) # CPF/CNPJ
    
    ordens = relationship("OrdemServico", back_populates="cliente")

class ProdutoServico(Base):
    __tablename__ = 'produtos_servicos'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    categoria = Column(String) 
    preco_custo = Column(Float)
    preco_venda = Column(Float)
    unidade = Column(String) 

class OrdemServico(Base):
    __tablename__ = 'ordens_servico'
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    data_criacao = Column(DateTime, default=datetime.datetime.now)
    status = Column(String, default="Fila") 
    valor_total = Column(Float)
    valor_pago = Column(Float, default=0.0)
    observacoes = Column(Text)
    imagem_os = Column(String) 
    
    cliente = relationship("Cliente", back_populates="ordens")
    itens = relationship("ItemOS", back_populates="os", cascade="all, delete-orphan")

class ItemOS(Base):
    __tablename__ = 'itens_os'
    id = Column(Integer, primary_key=True)
    os_id = Column(Integer, ForeignKey('ordens_servico.id'))
    produto_id = Column(Integer, ForeignKey('produtos_servicos.id'))
    descricao_item = Column(String)
    largura = Column(Float)
    altura = Column(Float)
    quantidade = Column(Integer)
    preco_unitario = Column(Float)
    total_item = Column(Float)
    
    os = relationship("OrdemServico", back_populates="itens")
    produto = relationship("ProdutoServico")

# --- TABELAS DE ESTOQUE (NOVAS) ---

class Material(Base):
    __tablename__ = 'materiais' 
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    unidade = Column(String) 
    quantidade = Column(Float, default=0.0)
    estoque_minimo = Column(Float, default=5.0)
    
    movimentacoes = relationship("MovimentacaoEstoque", back_populates="material", cascade="all, delete-orphan")

class MovimentacaoEstoque(Base):
    __tablename__ = 'movimentacoes_estoque'
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey('materiais.id'))
    tipo = Column(String) # "Entrada" ou "Saída"
    quantidade = Column(Float)
    data = Column(DateTime, default=datetime.datetime.now)
    observacao = Column(String)
    
    material = relationship("Material", back_populates="movimentacoes")

# Cria as tabelas
Base.metadata.create_all(engine)