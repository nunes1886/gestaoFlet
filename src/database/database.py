from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import datetime

DATABASE_URL = "sqlite:///gestaopro_2026.db"

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

def get_session():
    return Session()

# --- TABELAS DE SISTEMA ---
class Empresa(Base):
    __tablename__ = 'empresa_config'
    id = Column(Integer, primary_key=True)
    nome_fantasia = Column(String, default="Minha Gráfica")
    cnpj = Column(String, default="")
    endereco = Column(String, default="")
    telefone = Column(String, default="")
    caminho_logo = Column(String, default="") 
    caminho_icon = Column(String, default="") 
    cor_primaria = Column(String, default="BLUE")

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nome = Column(String)
    usuario = Column(String, unique=True, nullable=False)
    senha_hash = Column(String, nullable=False) 

# --- TABELAS DE NEGÓCIO ---
class Cliente(Base):
    __tablename__ = 'clientes'
    id = Column(Integer, primary_key=True)
    nome_empresa = Column(String, nullable=False)
    telefone = Column(String)
    email = Column(String)
    documento = Column(String)
    is_revenda = Column(Boolean, default=False)
    ordens = relationship("OrdemServico", back_populates="cliente")

class ProdutoServico(Base):
    __tablename__ = 'produtos_servicos'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    categoria = Column(String) 
    preco_venda = Column(Float)
    preco_revenda = Column(Float, default=0.0) # <--- NOVO CAMPO
    unidade = Column(String) 

class OrdemServico(Base):
    __tablename__ = 'ordens_servico'
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    data_criacao = Column(DateTime, default=datetime.datetime.now)
    status = Column(String, default="Fila") 
    valor_total = Column(Float)
    valor_pago = Column(Float, default=0.0)
    motivo = Column(String) 
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
    tipo = Column(String)
    quantidade = Column(Float)
    data = Column(DateTime, default=datetime.datetime.now)
    observacao = Column(String)
    material = relationship("Material", back_populates="movimentacoes")

Base.metadata.create_all(engine)