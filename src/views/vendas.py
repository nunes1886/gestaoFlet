import flet as ft
from src.database.database import get_session, ProdutoServico, Cliente, OrdemServico, ItemOS
from datetime import datetime

def ViewNovaVenda(page):
    # --- VARIÁVEIS DE ESTADO ---
    carrinho_itens = []
    cliente_selecionado_id = None 

    # --- DADOS (Backend) ---
    session = get_session()
    lista_produtos = session.query(ProdutoServico).all()
    todos_clientes = session.query(Cliente).all() 
    session.close()

    # --- LÓGICA DE FORMATAÇÃO (ESTRATÉGIA ON BLUR) ---
    def formatar_telefone_blur(e):
        # Remove tudo que não é número
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

    def limpar_formatacao_focus(e):
        # Remove formatação para editar
        valor_limpo = "".join(filter(str.isdigit, e.control.value))
        e.control.value = valor_limpo
        e.control.update()

    # --- FUNÇÕES DE BUSCA DE CLIENTE ---
    def selecionar_cliente_lista(e, cli):
        nonlocal cliente_selecionado_id
        txt_cliente.value = cli.nome_empresa
        
        # Formata o telefone vindo do banco para ficar bonito na tela
        tel = cli.telefone or ""
        tel_limpo = "".join(filter(str.isdigit, tel))
        if len(tel_limpo) == 11:
            txt_whatsapp.value = f"({tel_limpo[:2]}) {tel_limpo[2:7]}-{tel_limpo[7:]}"
        else:
            txt_whatsapp.value = tel_limpo
            
        cliente_selecionado_id = cli.id
        lista_sugestoes.visible = False
        page.update()

    def buscar_cliente(e):
        digitado = e.control.value.lower()
        if not digitado:
            lista_sugestoes.visible = False
            page.update()
            return

        matches = [c for c in todos_clientes if digitado in c.nome_empresa.lower()]
        
        if matches:
            lista_sugestoes.controls.clear()
            for c in matches:
                # Prepara o telefone para exibição na lista
                tel_display = c.telefone
                if tel_display and len(tel_display) == 11:
                     tel_display = f"({tel_display[:2]}) {tel_display[2:7]}-{tel_display[7:]}"

                lista_sugestoes.controls.append(
                    ft.ListTile(
                        title=ft.Text(c.nome_empresa, size=14, color=ft.colors.BLACK87),
                        subtitle=ft.Text(tel_display, size=12, color=ft.colors.GREY_600),
                        on_click=lambda e, cli=c: selecionar_cliente_lista(e, cli),
                        bgcolor=ft.colors.WHITE,
                    )
                )
            lista_sugestoes.visible = True
            lista_sugestoes.height = min(len(matches) * 60, 200) 
        else:
            lista_sugestoes.visible = False
        
        page.update()
    
    # --- ELEMENTOS VISUAIS ---
    
    txt_cliente = ft.TextField(
        label="Nome do Cliente (Busca)", 
        expand=True, 
        prefix_icon=ft.icons.SEARCH,
        on_change=buscar_cliente,
        height=50, bgcolor="white", text_size=14,
        content_padding=10
    )
    
    lista_sugestoes = ft.ListView(visible=False, spacing=0, padding=0)
    container_sugestoes = ft.Container(
        content=lista_sugestoes, 
        bgcolor="white", 
        border=ft.border.all(1, ft.colors.GREY_300),
        border_radius=5,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
        width=400 
    )

    # --- CAMPO WHATSAPP BLINDADO ---
    txt_whatsapp = ft.TextField(
        label="WhatsApp", 
        expand=True,
        prefix_icon=ft.icons.PHONE, 
        height=50, bgcolor="white", text_size=14,
        content_padding=ft.padding.only(left=10, right=10, bottom=5),
        
        # Só deixa digitar números (evita cursor pulando)
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"), 
        max_length=11,
        
        # Eventos para formatar e limpar
        on_blur=formatar_telefone_blur,
        on_focus=limpar_formatacao_focus
    )
    
    dt_entrega = ft.TextField(
        label="Entrega", 
        width=150, 
        value=datetime.now().strftime("%d/%m/%Y"), 
        prefix_icon=ft.icons.CALENDAR_MONTH,
        height=50, bgcolor="white", text_size=14,
        content_padding=10
    )

    # 2. Produtos e Itens
    opcoes_produtos = [ft.dropdown.Option(key=str(p.id), text=f"{p.nome} (R$ {p.preco_venda:.2f})") for p in lista_produtos]
    
    dd_produtos = ft.Dropdown(
        label="Selecione o Produto", 
        options=opcoes_produtos, 
        expand=True, 
        height=50, bgcolor="white", text_size=14,
        content_padding=10
    )
    
    txt_largura = ft.TextField(label="Larg (m)", expand=True, value="1", height=50, bgcolor="white", text_size=14, content_padding=10)
    txt_altura = ft.TextField(label="Alt (m)", expand=True, value="1", height=50, bgcolor="white", text_size=14, content_padding=10)
    txt_qtd = ft.TextField(label="Qtd", width=80, value="1", height=50, bgcolor="white", text_size=14, content_padding=10)

    # 3. Observações e Financeiro
    txt_obs = ft.TextField(
        label="Observações da Produção (Acabamento, Ilhós, etc...)", 
        multiline=True, 
        min_lines=3, max_lines=5, 
        bgcolor="white", text_size=14
    )
    
    txt_sinal = ft.TextField(
        label="Sinal (R$)", 
        value="0.00", 
        width=150, 
        text_align="right",
        bgcolor="white",
        text_size=16,
        on_change=lambda e: atualizar_financeiro(),
        content_padding=10
    )
    
    txt_falta_pagar = ft.Text("Falta: R$ 0.00", size=18, weight="bold", color=ft.colors.RED_600)

    # Tabela
    tabela_itens = ft.DataTable(
        width=float('inf'),
        column_spacing=10,
        heading_row_height=40,
        data_row_min_height=50,
        columns=[
            ft.DataColumn(ft.Text("Produto", size=12, weight="bold")),
            ft.DataColumn(ft.Text("Medidas", size=12, weight="bold")),
            ft.DataColumn(ft.Text("Total", size=12, weight="bold")),
            ft.DataColumn(ft.Text("Excluir", size=12, weight="bold")),
        ],
        rows=[]
    )

    txt_total_final = ft.Text("R$ 0.00", size=28, weight="bold", color=ft.colors.GREEN_700)

    # --- LÓGICA ---
    def atualizar_financeiro():
        try:
            total = sum(item["total"] for item in carrinho_itens)
            sinal_str = txt_sinal.value.replace(",", ".") if txt_sinal.value else "0"
            try: sinal = float(sinal_str)
            except: sinal = 0.0
            
            falta = total - sinal
            
            txt_total_final.value = f"R$ {total:.2f}"
            txt_falta_pagar.value = f"Falta: R$ {falta:.2f}"
            
            if falta <= 0.01: 
                txt_falta_pagar.color = ft.colors.GREEN_600
                txt_falta_pagar.value = "Quitado"
            else:
                txt_falta_pagar.color = ft.colors.RED_600
                
            txt_total_final.update()
            txt_falta_pagar.update()
        except Exception as e:
            print(f"Erro financeiro: {e}")

    def adicionar_item(e):
        if not dd_produtos.value: return
        
        session = get_session()
        prod = session.query(ProdutoServico).get(int(dd_produtos.value))
        session.close()

        try:
            larg = float(txt_largura.value.replace(",", "."))
            alt = float(txt_altura.value.replace(",", "."))
            qtd = int(txt_qtd.value)
        except:
            return 
            
        total_item = larg * alt * qtd * prod.preco_venda
        
        nome_curto = prod.nome if len(prod.nome) < 20 else prod.nome[:17] + "..."
        
        carrinho_itens.append({
            "produto_id": prod.id, 
            "nome": prod.nome,
            "largura": larg,      
            "altura": alt,        
            "quantidade": qtd,    
            "preco": prod.preco_venda, 
            "total": total_item
        })
        
        idx = len(tabela_itens.rows)
        tabela_itens.rows.append(
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(nome_curto, size=12)),
                ft.DataCell(ft.Text(f"{larg}x{alt} ({qtd})", size=12)),
                ft.DataCell(ft.Text(f"R$ {total_item:.2f}", size=12)),
                ft.DataCell(ft.IconButton(ft.icons.DELETE, icon_color="red", icon_size=20, on_click=lambda e, i=idx: remover_item(e, i))),
            ])
        )
        tabela_itens.update()
        atualizar_financeiro()

    def remover_item(e, index):
        if 0 <= index < len(carrinho_itens):
            carrinho_itens.pop(index)
            tabela_itens.rows.clear()
            for i, item in enumerate(carrinho_itens):
                nome_curto = item["nome"] if len(item["nome"]) < 20 else item["nome"][:17] + "..."
                tabela_itens.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text(nome_curto, size=12)),
                        ft.DataCell(ft.Text(f"{item['largura']}x{item['altura']} ({item['quantidade']})", size=12)),
                        ft.DataCell(ft.Text(f"R$ {item['total']:.2f}", size=12)),
                        ft.DataCell(ft.IconButton(ft.icons.DELETE, icon_color="red", icon_size=20, on_click=lambda e, idx=i: remover_item(e, idx))),
                    ])
                )
            tabela_itens.update()
            atualizar_financeiro()

    def concluir_venda(e):
        nonlocal cliente_selecionado_id 
        
        if not txt_cliente.value or not carrinho_itens:
            page.snack_bar = ft.SnackBar(ft.Text("Preencha cliente e itens!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        session = get_session()
        
        # 1. Resolve Cliente
        cli_id = cliente_selecionado_id
        
        # Limpa telefone antes de salvar (garante que vai só números pro banco)
        tel_limpo = "".join(filter(str.isdigit, txt_whatsapp.value))
        
        if not cli_id:
            existente = session.query(Cliente).filter_by(nome_empresa=txt_cliente.value).first()
            if existente:
                cli_id = existente.id
            else:
                novo_cli = Cliente(nome_empresa=txt_cliente.value, telefone=tel_limpo)
                session.add(novo_cli)
                session.flush()
                cli_id = novo_cli.id
        
        # 2. Cria OS
        total = sum(item["total"] for item in carrinho_itens)
        sinal_str = txt_sinal.value.replace(",", ".") if txt_sinal.value else "0"
        try: sinal = float(sinal_str)
        except: sinal = 0.0
        
        nova_os = OrdemServico(
            cliente_id=cli_id,
            status="Fila",
            valor_total=total,
            valor_pago=sinal,
            observacoes=txt_obs.value,
            data_criacao=datetime.now()
        )
        session.add(nova_os)
        session.flush()
        
        id_salvo = nova_os.id 

        # 3. Itens
        for item in carrinho_itens:
            session.add(ItemOS(
                os_id=nova_os.id, 
                produto_id=item["produto_id"],
                descricao_item=item["nome"], 
                largura=item["largura"], 
                altura=item["altura"],
                quantidade=item["quantidade"], 
                preco_unitario=item["preco"], 
                total_item=item["total"]
            ))
        
        session.commit()
        session.close()
        
        # 4. RESET
        carrinho_itens.clear()
        tabela_itens.rows.clear()
        txt_cliente.value = ""
        txt_whatsapp.value = ""
        txt_obs.value = ""
        txt_sinal.value = "0.00"
        txt_largura.value = "1"
        txt_altura.value = "1"
        txt_qtd.value = "1"
        txt_total_final.value = "R$ 0.00"
        txt_falta_pagar.value = "Falta: R$ 0.00"
        txt_falta_pagar.color = ft.colors.RED_600
        
        cliente_selecionado_id = None
        
        page.snack_bar = ft.SnackBar(ft.Text(f"Venda #{id_salvo} Salva com Sucesso!"), bgcolor="green")
        page.snack_bar.open = True
        page.update()


    # --- MONTAGEM DO LAYOUT ---
    coluna_esquerda = ft.Column([
        ft.Text("Dados do Cliente", weight="bold", size=16, color=ft.colors.BLUE_GREY_800),
        
        ft.Column([txt_cliente, container_sugestoes], spacing=0),
        
        ft.Row([txt_whatsapp, dt_entrega], alignment=ft.MainAxisAlignment.START),
        
        ft.Divider(color="transparent", height=10),
        
        ft.Text("Adicionar Produtos", weight="bold", size=16, color=ft.colors.BLUE_GREY_800),
        dd_produtos,
        ft.Row([txt_largura, txt_altura, txt_qtd]),
        ft.ElevatedButton("Adicionar Item", on_click=adicionar_item, bgcolor=ft.colors.BLUE_600, color="white", height=45),
        ft.Divider(color="transparent", height=10),
        
        ft.Text("Detalhes da Produção", weight="bold", size=16, color=ft.colors.BLUE_GREY_800),
        txt_obs
    ], scroll=ft.ScrollMode.AUTO)

    coluna_direita = ft.Column([
        ft.Row([ft.Icon(ft.icons.SHOPPING_CART, color=ft.colors.BLUE_GREY_800), ft.Text("Resumo do Pedido", weight="bold", size=18, color=ft.colors.BLUE_GREY_800)]),
        ft.Divider(),
        ft.Container(
            content=ft.Column([tabela_itens], scroll=ft.ScrollMode.AUTO),
            border=ft.border.all(1, ft.colors.GREY_200), border_radius=8, height=250, padding=5
        ),
        ft.Divider(),
        ft.Row([ft.Text("Total Geral:", size=16), txt_total_final], alignment="spaceBetween"),
        ft.Row([txt_sinal, txt_falta_pagar], alignment="spaceBetween", vertical_alignment="center"),
        ft.Container(height=20),
        ft.Row([ft.ElevatedButton("CONCLUIR VENDA", on_click=concluir_venda, height=50, bgcolor=ft.colors.GREEN_600, color="white", expand=True, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))])
    ])

    return ft.Container(
        padding=20, bgcolor=ft.colors.GREY_100, expand=True,
        content=ft.Row([
            ft.Container(coluna_esquerda, expand=3, bgcolor="white", padding=25, border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12)),
            ft.VerticalDivider(width=20, color="transparent"),
            ft.Container(coluna_direita, expand=2, bgcolor="white", padding=25, border_radius=15, shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12))
        ], vertical_alignment=ft.CrossAxisAlignment.START)
    )