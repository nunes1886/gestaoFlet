from src.database.database import get_session, ProdutoServico

def criar_produtos():
    session = get_session()
    
    # Verifica se já tem produtos
    if session.query(ProdutoServico).count() > 0:
        print("Já existem produtos cadastrados.")
        return

    print("Cadastrando produtos padrão...")
    produtos = [
        ProdutoServico(nome="Lona 440g (M²)", preco_venda=40.0, preco_revenda=30.0, categoria="Impressão"),
        ProdutoServico(nome="Adesivo Vinil (M²)", preco_venda=55.0, preco_revenda=45.0, categoria="Impressão"),
        ProdutoServico(nome="Criação de Arte", preco_venda=50.0, preco_revenda=0.0, categoria="Criação"),
        ProdutoServico(nome="Acabamento Ilhós", preco_venda=1.0, preco_revenda=0.50, categoria="Acabamento"),
    ]
    
    session.add_all(produtos)
    session.commit()
    session.close()
    print("Sucesso! Produtos de teste criados.")

if __name__ == "__main__":
    criar_produtos()