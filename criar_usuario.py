from src.database.database import get_session, Usuario

def criar_admin():
    print("--- INICIANDO CRIAÇÃO DE USUÁRIO ---")
    session = get_session()
    
    # Verifica se já existe
    user = session.query(Usuario).filter_by(usuario="admin").first()
    
    if user:
        print(f"O usuário 'admin' já existia. Atualizando a senha para 'admin123'...")
        user.senha_hash = "admin123"
    else:
        print("Usuário 'admin' não encontrado. Criando agora...")
        novo_admin = Usuario(
            nome="Administrador Master",
            usuario="admin",
            senha_hash="admin123",
            cargo="admin"
        )
        session.add(novo_admin)
    
    session.commit()
    session.close()
    print("--- SUCESSO! ---")
    print("Agora você pode rodar o main.py e logar com:")
    print("Usuario: admin")
    print("Senha:   admin123")

if __name__ == "__main__":
    criar_admin()