import os
import time
from src.database.database import Base, engine, ProdutoServico, Usuario
from sqlalchemy.orm import sessionmaker

def resetar_tudo():
    print("--- INICIANDO RESET DO BANCO DE DADOS ---")

    # 1. Identificar o arquivo
    db_file = "app.db"
    if engine.url.drivername == 'sqlite' and engine.url.database:
        db_file = engine.url.database

    print(f"Alvo detectado: {db_file}")

    # --- O SEGREDO ESTÁ AQUI ---
    # Força o Python a soltar o arquivo antes de tentar apagar
    engine.dispose()
    time.sleep(1) # Espera 1 segundo para o Windows liberar o arquivo
    # ---------------------------

    # 2. Apagar o arquivo
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print("✅ Banco de dados antigo APAGADO com sucesso!")
        except PermissionError:
            print("❌ ERRO: O arquivo ainda está preso pelo Windows.")
            print("Tente reiniciar o VS Code e rodar novamente.")
            return
        except Exception as e:
            print(f"❌ Erro ao apagar: {e}")
            return
    else:
        print("⚠️ Arquivo não existia (caminho livre).")

    # 3. Recriar tabelas
    print("🔨 Criando novas tabelas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas recriadas.")

    # 4. Inserir Dados Iniciais
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Produtos de Teste
    if session.query(ProdutoServico).count() == 0:
        print("📦 Cadastrando produtos com estoque...")
        produtos = [
            ProdutoServico(nome="Lona 440g (M²)", preco_venda=40.0, preco_revenda=30.0, categoria="Impressão", estoque_atual=50, estoque_minimo=10),
            ProdutoServico(nome="Adesivo Vinil (M²)", preco_venda=55.0, preco_revenda=45.0, categoria="Impressão", estoque_atual=5, estoque_minimo=10),
            ProdutoServico(nome="Criação de Arte", preco_venda=50.0, preco_revenda=0.0, categoria="Criação", estoque_atual=999, estoque_minimo=0),
            ProdutoServico(nome="Ilhós (Unid)", preco_venda=1.0, preco_revenda=0.50, categoria="Acabamento", estoque_atual=500, estoque_minimo=100),
        ]
        session.add_all(produtos)
    
    # Criar Admin usando a lógica que você já tem no criar_usuario.py
    if session.query(Usuario).filter_by(usuario="admin").count() == 0:
        print("👤 Recriando usuário Admin...")
        admin = Usuario(nome="Administrador Master", usuario="admin", senha_hash="admin123", cargo="admin")
        session.add(admin)

    session.commit()
    session.close()
    print("\n🚀 TUDO PRONTO! Banco atualizado com suporte a Estoque.")

if __name__ == "__main__":
    resetar_tudo()