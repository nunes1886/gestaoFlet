import os
import hashlib
from src.database.database import Base, engine, Session, Usuario, ProdutoServico, Cliente, Material, Empresa, DATABASE_URL

def resetar_tudo():
    print("--- INICIANDO RESET DO BANCO DE DADOS ---")
    
    # 1. Identifica o nome do arquivo do banco
    nome_arquivo_db = DATABASE_URL.replace("sqlite:///", "")
    
    # Solta o arquivo para poder apagar
    engine.dispose()

    # 2. Apagar arquivo do banco se existir
    if os.path.exists(nome_arquivo_db):
        try:
            os.remove(nome_arquivo_db)
            print(f"✅ Arquivo '{nome_arquivo_db}' APAGADO com sucesso!")
        except PermissionError:
            print(f"❌ ERRO: O arquivo '{nome_arquivo_db}' está travado.")
            print("   -> Feche o VS Code totalmente e tente de novo.")
            return
    
    # 3. Recriar Tabelas
    print("🔨 Criando novas tabelas...")
    Base.metadata.create_all(engine)
    print("✅ Tabelas recriadas.")
    
    session = Session()

    # 4. Criar Usuário Admin
    print("👤 Criando usuário admin...")
    senha_texto_puro = "admin"
    senha_bytes = senha_texto_puro.encode('utf-8')
    hash_obj = hashlib.sha256(senha_bytes)
    senha_cripto = hash_obj.hexdigest()

    admin = Usuario(nome="Administrador", usuario="admin", senha_hash=senha_cripto)
    session.add(admin)

    # 5. Criar Empresa Padrão
    print("🏢 Configurando Empresa Padrão...")
    session.add(Empresa(nome_fantasia="Minha Gráfica", telefone="(00) 0000-0000"))

    # 6. Criar Clientes Exemplo (COM TESTE DE REVENDA)
    print("🤝 Criando clientes...")
    cli1 = Cliente(nome_empresa="Cliente Final (Balcão)", telefone="(79) 99999-9999", is_revenda=False)
    cli2 = Cliente(nome_empresa="Agência Parceira (Revenda)", telefone="(79) 88888-8888", documento="12345678000199", is_revenda=True)
    session.add_all([cli1, cli2])

    # 7. Criar Materiais de Estoque
    print("🏭 Criando estoque de insumos...")
    m1 = Material(nome="Rolo Lona 440g", unidade="Rolo", quantidade=2.0, estoque_minimo=1.0)
    m2 = Material(nome="Tinta Solvente Cyan", unidade="Litro", quantidade=5.0, estoque_minimo=2.0)
    session.add_all([m1, m2])

    # 8. Criar Produtos de Venda (COM PREÇO REVENDA)
    print("📦 Criando produtos de venda...")
    p1 = ProdutoServico(nome="Lona 440g (m²)", categoria="Impressão", preco_venda=40.0, preco_revenda=30.0, unidade="m²")
    p2 = ProdutoServico(nome="Adesivo Vinil (m²)", categoria="Impressão", preco_venda=55.0, preco_revenda=45.0, unidade="m²")
    p3 = ProdutoServico(nome="Cartão de Visita 1000un", categoria="Offset", preco_venda=120.0, preco_revenda=90.0, unidade="un")
    session.add_all([p1, p2, p3])

    session.commit()
    session.close()
    print("\n✅ TUDO PRONTO! Banco resetado com sucesso.")
    print("👉 Pode rodar 'python main.py'")

if __name__ == "__main__":
    resetar_tudo()