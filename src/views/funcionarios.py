import flet as ft
from src.database.database import get_session, Usuario
import hashlib

def ViewFuncionarios(page: ft.Page):
    
    id_editar = ft.Ref[int]()
    id_excluir = ft.Ref[int]() # Referência para saber quem excluir no diálogo
    
    # --- CAMPOS DO FORMULÁRIO ---
    txt_nome = ft.TextField(label="Nome do Funcionário", bgcolor="white", height=40, content_padding=10)
    txt_usuario = ft.TextField(label="Login (Usuário)", bgcolor="white", height=40, content_padding=10)
    txt_senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, bgcolor="white", height=40, content_padding=10)
    
    # --- CHECKBOXES DE PERMISSÃO ---
    chk_admin = ft.Checkbox(label="Admin Master (Poder Total)", label_style=ft.TextStyle(weight="bold", color="red"))
    chk_designer = ft.Checkbox(label="Designer (Baixar Arquivos)")
    chk_cadastrar = ft.Checkbox(label="Cadastrar (Clientes/Vendas)")
    chk_estoque = ft.Checkbox(label="Gerenciar Estoque") # Permissão de Estoque
    chk_excluir = ft.Checkbox(label="Excluir Registros (Perigoso)")
    chk_dash = ft.Checkbox(label="Ver Dashboard/Financeiro")
    
    # --- TABELA DE USUÁRIOS ---
    tabela = ft.DataTable(
        heading_row_height=40, column_spacing=10,
        columns=[
            ft.DataColumn(ft.Text("Usuário")),
            ft.DataColumn(ft.Text("Admin", color="red")),
            ft.DataColumn(ft.Text("Vendas")),
            ft.DataColumn(ft.Text("Estoque")),
            ft.DataColumn(ft.Text("Dash")),
            ft.DataColumn(ft.Text("Ações")),
        ], rows=[]
    )

    def carregar_dados():
        tabela.rows.clear()
        session = get_session()
        users = session.query(Usuario).all()
        session.close()

        def icone_check(valor, cor="green"):
            return ft.Icon(ft.Icons.CHECK_CIRCLE if valor else ft.Icons.CIRCLE_OUTLINED, color=cor if valor else "grey", size=18)

        for u in users:
            # Proteção: Não deixa editar/excluir o admin principal pela interface comum
            is_master = (u.usuario == "admin")
            
            tabela.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(u.usuario, weight="bold")),
                ft.DataCell(icone_check(u.is_admin, "red")),
                ft.DataCell(icone_check(u.can_register)),
                ft.DataCell(icone_check(u.manage_stock, "blue")), # Ícone Estoque
                ft.DataCell(icone_check(u.view_dashboard)),
                ft.DataCell(
                    ft.Row([
                        ft.IconButton(ft.Icons.EDIT, icon_color="blue", disabled=is_master, on_click=lambda e, usr=u: editar_usuario(usr)),
                        ft.IconButton(ft.Icons.DELETE, icon_color="red", disabled=is_master, on_click=lambda e, uid=u.id: confirmar_exclusao_click(uid))
                    ])
                )
            ]))
        page.update()

    def editar_usuario(u):
        id_editar.current = u.id
        txt_nome.value = u.nome
        txt_usuario.value = u.usuario
        txt_senha.value = "" # Senha em branco para não alterar
        txt_senha.label = "Nova Senha (Deixe vazio para manter)"
        
        # Carrega Permissões
        chk_admin.value = u.is_admin
        chk_designer.value = u.is_designer
        chk_cadastrar.value = u.can_register
        chk_estoque.value = u.manage_stock # Carrega Estoque
        chk_excluir.value = u.can_delete
        chk_dash.value = u.view_dashboard or u.view_financeiro 
        
        btn_acao.text = "Atualizar Usuário"
        btn_acao.bgcolor = "orange"
        page.update()

    # --- LÓGICA DE EXCLUSÃO COM CONFIRMAÇÃO ---
    def confirmar_exclusao_click(uid):
        id_excluir.current = uid
        page.open(dlg_confirm)

    def realizar_exclusao(e):
        if id_excluir.current:
            session = get_session()
            session.query(Usuario).filter_by(id=id_excluir.current).delete()
            session.commit(); session.close()
            carregar_dados()
            page.snack_bar = ft.SnackBar(ft.Text("Usuário removido!"), bgcolor="orange"); page.snack_bar.open=True
        page.close(dlg_confirm)
        page.update()

    dlg_confirm = ft.AlertDialog(
        title=ft.Text("Tem certeza?"),
        content=ft.Text("Essa ação não pode ser desfeita e o usuário perderá o acesso."),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_confirm)),
            ft.ElevatedButton("Excluir", bgcolor="red", color="white", on_click=realizar_exclusao),
        ],
    )

    def salvar_usuario(e):
        if not txt_usuario.value: return
        
        session = get_session()
        try:
            if id_editar.current:
                # Edição
                u = session.query(Usuario).get(id_editar.current)
                u.nome = txt_nome.value
                u.usuario = txt_usuario.value
                if txt_senha.value:
                    u.senha_hash = hashlib.sha256(txt_senha.value.encode()).hexdigest()
                
                u.is_admin = chk_admin.value
                u.is_designer = chk_designer.value
                u.can_register = chk_cadastrar.value
                u.manage_stock = chk_estoque.value # Salva Estoque
                u.can_delete = chk_excluir.value
                u.view_dashboard = chk_dash.value
                u.view_financeiro = chk_dash.value
                
                msg = "Usuário Atualizado!"
            else:
                # Novo
                if not txt_senha.value:
                    page.snack_bar = ft.SnackBar(ft.Text("Senha obrigatória para novo usuário!"), bgcolor="red"); page.snack_bar.open=True; page.update(); return
                
                novo = Usuario(
                    nome=txt_nome.value,
                    usuario=txt_usuario.value,
                    senha_hash=hashlib.sha256(txt_senha.value.encode()).hexdigest(),
                    is_admin=chk_admin.value,
                    is_designer=chk_designer.value,
                    can_register=chk_cadastrar.value,
                    manage_stock=chk_estoque.value, # Salva Estoque
                    can_delete=chk_excluir.value,
                    view_dashboard=chk_dash.value,
                    view_financeiro=chk_dash.value
                )
                session.add(novo)
                msg = "Usuário Criado!"

            session.commit()
            limpar_form()
            carregar_dados()
            page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor="green"); page.snack_bar.open=True; page.update()
            
        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro (Usuário já existe?): {err}"), bgcolor="red"); page.snack_bar.open=True; page.update()
        finally:
            session.close()

    def limpar_form():
        id_editar.current = None
        txt_nome.value = ""; txt_usuario.value = ""; txt_senha.value = ""
        txt_senha.label = "Senha"
        chk_admin.value = False; chk_designer.value = False; chk_cadastrar.value = False; chk_estoque.value = False
        chk_excluir.value = False; chk_dash.value = False
        btn_acao.text = "Criar Usuário"
        btn_acao.bgcolor = "blue"
        page.update()

    btn_acao = ft.ElevatedButton("Criar Usuário", bgcolor="blue", color="white", width=float('inf'), height=45, on_click=salvar_usuario)

    carregar_dados()

    return ft.Container(padding=20, bgcolor=ft.Colors.GREY_100, expand=True, content=ft.Column([
        ft.Text("Gestão de Equipe & Permissões", size=25, weight="bold", color=ft.Colors.BLUE_GREY_900),
        ft.Row([
            # Coluna 1: Formulário
            ft.Container(bgcolor="white", padding=20, border_radius=10, expand=1, content=ft.Column([
                ft.Text("Adicionar / Editar", weight="bold", size=16),
                ft.Divider(),
                txt_nome, txt_usuario, txt_senha,
                ft.Divider(),
                ft.Text("Permissões de Acesso:", weight="bold"),
                chk_admin,
                chk_designer,
                chk_cadastrar,
                chk_estoque, # Checkbox novo
                chk_excluir,
                chk_dash,
                ft.Divider(),
                btn_acao,
                ft.TextButton("Cancelar / Limpar", on_click=lambda e: limpar_form())
            ])),
            
            # Coluna 2: Lista
            ft.Container(bgcolor="white", padding=20, border_radius=10, expand=2, content=ft.Column([
                ft.Text("Usuários do Sistema", weight="bold", size=16),
                ft.Divider(),
                # Aqui está a correção principal: Usando Column com scroll em vez de Container
                ft.Column([tabela], scroll=ft.ScrollMode.AUTO, height=400)
            ]))
        ], vertical_alignment=ft.CrossAxisAlignment.START)
    ], scroll=ft.ScrollMode.AUTO))