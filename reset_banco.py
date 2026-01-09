import os
import hashlib
# ADICIONEI: ChatMensagem na importação abaixo
from src.database.database import Base, engine, Session, Usuario, ProdutoServico, Cliente, Material, Empresa, Setor, StatusOS, DATABASE_URL, ChatMensagem

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
    
    print("🔨 Criando tabelas (Incluindo Chat)...")
    Base.metadata.create_all(engine)
    session = Session()

    print("👤 Criando Admin Master...")
    hash_senha = hashlib.sha256("admin".encode()).hexdigest()
    
    # Atualizei as permissões para incluir tudo
    admin = Usuario(
        nome="Administrador", usuario="admin", senha_hash=hash_senha,
        is_admin=True, 
        is_designer=True, 
        can_register=True, 
        can_delete=True, 
        view_dashboard=True, 
        view_financeiro=True, 
        manage_stock=True
    )
    session.add(admin)

    print("🏭 Criando Setores e Status Padrão...")
    
    # Setores (Locais físicos)
    session.add_all([
        Setor(nome="Atendimento"),
        Setor(nome="Criação/Design"), # Adicionei este
        Setor(nome="Impressão"),
        Setor(nome="Acabamento"),
        Setor(nome="Expedição")
    ])
    
    # Status (ATUALIZADO PARA O FLUXO COMPLETO QUE CRIAMOS)
    session.add_all([
        # 1. Financeiro / Bloqueio
        StatusOS(nome="Aguardando Pagamento", cor="red", ordem=0),
        
        # 2. Design (Para o Kanban de Criação)
        StatusOS(nome="Criando Arte", cor="purple", ordem=1),
        StatusOS(nome="Aprovação", cor="orange", ordem=2),
        
        # 3. Produção (Para o Painel de Produção)
        StatusOS(nome="Fila", cor="grey", ordem=3),
        StatusOS(nome="Impressão", cor="blue", ordem=4),
        StatusOS(nome="Acabamento", cor="amber", ordem=5),
        
        # 4. Finalização
        StatusOS(nome="Entregue", cor="green", ordem=6),
        StatusOS(nome="Cancelado", cor="black", ordem=7)
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
    print("✅ TUDO PRONTO! Tabela de Chat criada e Status atualizados.")

if __name__ == "__main__":
    resetar_tudo()