import os
import hashlib
import datetime # Import necessário para data
from src.database.database import Base, engine, Session, Usuario, ProdutoServico, Cliente, Material, Empresa, DATABASE_URL

def resetar_tudo():
    print("--- INICIANDO RESET ---")
    nome_db = DATABASE_URL.replace("sqlite:///", "")
    engine.dispose()

    if os.path.exists(nome_db):
        try: os.remove(nome_db); print("✅ Banco apagado.")
        except: print("❌ Feche o app e tente de novo."); return
    
    print("🔨 Criando tabelas...")
    Base.metadata.create_all(engine)
    session = Session()

    print("👤 Admin e Empresa...")
    hash_senha = hashlib.sha256("admin".encode()).hexdigest()
    session.add(Usuario(nome="Admin", usuario="admin", senha_hash=hash_senha))
    session.add(Empresa(nome_fantasia="Minha Gráfica", telefone="(00) 0000-0000"))

    print("📦 Produtos e Clientes...")
    session.add_all([
        ProdutoServico(nome="Lona 440g", preco_venda=40.0, preco_revenda=30.0),
        ProdutoServico(nome="Adesivo", preco_venda=55.0, preco_revenda=45.0)
    ])
    session.add(Cliente(nome_empresa="Cliente Balcão", telefone="(00) 0000-0000"))

    session.commit(); session.close()
    print("✅ TUDO PRONTO! Novas colunas (Urgência e Entrega) criadas.")

if __name__ == "__main__":
    resetar_tudo()