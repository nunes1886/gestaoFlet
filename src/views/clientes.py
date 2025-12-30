import flet as ft
from src.database.database import get_session, Cliente, OrdemServico

def ViewClientes(page):
    
    id_editar = ft.Ref[int]()
    
    # --- LÓGICA DE FORMATAÇÃO (ESTRATÉGIA ON BLUR / ON FOCUS) ---
    
    def formatar_telefone_blur(e):
        # Quando sai do campo: Aplica a máscara visual
        valor = "".join(filter(str.isdigit, e.control.value))[:11]
        
        if not valor:
            e.control.value = ""
        elif len(valor) <= 10:
            # (XX) XXXX-XXXX
            e.control.value = f"({valor[:2]}) {valor[2:6]}-{valor[6:]}"
        else:
            # (XX) XXXXX-XXXX
            e.control.value = f"({valor[:2]}) {valor[2:7]}-{valor[7:]}"
        
        e.control.update()

    def formatar_doc_blur(e):
        # Quando sai do campo: Aplica CPF ou CNPJ
        v = "".join(filter(str.isdigit, e.control.value))[:14]
        
        if not v:
            e.control.value = ""
        elif len(v) <= 11:
            # CPF: 000.000.000-00
            # Preenche com zeros à esquerda se for curto, ou formata o que tem
            if len(v) == 11:
                e.control.value = f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"
        else:
            # CNPJ: 00.000.000/0000-00
            if len(v) == 14:
                e.control.value = f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}"
        
        e.control.update()

    def limpar_formatacao_focus(e):
        # Quando clica para editar: Remove os símbolos para facilitar
        valor_limpo = "".join(filter(str.isdigit, e.control.value))
        e.control.value = valor_limpo
        e.control.update()

    # --- CAMPOS DO FORMULÁRIO ---
    txt_nome = ft.TextField(label="Nome Completo / Empresa", expand=True)
    
    txt_telefone = ft.TextField(
        label="Telefone (Só números)", 
        width=200,
        # O SEGREDO ESTÁ AQUI:
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"), # Só deixa digitar números
        on_blur=formatar_telefone_blur,   # Formata quando sai
        on_focus=limpar_formatacao_focus, # Limpa quando entra
        max_length=11 # Limita dígitos reais
    )
    
    txt_doc = ft.TextField(
        label="CPF ou CNPJ (Só números)", 
        width=200,
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"), # Só deixa digitar números
        on_blur=formatar_doc_blur,      # Formata quando sai
        on_focus=limpar_formatacao_focus, # Limpa quando entra
        max_length=14
    )
    
    txt_email = ft.TextField(label="Email (Opcional)", expand=True, prefix_icon=ft.icons.EMAIL)

    # --- RESTANTE DO CÓDIGO (IGUAL) ---
    def fechar_dialogo(e):
        dialogo_cliente.open = False
        page.update()

    def salvar_cliente(e):
        if not txt_nome.value:
            txt_nome.error_text = "Nome é obrigatório"
            txt_nome.update()
            return

        session = get_session()
        
        # Remove formatação antes de salvar no banco (para garantir dados limpos)
        tel_limpo = "".join(filter(str.isdigit, txt_telefone.value))
        doc_limpo = "".join(filter(str.isdigit, txt_doc.value))
        
        if id_editar.current:
            # --- MODO EDIÇÃO ---
            cliente = session.query(Cliente).get(id_editar.current)
            if cliente:
                cliente.nome_empresa = txt_nome.value
                cliente.telefone = tel_limpo
                cliente.email = txt_email.value
                cliente.documento = doc_limpo
                mensagem = "Dados atualizados!"
        else:
            # --- MODO NOVO ---
            novo_cliente = Cliente(
                nome_empresa=txt_nome.value,
                telefone=tel_limpo,
                email=txt_email.value,
                documento=doc_limpo
            )
            session.add(novo_cliente)
            mensagem = "Cliente cadastrado!"

        session.commit()
        session.close()
        
        dialogo_cliente.open = False
        page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor="green")
        page.snack_bar.open = True
        
        carregar_dados()
        page.update()

    # --- DIÁLOGO (MODAL) ---
    dialogo_cliente = ft.AlertDialog(
        title=ft.Text("Dados do Cliente"),
        content=ft.Container(
            width=600,
            content=ft.Column([
                txt_nome,
                ft.Row([txt_telefone, txt_doc]),
                txt_email
            ], height=220, spacing=20)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_dialogo),
            ft.ElevatedButton("Salvar", on_click=salvar_cliente, bgcolor=ft.colors.BLUE_600, color="white"),
        ],
    )

    # --- AÇÕES DA TELA ---
    def abrir_novo(e):
        id_editar.current = None
        txt_nome.value = ""
        txt_telefone.value = ""
        txt_email.value = ""
        txt_doc.value = ""
        txt_nome.error_text = None
        
        dialogo_cliente.title = ft.Text("Novo Cliente")
        page.dialog = dialogo_cliente
        dialogo_cliente.open = True
        page.update()

    def abrir_edicao(e, cli):
        id_editar.current = cli.id
        txt_nome.value = cli.nome_empresa
        
        # Formata visualmente ao abrir a edição
        tel = cli.telefone or ""
        if len(tel) == 11:
            txt_telefone.value = f"({tel[:2]}) {tel[2:7]}-{tel[7:]}"
        else:
            txt_telefone.value = tel
            
        txt_email.value = cli.email or ""
        
        doc = cli.documento or ""
        if len(doc) == 11:
            txt_doc.value = f"{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}"
        elif len(doc) == 14:
            txt_doc.value = f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}"
        else:
            txt_doc.value = doc
            
        txt_nome.error_text = None
        
        dialogo_cliente.title = ft.Text(f"Editar: {cli.nome_empresa}")
        page.dialog = dialogo_cliente
        dialogo_cliente.open = True
        page.update()

    def excluir_cliente(e, cli_id):
        session = get_session()
        tem_os = session.query(OrdemServico).filter_by(cliente_id=cli_id).count() > 0
        
        if tem_os:
            page.snack_bar = ft.SnackBar(ft.Text("Não é possível excluir: Cliente tem histórico de vendas."), bgcolor="red")
        else:
            cli = session.query(Cliente).get(cli_id)
            session.delete(cli)
            session.commit()
            page.snack_bar = ft.SnackBar(ft.Text("Cliente removido."), bgcolor="green")
            
        session.close()
        page.snack_bar.open = True
        carregar_dados()
        page.update()

    # --- TABELA DE DADOS ---
    tabela = ft.DataTable(
        width=float('inf'),
        column_spacing=20,
        columns=[
            ft.DataColumn(ft.Text("Nome", weight="bold")),
            ft.DataColumn(ft.Text("Documento", weight="bold")),
            ft.DataColumn(ft.Text("Telefone", weight="bold")),
            ft.DataColumn(ft.Text("Email", weight="bold")),
            ft.DataColumn(ft.Text("Ações", weight="bold")),
        ],
        rows=[]
    )

    def carregar_dados():
        tabela.rows.clear()
        session = get_session()
        clientes = session.query(Cliente).order_by(Cliente.id.desc()).all()
        session.close()

        for c in clientes:
            # Aplica formatação visual na tabela
            tel_visual = c.telefone
            if tel_visual and len(tel_visual) == 11:
                tel_visual = f"({tel_visual[:2]}) {tel_visual[2:7]}-{tel_visual[7:]}"
            
            doc_visual = c.documento
            if doc_visual and len(doc_visual) == 11:
                doc_visual = f"{doc_visual[:3]}.{doc_visual[3:6]}.{doc_visual[6:9]}-{doc_visual[9:]}"
            elif doc_visual and len(doc_visual) == 14:
                doc_visual = f"{doc_visual[:2]}.{doc_visual[2:5]}.{doc_visual[5:8]}/{doc_visual[8:12]}-{doc_visual[12:]}"

            tabela.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(c.nome_empresa, weight="bold")),
                        ft.DataCell(ft.Text(doc_visual if doc_visual else "-")),
                        ft.DataCell(ft.Text(tel_visual if tel_visual else "-")),
                        ft.DataCell(ft.Text(c.email if c.email else "-", size=12, color=ft.colors.GREY_700)),
                        ft.DataCell(ft.Row([
                            ft.IconButton(ft.icons.EDIT, icon_color=ft.colors.BLUE_600, on_click=lambda e, cli=c: abrir_edicao(e, cli)),
                            ft.IconButton(ft.icons.DELETE, icon_color=ft.colors.RED_600, on_click=lambda e, cid=c.id: excluir_cliente(e, cid)),
                        ])),
                    ]
                )
            )
        page.update()

    carregar_dados()

    # --- LAYOUT FINAL ---
    return ft.Container(
        padding=30, expand=True, bgcolor=ft.colors.GREY_100,
        content=ft.Column([
            ft.Row([
                ft.Text("Gestão de Clientes", size=25, weight="bold", color=ft.colors.BLUE_GREY_900),
                ft.ElevatedButton(
                    "Novo Cliente", 
                    icon=ft.icons.ADD, 
                    bgcolor=ft.colors.BLUE_600, 
                    color="white",
                    height=45,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    on_click=abrir_novo
                )
            ], alignment="spaceBetween"),
            
            ft.Divider(color="transparent", height=20),
            
            ft.Container(
                bgcolor="white", padding=20, border_radius=10, 
                shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
                content=ft.Column([tabela], scroll=ft.ScrollMode.AUTO)
            )
        ], scroll=ft.ScrollMode.AUTO)
    )