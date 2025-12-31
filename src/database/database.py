# src/database/database.py
import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# Cria a base para os modelos
Base = declarative_base()

# --- DEFINIÇÃO DAS TABELAS ---

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    usuario = Column(String, unique=True, nullable=False)
    senha_hash = Column(String, nullable=False) # Armazena a senha (hash idealmente)
    cargo = Column(String, nullable=False) # 'admin', 'producao', 'vendedor', 'designer'
    ativo = Column(Boolean, default=True)

class Cliente(Base):
    __tablename__ = 'clientes'
    id = Column(Integer, primary_key=True)
    nome_empresa = Column(String, nullable=False)
    telefone = Column(String)
    email = Column(String, nullable=True)
    documento = Column(String, nullable=True) # CPF ou CNPJ
    tipo = Column(String, default="Final") # 'Final' ou 'Revenda'
    ativo = Column(Boolean, default=True)
    
    # Relacionamento inverso (Opcional, mas ajuda em consultas complexas)
    ordens_servico = relationship("OrdemServico", back_populates="cliente")

class ProdutoServico(Base):
    __tablename__ = 'produtos'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    preco_venda = Column(Float, default=0.0)   # Preço para cliente final
    preco_revenda = Column(Float, default=0.0) # Preço para revendedores/parceiros
    categoria = Column(String) # 'Impressão', 'Acabamento', 'Criação'

    # Controle de Estoque Direto no Produto (Usado na tela de Estoque)
    estoque_atual = Column(Integer, default=0) 
    estoque_minimo = Column(Integer, default=10) 

class OrdemServico(Base):
    __tablename__ = 'ordens_servico'
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True) # Pode ser Null se não tiver login sistema ainda
    
    data_criacao = Column(DateTime, default=datetime.now)
    data_entrega = Column(DateTime)
    
    status = Column(String, default="Fila") # 'Fila', 'Impressão', 'Acabamento', 'Expedição', 'Entregue'
    
    valor_total = Column(Float, default=0.0)
    valor_pago = Column(Float, default=0.0) # Controle de Sinal/Pagamento
    forma_pagamento = Column(String)
    
    # Campo atualizado para bater com a tela de Vendas
    observacoes = Column(String, nullable=True)

    imagem_os = Column(String, nullable=True) 
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="ordens_servico")
    usuario = relationship("Usuario")
    itens = relationship("ItemOS", back_populates="os", cascade="all, delete-orphan")

class ItemOS(Base):
    __tablename__ = 'itens_os'
    id = Column(Integer, primary_key=True)
    os_id = Column(Integer, ForeignKey('ordens_servico.id'))
    produto_id = Column(Integer, ForeignKey('produtos.id'))
    
    descricao_item = Column(String) # Nome do produto congelado na venda
    largura = Column(Float)         # Metros
    altura = Column(Float)          # Metros
    quantidade = Column(Integer, default=1)
    
    preco_unitario = Column(Float)  # Preço cobrado no momento da venda
    total_item = Column(Float)

    os = relationship("OrdemServico", back_populates="itens")
    produto = relationship("ProdutoServico")

# --- TABELAS ADICIONAIS (Futuro / Expansão) ---
# Mantivemos aqui caso queira controlar estoque de matéria prima separada depois
class Estoque(Base):
    __tablename__ = 'estoque'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    unidade = Column(String) 
    quantidade_atual = Column(Float, default=0.0)
    minimo_alerta = Column(Float, default=5.0)

class MovimentacaoEstoque(Base):
    __tablename__ = 'mov_estoque'
    id = Column(Integer, primary_key=True)
    estoque_id = Column(Integer, ForeignKey('estoque.id'))
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    tipo = Column(String) 
    quantidade = Column(Float)
    data = Column(DateTime, default=datetime.now)

    estoque = relationship("Estoque")

# --- CONFIGURAÇÕES DO SISTEMA ---
class Configuracao(Base):
    __tablename__ = 'configuracoes'
    id = Column(Integer, primary_key=True)
    
    nome_fantasia = Column(String, default="Sistema Gráfica")
    razao_social = Column(String)
    cnpj = Column(String)
    endereco = Column(String)
    telefone = Column(String)
    
    caminho_logo = Column(String)
    caminho_icone = Column(String) 
    cor_primaria = Column(String, default="BLUE") 

# --- CONEXÃO BLINDADA ---

def get_db_path():
    app_name = "SistemaGraficaPro"
    if sys.platform == "win32":
        app_data = os.getenv("APPDATA")
        path = os.path.join(app_data, app_name)
    else:
        path = os.path.join(os.path.expanduser("~"), "." + app_name)
    
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError:
            return "sistema_dados.db"
        
    return os.path.join(path, "sistema_dados.db")

db_path = get_db_path()
engine = create_engine(f'sqlite:///{db_path}', echo=False)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

def get_session():
    return Session()