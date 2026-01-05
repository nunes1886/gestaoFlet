import flet as ft
from src.database.database import get_session, Empresa, ProdutoServico, Usuario, StatusOS, Setor, DATABASE_URL, engine
import shutil
import os
import datetime
import hashlib
try:
    from reset_banco import resetar_tudo
except ImportError:
    resetar_tudo = None

def ViewConfiguracao(page: ft.Page):
    
    # --- ESTILOS ---
    estilo_input = {
        "bgcolor": "white",
        "height": 40,
        "content_padding": 10,
        "text_size": 14,
        "border_color": ft.colors.GREY_400,
    }

    # --- HELPER: CACHE BUSTER ---
    def get_img_src(arquivo):
        if os.path.exists(arquivo):
            return f"{arquivo}?v={datetime.datetime.now().timestamp()}"
        return ""

    # --- LÓGICA DE UPLOAD ---
    txt_path_logo = ft.Text("Nenhum arquivo selecionado", size=12, color="grey", italic=True, overflow=ft.TextOverflow.ELLIPSIS)
    txt_path_icon = ft.Text("Nenhum arquivo selecionado", size=12, color="grey", italic=True, overflow=ft.TextOverflow.ELLIPSIS)

    def salvar_arquivo_upload(e: ft.FilePickerResultEvent, destino_nome):
        if e.files:
            origem = e.files[0].path
            if not os.path.exists("assets"): os.makedirs("assets")
            destino = f"assets/{destino_nome}"
            
            try:
                shutil.copy(origem, destino)
                if destino_nome == "logo.png":
                    img_logo.src = get_img_src(destino)
                    img_logo.visible = True
                    txt_path_logo.value = e.files[0].name
                else:
                    img_favicon.src = get_img_src(destino)
                    img_favicon.visible = True
                    txt_path_icon.value = e.files[0].name
                
                page.snack_bar = ft.SnackBar(ft.Text(f"{destino_nome} atualizado! Reinicie para aplicar."), bgcolor="green")
                page.snack_bar.open = True
                page.update()
            except Exception as err:
                print(err)

    picker_logo = ft.FilePicker(on_result=lambda e: salvar_arquivo_upload(e, "logo.png"))
    picker_icon = ft.FilePicker(on_result=lambda e: salvar_arquivo_upload(e, "favicon.png"))
    page.overlay.extend([picker_logo, picker_icon])

    # --- FORMATAÇÃO (MÁSCARAS) ---
    def formatar_telefone_blur(e):
        v = "".join(filter(str.isdigit, e.control.value))
        if not v: e.control.value = ""
        elif len(v) == 11: e.control.value = f"({v[:2]}) {v[2:7]}-{v[7:]}"
        elif len(v) == 10: e.control.value = f"({v[:2]}) {v[2:6]}-{v[6:]}"
        else: e.control.value = v
        e.control.update()

    def formatar_cnpj_blur(e):
        v = "".join(filter(str.isdigit, e.control.value))[:14]
        if not v: e.control.value = ""
        elif len(v) == 14: e.control.value = f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}"
        else: e.control.value = v
        e.control.update()

    def limpar_formatacao_focus(e):
        e.control.value = "".join(filter(str.isdigit, e.control.value))
        e.control.update()

    # --- GERENCIAMENTO DE STATUS (KANBAN) ---
    lista_status = ft.Column(spacing=5)
    txt_novo_status = ft.TextField(label="Novo Status", expand=True, **estilo_input)
    dd_cor_status = ft.Dropdown(
        width=100, height=40, value="blue", content_padding=5, bgcolor="white", text_size=12,
        options=[
            ft.dropdown.Option("blue", "Azul"), ft.dropdown.Option("orange", "Laranja"),
            ft.dropdown.Option("green", "Verde"), ft.dropdown.Option("red", "Vermelho"),
            ft.dropdown.Option("purple", "Roxo"), ft.dropdown.Option("amber", "Amarelo")
        ]
    )

    def carregar_status():
        lista_status.controls.clear()
        session = get_session(); todos = session.query(StatusOS).order_by(StatusOS.ordem).all(); session.close()
        for st in todos:
            lista_status.controls.append(
                ft.Container(bgcolor="white", padding=5, border_radius=5, border=ft.border.all(1, ft.colors.GREY_300),
                    content=ft.Row([
                        ft.Icon(ft.Icons.CIRCLE, color=st.cor, size=12),
                        ft.Text(st.nome, expand=True, size=12),
                        ft.IconButton(ft.Icons.CLOSE, icon_color="red", icon_size=16, on_click=lambda e, sid=st.id: deletar_status(sid))
                    ], alignment="spaceBetween")
                )
            )
        page.update()

    def adicionar_status(e):
        if not txt_novo_status.value: return
        session = get_session(); qtd = session.query(StatusOS).count()
        novo = StatusOS(nome=txt_novo_status.value, cor=dd_cor_status.value, ordem=qtd+1)
        session.add(novo); session.commit(); session.close()
        txt_novo_status.value = ""; carregar_status()

    def deletar_status(sid):
        session = get_session(); session.query(StatusOS).filter_by(id=sid).delete(); session.commit(); session.close(); carregar_status()

    # --- GERENCIAMENTO DE SETORES ---
    lista_setores = ft.Column(spacing=5)
    txt_novo_setor = ft.TextField(label="Novo Setor", expand=True, **estilo_input)

    def carregar_setores():
        lista_setores.controls.clear()
        session = get_session(); todos = session.query(Setor).all(); session.close()
        for s in todos:
            lista_setores.controls.append(
                ft.Container(bgcolor="white", padding=5, border_radius=5, border=ft.border.all(1, ft.colors.GREY_300),
                             content=ft.Row([ft.Text(s.nome, expand=True, size=12), ft.IconButton(ft.Icons.CLOSE, icon_color="red", icon_size=16, on_click=lambda e, sid=s.id: deletar_setor(sid))]))
            )
        page.update()

    def adicionar_setor(e):
        if not txt_novo_setor.value: return
        session = get_session(); session.add(Setor(nome=txt_novo_setor.value)); session.commit(); session.close()
        txt_novo_setor.value = ""; carregar_setores()

    def deletar_setor(sid):
        session = get_session(); session.query(Setor).filter_by(id=sid).delete(); session.commit(); session.close(); carregar_setores()

    # --- TABELA DE PRODUTOS ---
    tabela_produtos = ft.DataTable(
        heading_row_height=30, column_spacing=10, data_row_max_height=40,
        columns=[ft.DataColumn(ft.Text("Produto")), ft.DataColumn(ft.Text("Venda"), numeric=True), ft.DataColumn(ft.Text("Revenda"), numeric=True), ft.DataColumn(ft.Text("Ações"))],
        rows=[]
    )
    
    txt_novo_prod_nome = ft.TextField(label="Nome do Produto", expand=True, **estilo_input)
    txt_novo_prod_venda = ft.TextField(label="Venda", width=80, keyboard_type=ft.KeyboardType.NUMBER, **estilo_input)
    txt_novo_prod_revenda = ft.TextField(label="Revenda", width=80, keyboard_type=ft.KeyboardType.NUMBER, **estilo_input)

    def carregar_produtos():
        tabela_produtos.rows.clear()
        session = get_session(); prods = session.query(ProdutoServico).all(); session.close()
        for p in prods:
            tabela_produtos.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(p.nome, size=12)), ft.DataCell(ft.Text(f"{p.preco_venda:.2f}", size=12)), ft.DataCell(ft.Text(f"{p.preco_revenda:.2f}", size=12)),
                ft.DataCell(ft.IconButton(ft.Icons.DELETE, icon_color="red", icon_size=18, on_click=lambda e, pid=p.id: deletar_produto(pid)))
            ]))
        try: tabela_produtos.update()
        except: pass

    def adicionar_produto(e):
        if not txt_novo_prod_nome.value: return
        try:
            pv = float(txt_novo_prod_venda.value.replace(",", ".")) if txt_novo_prod_venda.value else 0.0
            pr = float(txt_novo_prod_revenda.value.replace(",", ".")) if txt_novo_prod_revenda.value else 0.0
            session = get_session(); session.add(ProdutoServico(nome=txt_novo_prod_nome.value, preco_venda=pv, preco_revenda=pr)); session.commit(); session.close()
            txt_novo_prod_nome.value = ""; txt_novo_prod_venda.value = ""; txt_novo_prod_revenda.value = ""; carregar_produtos()
        except: pass

    def deletar_produto(pid):
        session = get_session(); session.query(ProdutoServico).filter_by(id=pid).delete(); session.commit(); session.close(); carregar_produtos()

    # --- DADOS DA EMPRESA ---
    txt_nome_empresa = ft.TextField(label="Nome Fantasia", **estilo_input)
    txt_cnpj = ft.TextField(label="CNPJ", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"), max_length=18, on_blur=formatar_cnpj_blur, on_focus=limpar_formatacao_focus, **estilo_input)
    txt_endereco = ft.TextField(label="Endereço", **estilo_input)
    txt_telefone = ft.TextField(label="Telefone", input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"), max_length=15, on_blur=formatar_telefone_blur, on_focus=limpar_formatacao_focus, **estilo_input)
    
    # Imagens (Layout organizado: Preview + Botão e Texto)
    img_logo = ft.Image(src=get_img_src("assets/logo.png"), width=80, height=80, fit=ft.ImageFit.CONTAIN, visible=os.path.exists("assets/logo.png"))
    img_favicon = ft.Image(src=get_img_src("assets/favicon.png"), width=32, height=32, fit=ft.ImageFit.CONTAIN, visible=os.path.exists("assets/favicon.png"))

    def salvar_dados_empresa(e):
        session = get_session(); emp = session.query(Empresa).first()
        if not emp: emp = Empresa(); session.add(emp)
        emp.nome_fantasia = txt_nome_empresa.value
        emp.cnpj = "".join(filter(str.isdigit, txt_cnpj.value))
        emp.endereco = txt_endereco.value
        emp.telefone = "".join(filter(str.isdigit, txt_telefone.value))
        session.commit(); session.close()
        page.title = f"{txt_nome_empresa.value}"; page.update()
        page.snack_bar = ft.SnackBar(ft.Text("Dados Salvos!"), bgcolor="green"); page.snack_bar.open=True; page.update()

    def carregar_dados_empresa():
        session = get_session(); emp = session.query(Empresa).first(); session.close()
        if emp:
            txt_nome_empresa.value = emp.nome_fantasia
            txt_endereco.value = emp.endereco
            c_raw = emp.cnpj or ""; txt_cnpj.value = f"{c_raw[:2]}.{c_raw[2:5]}.{c_raw[5:8]}/{c_raw[8:12]}-{c_raw[12:]}" if len(c_raw) == 14 else c_raw
            t_raw = emp.telefone or ""; txt_telefone.value = f"({t_raw[:2]}) {t_raw[2:7]}-{t_raw[7:]}" if len(t_raw) == 11 else t_raw

    # --- ZONA DE RISCO ---
    def baixar_backup(e):
        nome_db = DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(nome_db):
            destino = f"backup_{datetime.date.today()}.db"
            shutil.copy(nome_db, destino)
            os.startfile(os.path.abspath(".")) 
            page.snack_bar = ft.SnackBar(ft.Text(f"Backup: {destino}"), bgcolor="green"); page.snack_bar.open=True; page.update()

    def restaurar_backup_pick(e: ft.FilePickerResultEvent):
        if e.files and e.files[0].path:
            engine.dispose()
            try:
                shutil.copy(e.files[0].path, DATABASE_URL.replace("sqlite:///", ""))
                page.snack_bar = ft.SnackBar(ft.Text("Backup Restaurado! Fechando..."), bgcolor="green"); page.snack_bar.open=True; page.update()
                import time; time.sleep(2); page.window_close()
            except Exception as err:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro: {err}"), bgcolor="red"); page.snack_bar.open=True; page.update()

    fp_restore = ft.FilePicker(on_result=restaurar_backup_pick)
    page.overlay.append(fp_restore)
    
    txt_senha_reset = ft.TextField(label="Senha Admin", password=True, **estilo_input)
    def confirmar_reset(e):
        if not txt_senha_reset.value: return
        session = get_session(); admin = session.query(Usuario).filter_by(usuario="admin").first()
        hash_s = hashlib.sha256(txt_senha_reset.value.encode()).hexdigest()
        if admin and admin.senha_hash == hash_s:
            if resetar_tudo:
                session.close(); page.close(dlg_reset); resetar_tudo()
                page.snack_bar = ft.SnackBar(ft.Text("Resetado!"), bgcolor="green"); page.snack_bar.open=True; page.update()
            else:
                 page.snack_bar = ft.SnackBar(ft.Text("Script de reset não encontrado."), bgcolor="red"); page.snack_bar.open=True; page.update()
        else: session.close(); page.snack_bar = ft.SnackBar(ft.Text("Senha Errada!"), bgcolor="red"); page.snack_bar.open=True; page.update()
    
    dlg_reset = ft.AlertDialog(title=ft.Text("RESET TOTAL"), content=txt_senha_reset, actions=[ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_reset)), ft.ElevatedButton("CONFIRMAR", bgcolor="red", color="white", on_click=confirmar_reset)])

    # INICIALIZAÇÃO
    carregar_dados_empresa(); carregar_produtos(); carregar_status(); carregar_setores()

    # --- MONTAGEM DO LAYOUT ORGANIZADO ---
    
    # 1. Coluna Esquerda: Empresa + Zona de Risco
    coluna_esquerda = ft.Column([
        # CARD DADOS DA EMPRESA
        ft.Container(bgcolor="white", padding=20, border_radius=10, shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.BLACK12), content=ft.Column([
            ft.Text("Dados da Empresa", weight="bold", size=16, color=ft.colors.BLUE_GREY_800),
            ft.Divider(height=10, color="transparent"),
            txt_nome_empresa,
            txt_cnpj,
            txt_endereco,
            ft.Row([txt_cep_fake := ft.TextField(label="CEP", width=120, **estilo_input), txt_telefone], spacing=10), # Adicionei CEP visual só pra bater com layout se quiser
            
            ft.Divider(),
            ft.Text("Identidade Visual", weight="bold", size=14, color=ft.colors.BLUE_GREY_800),
            ft.Container(height=5),
            
            # LOGO ORGANIZADA
            ft.Row([
                ft.Container(content=img_logo, border=ft.border.all(1, ft.colors.GREY_300), border_radius=5, padding=5),
                ft.Column([
                    ft.Text("Alterar Logo:", size=12, weight="bold"),
                    ft.Row([
                        ft.ElevatedButton("Escolher arquivo", on_click=lambda _: picker_logo.pick_files(), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5), bgcolor=ft.colors.GREY_200, color="black"), height=30),
                        ft.Container(width=150, content=txt_path_logo) # Limita largura do texto
                    ])
                ], spacing=2)
            ]),
            
            ft.Container(height=10),
            
            # FAVICON ORGANIZADO
            ft.Row([
                ft.Container(content=img_favicon, border=ft.border.all(1, ft.colors.GREY_300), border_radius=5, padding=5, width=40, height=40, alignment=ft.alignment.center),
                ft.Column([
                    ft.Text("Alterar Favicon:", size=12, weight="bold"),
                    ft.Row([
                        ft.ElevatedButton("Escolher arquivo", on_click=lambda _: picker_icon.pick_files(), style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5), bgcolor=ft.colors.GREY_200, color="black"), height=30),
                        ft.Container(width=150, content=txt_path_icon)
                    ])
                ], spacing=2)
            ]),

            ft.Container(height=15),
            ft.ElevatedButton("SALVAR DADOS", bgcolor=ft.colors.BLUE_600, color="white", width=float('inf'), height=45, on_click=salvar_dados_empresa)
        ])),

        # CARD ZONA DE RISCO
        ft.Container(bgcolor="#FFF0F0", padding=20, border_radius=10, border=ft.border.all(1, ft.colors.RED_200), content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.WARNING, color="red"), ft.Text("Zona de Risco", weight="bold", color="red")]),
            ft.Divider(),
            ft.OutlinedButton("Baixar Backup do Sistema", icon=ft.Icons.DOWNLOAD, style=ft.ButtonStyle(color=ft.colors.BLUE_900), width=float('inf'), on_click=baixar_backup),
            ft.Container(height=5),
            ft.Text("Restaurar Backup (.db):", size=12),
            ft.Row([
                ft.ElevatedButton("Escolher arquivo", on_click=lambda _: fp_restore.pick_files(), style=ft.ButtonStyle(bgcolor=ft.colors.AMBER_600, color="white"), height=35),
                ft.Text("Nenhum arquivo", size=11, color="grey")
            ]),
            ft.Divider(),
            ft.Text("Reset de Fábrica:", size=12, color="red"),
            ft.Row([
                txt_senha_reset,
                ft.ElevatedButton("Zerar Tudo", bgcolor="red", color="white", on_click=lambda e: page.open(dlg_reset), height=40)
            ])
        ]))
    ])

    # 2. Coluna Direita: Produtos + Setores/Status
    coluna_direita = ft.Column([
        # CARD PRODUTOS
        ft.Container(bgcolor="white", padding=20, border_radius=10, shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.BLACK12), content=ft.Column([
            ft.Container(bgcolor=ft.colors.GREEN_600, padding=10, border_radius=5, content=ft.Text("Produtos & Serviços", color="white", weight="bold")),
            ft.Container(height=5),
            ft.Row([txt_novo_prod_nome, txt_novo_prod_venda, txt_novo_prod_revenda, ft.Container(content=ft.IconButton(ft.Icons.ADD, icon_color="white", on_click=adicionar_produto), bgcolor="green", border_radius=5, width=40, height=40)]),
            ft.Container(content=ft.Column([tabela_produtos], scroll=ft.ScrollMode.AUTO), height=250, border=ft.border.all(1, ft.colors.GREY_100), border_radius=5)
        ])),

        # ROW COM SETORES E STATUS
        ft.Row([
            # CARD SETORES
            ft.Container(bgcolor="white", padding=15, border_radius=10, shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.BLACK12), expand=1, content=ft.Column([
                ft.Container(bgcolor=ft.colors.CYAN_600, padding=5, border_radius=5, alignment=ft.alignment.center, content=ft.Text("Setores", color="white", weight="bold")),
                ft.Row([txt_novo_setor, ft.Container(content=ft.IconButton(ft.Icons.ADD, icon_color="white", icon_size=18, on_click=adicionar_setor), bgcolor="cyan", border_radius=5, width=40, height=40)]),
                ft.Container(content=ft.Column([lista_setores], scroll=ft.ScrollMode.AUTO), height=200)
            ])),
            # CARD STATUS
            ft.Container(bgcolor="white", padding=15, border_radius=10, shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.BLACK12), expand=1, content=ft.Column([
                ft.Container(bgcolor=ft.colors.AMBER_700, padding=5, border_radius=5, alignment=ft.alignment.center, content=ft.Text("Status (Kanban)", color="white", weight="bold")),
                ft.Row([txt_novo_status, ft.Container(content=ft.IconButton(ft.Icons.ADD, icon_color="white", icon_size=18, on_click=adicionar_status), bgcolor="orange", border_radius=5, width=40, height=40)]),
                dd_cor_status,
                ft.Container(content=ft.Column([lista_status], scroll=ft.ScrollMode.AUTO), height=150)
            ]))
        ], vertical_alignment=ft.CrossAxisAlignment.START)
    ])

    return ft.Container(
        padding=20, bgcolor=ft.Colors.GREY_100, expand=True,
        content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.SETTINGS, size=24), ft.Text("Configurações do Sistema", size=24, weight="bold", color=ft.colors.BLUE_GREY_900)]),
            ft.Container(height=10),
            ft.Row([
                ft.Container(coluna_esquerda, expand=4), # 40% da tela
                ft.Container(coluna_direita, expand=6)   # 60% da tela
            ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=20)
        ], scroll=ft.ScrollMode.AUTO)
    )