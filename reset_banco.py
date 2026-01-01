import os
import hashlib
# Importamos o DATABASE_URL para saber exatamente qual arquivo apagar
from src.database.database import Base, engine, Session, Usuario, ProdutoServico, Cliente, Material, MovimentacaoEstoque, DATABASE_URL

def resetar_tudo():
    print("--- INICIANDO RESET DO BANCO DE DADOS ---")
    
    # 1. Identifica o nome do arquivo do banco
    nome_arquivo_db = DATABASE_URL.replace("sqlite:///", "")
    
    # 2. Apagar arquivo do banco se existir (Onde ocorre a limpeza real)
    if os.path.exists(nome_arquivo_db):
        try:
            os.remove(nome_arquivo_db)
            print(f"✅ Arquivo '{nome_arquivo_db}' APAGADO com sucesso!")
        except PermissionError:
            print(f"❌ ERRO: O arquivo '{nome_arquivo_db}' está travado/aberto.")
            print("   -> Feche o terminal, feche a aplicação e tente novamente.")
            return
    
    # 3. Recriar Tabelas
    print("🔨 Criando novas tabelas...")
    Base.metadata.create_all(engine)
    print("✅ Tabelas recriadas.")
    
    session = Session()

    # 4. Criar Usuário Admin (COM CRIPTOGRAFIA CORRETA)
    print("👤 Criando usuário admin...")
    senha_texto_puro = "admin"
    
    # Gera o hash SHA256 da senha 'admin'
    senha_bytes = senha_texto_puro.encode('utf-8')
    hash_obj = hashlib.sha256(senha_bytes)
    senha_cripto = hash_obj.hexdigest()

    # Salva no banco com o nome de coluna correto: senha_hash
    admin = Usuario(nome="Administrador", usuario="admin", senha_hash=senha_cripto)
    session.add(admin)

    # 5. Criar Clientes Exemplo
    print("🤝 Criando clientes...")
    cli1 = Cliente(nome_empresa="Cliente Balcão", telefone="(79) 99999-9999")
    cli2 = Cliente(nome_empresa="Loja do Centro", telefone="(79) 88888-8888", documento="12345678000199")
    session.add_all([cli1, cli2])

    # 6. Criar Materiais de Estoque (Insumos)
    print("🏭 Criando estoque de insumos...")
    m1 = Material(nome="Rolo Lona 440g", unidade="Rolo", quantidade=2.0, estoque_minimo=1.0)
    m2 = Material(nome="Tinta Solvente Cyan", unidade="Litro", quantidade=5.0, estoque_minimo=2.0)
    session.add_all([m1, m2])

    session.commit()
    session.close()
    print("\n✅ TUDO PRONTO! A senha do usuário 'admin' foi redefinida corretamente.")
    print("👉 Pode rodar 'python main.py'")

if __name__ == "__main__":
    resetar_tudo()