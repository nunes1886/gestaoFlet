import os
import hashlib
from src.database.database import Base, engine, Session, Usuario, ProdutoServico, Cliente, Material, Empresa, Setor, StatusOS, DATABASE_URL

def resetar_tudo():
    print("--- INICIANDO RESET DO BANCO ---")
    
    # Tratamento para garantir que o caminho do DB esteja limpo
    nome_db = DATABASE_URL.replace("sqlite:///", "")
    engine.dispose()

    if os.path.exists(nome_db):
        try: 
            os.remove(nome_db)
            print("✅ Banco antigo apagado.")
        except Exception as e: 
            print(f"❌ Erro ao apagar banco: {e}. Feche o app e tente de novo.")
            return
    
    print("🔨 Criando tabelas...")
    Base.metadata.create_all(engine)
    session = Session()

    print("👤 Criando Admin Master...")
    hash_senha = hashlib.sha256("admin".encode()).hexdigest()
    
    admin = Usuario(
        nome="Administrador", usuario="admin", senha_hash=hash_senha,
        is_admin=True, is_designer=True, can_register=True, can_delete=True, 
        view_dashboard=True, view_financeiro=True, manage_stock=True
    )
    session.add(admin)

    print("🏭 Criando Setores e Status Padrão...")
    
    # Setores (Locais físicos)
    session.add_all([
        Setor(nome="Atendimento"),
        Setor(nome="Impressão"),
        Setor(nome="Acabamento"),
        Setor(nome="Expedição")
    ])
    
    # Status (Colunas do Kanban) - AQUI ESTÁ A MUDANÇA (ordem=X)
    session.add_all([
        StatusOS(nome="Fila", cor="grey", ordem=1),
        StatusOS(nome="Impressão", cor="blue", ordem=2),     # Alterei "Rodando" para "Impressão" (padrão de mercado)
        StatusOS(nome="Acabamento", cor="orange", ordem=3),
        StatusOS(nome="Expedição", cor="purple", ordem=4),
        StatusOS(nome="Entregue", cor="green", ordem=5)      # Importante para a aba de histórico
    ])

    print("🏢 Dados básicos da empresa...")
    session.add(Empresa(nome_fantasia="Minha Gráfica", telefone="(00) 0000-0000"))
    
    session.add_all([
        ProdutoServico(nome="Lona 440g", preco_venda=40.0, preco_revenda=30.0),
        ProdutoServico(nome="Adesivo Vinil", preco_venda=55.0, preco_revenda=45.0)
    ])
    
    session.add(Cliente(nome_empresa="Cliente Balcão", telefone="(00) 0000-0000"))

    session.commit()
    session.close()
    print("✅ TUDO PRONTO! Permissões, Workflow e Ordem do Kanban criados.")

if __name__ == "__main__":
    resetar_tudo()