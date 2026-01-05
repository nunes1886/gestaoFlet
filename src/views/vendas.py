import flet as ft
from src.database.database import get_session, ProdutoServico, Cliente, OrdemServico, ItemOS
from datetime import datetime, timedelta
from PIL import ImageGrab 
import os
import time
import shutil
from src.utils.gerar_pdf import gerar_pdf_venda 

def ViewNovaVenda(page):
    # --- VARIÁVEIS DE ESTADO ---
    carrinho_itens = []
    cliente_selecionado_id = None 
    caminho_imagem_temp = None 

    session = get_session()
    lista_produtos = session.query(ProdutoServico).all()
    todos_clientes = session.query(Cliente).all() 
    session.close()

    # --- ESTILOS VISUAIS ---
    COR_PRIMARIA = ft.colors.BLUE_800
    COR_SECUNDARIA = ft.colors.BLUE_600
    COR_FUNDO = ft.colors.GREY_100

    def criar_titulo_secao(texto, icone):
        return ft.Row([
            ft.Icon(icone, color=COR_PRIMARIA),
            ft.Text(texto, weight="bold", size=16, color=ft.colors.BLUE_GREY_800)
        ], alignment="start")

    # --- LÓGICA DE MÁSCARA (WHATSAPP) ---
    def formatar_telefone(e):
        valor = e.control.value
        # Remove tudo que não é dígito
        apenas_numeros = "".join(filter(str.isdigit, valor))
        
        # Limita a 11 dígitos (DDD + 9 + 8 números)
        apenas_numeros = apenas_numeros[:11]
        
        novo_valor = ""
        if len(apenas_numeros) > 0:
            novo_valor += f"({apenas_numeros[:2]}"
        if len(apenas_numeros) > 2:
            novo_valor += f") {apenas_numeros[2:7]}"
        if len(apenas_numeros) > 7:
            novo_valor += f"-{apenas_numeros[7:]}"
            
        e.control.value = novo_valor
        e.control.update()

    # --- LÓGICA DE IMAGEM ---
    def colar_imagem_clipboard(e):
        nonlocal caminho_imagem_temp
        try:
            imagem = ImageGrab.grabclipboard()
            if imagem:
                if not os.path.exists("temp_img"): os.makedirs("temp_img")
                if isinstance(imagem, list): return # Proteção contra arquivos múltiplos
                nome_arq = f"temp_img/temp_{int(time.time())}.png"
                imagem.save(nome_arq)
                caminho_imagem_temp = nome_arq
                
                img_preview.src = os.path.abspath(nome_arq)
                img_preview.visible = True
                texto_img_placeholder.visible = False
                container_img.border = ft.border.all(2, ft.colors.GREEN_400)
                page.update()
                
                page.snack_bar = ft.SnackBar(ft.Text("Imagem anexada com sucesso!"), bgcolor="green"); page.snack_bar.open=True; page.update()
        except: pass

    def limpar_imagem(e):
        nonlocal caminho_imagem_temp
        caminho_imagem_temp = None
        img_preview.src = ""
        img_preview.visible = False
        texto_img_placeholder.visible = True
        container_img.border = ft.border.all(1, ft.colors.GREY_300)
        page.update()

    # Componentes de Imagem
    img_preview = ft.Image(src="", width=150, height=150, fit=ft.ImageFit.CONTAIN, visible=False, border_radius=8)
    texto_img_placeholder = ft.Column([
        ft.Icon(ft.Icons.IMAGE_SEARCH, size=40, color=ft.colors.GREY_400),
        ft.Text("Cole sua arte aqui\n(Ctrl+V)", text_align="center", color=ft.colors.GREY_500, size=12)
    ], alignment="center", horizontal_alignment="center")
    
    container_img = ft.Container(
        content=ft.Stack([texto_img_placeholder, img_preview], alignment=ft.alignment.center),
        width=160, height=160,
        border=ft.border.all(1, ft.colors.GREY_300),
        border_radius=10,
        bgcolor=ft.colors.GREY_50,
        alignment=ft.alignment.center,
        on_click=colar_imagem_clipboard, # Clicar também cola
        tooltip="Clique para colar ou use Ctrl+V"
    )
    
    btn_limpar_img = ft.IconButton(icon=ft.Icons.DELETE, icon_color="red", tooltip="Remover imagem", on_click=limpar_imagem)

    # --- CLIENTE ---
    def buscar_cliente(e):
        digitado = e.control.value.lower()
        if not digitado: lista_sugestoes.visible = False; page.update(); return
        matches = [c for c in todos_clientes if digitado in c.nome_empresa.lower()]
        
        lista_sugestoes.controls.clear()
        if matches:
            for c in matches:
                sufixo = " (Revenda)" if c.is_revenda else ""
                lista_sugestoes.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.PERSON, color=COR_SECUNDARIA),
                        title=ft.Text(f"{c.nome_empresa}{sufixo}", weight="bold"),
                        subtitle=ft.Text(c.telefone or "Sem telefone"),
                        on_click=lambda e, cli=c: selecionar_cliente_lista(e, cli),
                        bgcolor=ft.colors.WHITE,
                    )
                )
            lista_sugestoes.visible = True
            lista_sugestoes.height = min(len(matches) * 70, 250) 
        else:
            lista_sugestoes.visible = False
        page.update()

    def selecionar_cliente_lista(e, cli):
        nonlocal cliente_selecionado_id
        txt_cliente.value = cli.nome_empresa
        txt_whatsapp.value = cli.telefone or ""
        
        # --- CORREÇÃO DO ERRO ---
        # Aplica formatação visual se já tiver numero
        if txt_whatsapp.value:
            # Passamos o próprio controle txt_whatsapp dentro do evento simulado
            class MockEvent: 
                control = txt_whatsapp
            
            formatar_telefone(MockEvent())
        # ------------------------
            
        cliente_selecionado_id = cli.id
        lista_sugestoes.visible = False
        if cli.is_revenda:
            page.snack_bar = ft.SnackBar(ft.Text("Cliente Revenda selecionado! Preços ajustados."), bgcolor="blue"); page.snack_bar.open = True
        page.update()

    txt_cliente = ft.TextField(label="Buscar Cliente", text_size=14, expand=True, prefix_icon=ft.Icons.SEARCH, on_change=buscar_cliente, height=45, bgcolor="white", border_radius=8)
    lista_sugestoes = ft.ListView(visible=False, spacing=0, padding=0)
    container_sugestoes = ft.Container(content=lista_sugestoes, bgcolor="white", border=ft.border.all(1, ft.colors.GREY_200), border_radius=8, shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12))
    
    # Campo Whatsapp com formatação
    txt_whatsapp = ft.TextField(label="WhatsApp", expand=True, prefix_icon=ft.Icons.PHONE, height=45, text_size=14, bgcolor="white", border_radius=8, on_change=formatar_telefone, max_length=15)
    
    # DATA DE ENTREGA
    data_padrao = (datetime.now() + timedelta(days=2)).strftime("%d/%m/%Y")
    dt_entrega = ft.TextField(label="Entrega", width=140, value=data_padrao, prefix_icon=ft.Icons.CALENDAR_MONTH, height=45, text_size=14, bgcolor="white", border_radius=8)
    
    # CHECKBOX URGÊNCIA
    chk_urgente = ft.Checkbox(label="URGENTE", value=False, label_style=ft.TextStyle(color="red", weight="bold"))

    # --- PRODUTOS ---
    opcoes_produtos = [ft.dropdown.Option(key=str(p.id), text=f"{p.nome} (V: {p.preco_venda:.2f} | R: {p.preco_revenda:.2f})") for p in lista_produtos]
    dd_produtos = ft.Dropdown(label="Selecione o Produto", options=opcoes_produtos, expand=True, height=45, text_size=14, bgcolor="white", border_radius=8)
    
    txt_largura = ft.TextField(label="Larg (m)", expand=True, value="1", height=45, bgcolor="white", border_radius=8, text_align="center")
    txt_altura = ft.TextField(label="Alt (m)", expand=True, value="1", height=45, bgcolor="white", border_radius=8, text_align="center")
    txt_qtd = ft.TextField(label="Qtd", width=80, value="1", height=45, bgcolor="white", border_radius=8, text_align="center")
    
    txt_motivo = ft.TextField(label="Nome do Arquivo / Motivo", hint_text="Ex: Banner Promoção", bgcolor="white", border_radius=8, prefix_icon=ft.Icons.DESCRIPTION, height=45)
    txt_obs = ft.TextField(label="Observações de Produção", multiline=True, min_lines=3, bgcolor="white", border_radius=8, text_size=13)
    
    txt_sinal = ft.TextField(label="Sinal (R$)", value="0.00", width=150, text_align="right", bgcolor="white", border_radius=8, on_change=lambda e: atualizar_financeiro(), text_style=ft.TextStyle(weight="bold", color=ft.colors.BLUE_900))
    txt_falta_pagar = ft.Text("Falta: R$ 0.00", size=16, weight="bold", color=ft.colors.RED_600)
    
    tabela_itens = ft.DataTable(
        width=float('inf'), heading_row_height=40, column_spacing=10,
        heading_row_color=ft.colors.BLUE_50,
        columns=[ft.DataColumn(ft.Text("Prod")), ft.DataColumn(ft.Text("Medidas")), ft.DataColumn(ft.Text("Total")), ft.DataColumn(ft.Text("Del"))], rows=[]
    )
    txt_total_final = ft.Text("R$ 0.00", size=30, weight="bold", color=ft.colors.GREEN_700)

    # --- FUNÇÕES LÓGICAS ---
    def atualizar_financeiro():
        try:
            total = sum(item["total"] for item in carrinho_itens)
            sinal_str = txt_sinal.value.replace("R$", "").strip()
            sinal = float(sinal_str.replace(",", ".")) if sinal_str else 0.0
            falta = total - sinal
            txt_total_final.value = f"R$ {total:.2f}"
            txt_falta_pagar.value = f"Falta: R$ {falta:.2f}"
            txt_falta_pagar.color = ft.colors.GREEN_600 if falta <= 0.01 else ft.colors.RED_600
            page.update()
        except: pass

    def adicionar_item(e):
        if not dd_produtos.value: return
        if not cliente_selecionado_id:
             page.snack_bar = ft.SnackBar(ft.Text("Selecione um Cliente PRIMEIRO!"), bgcolor="red"); page.snack_bar.open = True; page.update(); return

        session = get_session()
        prod = session.query(ProdutoServico).get(int(dd_produtos.value))
        cliente = session.query(Cliente).get(cliente_selecionado_id)
        preco_usado = prod.preco_revenda if cliente.is_revenda else prod.preco_venda
        tag_preco = " (Rev)" if cliente.is_revenda else ""
        session.close()

        try:
            larg = float(txt_largura.value.replace(",", "."))
            alt = float(txt_altura.value.replace(",", "."))
            qtd = int(txt_qtd.value)
        except: return 
        
        total_item = larg * alt * qtd * preco_usado
        carrinho_itens.append({"id": prod.id, "nome": f"{prod.nome}{tag_preco}", "l": larg, "a": alt, "q": qtd, "p": preco_usado, "total": total_item})
        reconstruir_tabela()

    def remover_item(e, idx):
        carrinho_itens.pop(idx); reconstruir_tabela()

    def reconstruir_tabela():
        tabela_itens.rows.clear()
        for i, item in enumerate(carrinho_itens):
            tabela_itens.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(item["nome"][:15], size=12)), 
                ft.DataCell(ft.Text(f"{item['l']}x{item['a']} ({item['q']})", size=12)), 
                ft.DataCell(ft.Text(f"{item['total']:.2f}", size=12, weight="bold")),
                ft.DataCell(ft.IconButton(ft.Icons.DELETE, icon_color="red", icon_size=20, on_click=lambda e, idx=i: remover_item(e, idx)))
            ]))
        page.update(); atualizar_financeiro()

    def resetar_tela():
        nonlocal cliente_selecionado_id
        carrinho_itens.clear(); cliente_selecionado_id = None
        txt_cliente.value = ""; txt_whatsapp.value = ""; txt_motivo.value = ""; txt_obs.value = ""; txt_sinal.value = "0.00"
        dd_produtos.value = None; txt_largura.value = "1"; txt_altura.value = "1"; txt_qtd.value = "1"
        txt_total_final.value = "R$ 0.00"; txt_falta_pagar.value = "Falta: R$ 0.00"
        tabela_itens.rows.clear(); limpar_imagem(None)
        dt_entrega.value = (datetime.now() + timedelta(days=2)).strftime("%d/%m/%Y")
        chk_urgente.value = False
        page.update()

    def concluir_venda(e):
        nonlocal cliente_selecionado_id, caminho_imagem_temp
        if not txt_cliente.value or not carrinho_itens:
            page.snack_bar = ft.SnackBar(ft.Text("Preencha cliente e adicione produtos!"), bgcolor="red"); page.snack_bar.open=True; page.update(); return

        session = get_session()
        cli_id = cliente_selecionado_id
        if not cli_id: # Cria cliente novo se não selecionou da lista
            existente = session.query(Cliente).filter_by(nome_empresa=txt_cliente.value).first()
            if existente: cli_id = existente.id
            else:
                tel_limpo = "".join(filter(str.isdigit, txt_whatsapp.value))
                novo = Cliente(nome_empresa=txt_cliente.value, telefone=tel_limpo, is_revenda=False)
                session.add(novo); session.flush(); cli_id = novo.id
        
        sinal_str = txt_sinal.value.replace("R$", "").strip()
        sinal = float(sinal_str.replace(",", ".")) if sinal_str else 0.0
        total = sum(i["total"] for i in carrinho_itens)
        
        caminho_final = None
        if caminho_imagem_temp:
            if not os.path.exists("assets/os_images"): os.makedirs("assets/os_images")
            nome_final = f"assets/os_images/os_{int(time.time())}.png"
            shutil.copy(caminho_imagem_temp, nome_final)
            caminho_final = nome_final
        
        nova_os = OrdemServico(
            cliente_id=cli_id, status="Fila", valor_total=total, valor_pago=sinal, 
            motivo=txt_motivo.value, observacoes=txt_obs.value, imagem_os=caminho_final, 
            data_criacao=datetime.now(),
            data_entrega=dt_entrega.value,
            is_urgente=chk_urgente.value
        )
        session.add(nova_os); session.flush()
        for item in carrinho_itens:
            session.add(ItemOS(os_id=nova_os.id, produto_id=item["id"], descricao_item=item["nome"], largura=item["l"], altura=item["a"], quantidade=item["q"], preco_unitario=item["p"], total_item=item["total"]))
        
        session.commit(); session.refresh(nova_os)
        try:
            gerar_pdf_venda(nova_os)
            mensagem = f"Venda #{nova_os.id} realizada! PDF Gerado."
            cor_msg = ft.colors.GREEN
        except Exception as err:
            mensagem = f"Venda salva, mas erro no PDF: {err}"; cor_msg = ft.colors.ORANGE

        session.close() 
        if caminho_imagem_temp: 
            try: os.remove(caminho_imagem_temp)
            except: pass
        resetar_tela()
        page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=cor_msg); page.snack_bar.open=True; page.update()

    # --- MONTAGEM DOS CARDS (GRID LAYOUT) ---
    
    # 1. CARD CLIENTE
    card_cliente = ft.Container(
        padding=15, bgcolor="white", border_radius=12, shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
        content=ft.Column([
            criar_titulo_secao("Dados do Cliente", ft.Icons.PERSON),
            ft.Divider(color="transparent", height=5),
            txt_cliente,
            # Container de sugestões flutuante (gambiarra visual)
            ft.Column([container_sugestoes], spacing=0),
            ft.Row([txt_whatsapp, dt_entrega]),
        ])
    )

    # 2. CARD PRODUTO
    card_produto = ft.Container(
        padding=15, bgcolor="white", border_radius=12, shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
        content=ft.Column([
            criar_titulo_secao("Adicionar Produtos", ft.Icons.SHOPPING_BAG),
            ft.Divider(color="transparent", height=5),
            dd_produtos,
            ft.Row([txt_largura, txt_altura, txt_qtd]),
            ft.ElevatedButton("ADICIONAR ITEM", icon=ft.Icons.ADD, width=float('inf'), style=ft.ButtonStyle(bgcolor=COR_SECUNDARIA, color="white", shape=ft.RoundedRectangleBorder(radius=8)), on_click=adicionar_item)
        ])
    )

    # 3. CARD DETALHES (IMAGEM + OBS)
    card_detalhes = ft.Container(
        padding=15, bgcolor="white", border_radius=12, shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
        content=ft.Column([
            criar_titulo_secao("Detalhes & Arte", ft.Icons.IMAGE),
            ft.Divider(color="transparent", height=5),
            ft.Row([
                container_img, # Área da imagem
                ft.Column([
                    txt_motivo,
                    txt_obs,
                    ft.Row([chk_urgente, btn_limpar_img], alignment="spaceBetween")
                ], expand=True)
            ], alignment="start", vertical_alignment="start")
        ])
    )

    # 4. COLUNA DA DIREITA (RESUMO + PAGAMENTO)
    coluna_direita = ft.Container(
        padding=20, bgcolor="white", border_radius=12, shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.BLACK12),
        expand=True,
        content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.RECEIPT_LONG, color=COR_PRIMARIA), ft.Text("Resumo do Pedido", size=20, weight="bold", color=ft.colors.BLUE_GREY_900)]),
            ft.Divider(),
            ft.Container(
                content=ft.Column([tabela_itens], scroll=ft.ScrollMode.AUTO),
                height=300, 
                border=ft.border.all(1, ft.colors.GREY_100), border_radius=8, bgcolor=ft.colors.GREY_50
            ),
            ft.Divider(),
            ft.Row([ft.Text("TOTAL:", weight="bold", size=16), txt_total_final], alignment="spaceBetween"),
            ft.Row([
                ft.Text("Sinal Pago:", size=14, color=ft.colors.GREY_700), 
                txt_sinal
            ], alignment="spaceBetween", vertical_alignment="center"),
            ft.Container(height=10),
            
            ft.Container(
                content=txt_falta_pagar, 
                alignment=ft.alignment.center, # Alinhamento corrigido
                bgcolor=ft.colors.GREY_100, padding=10, border_radius=8
            ),
            
            ft.Container(height=10),
            ft.ElevatedButton(
                "CONCLUIR VENDA", 
                on_click=concluir_venda, 
                height=60, 
                width=float('inf'),
                style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_600, color="white", shape=ft.RoundedRectangleBorder(radius=10), elevation=5),
                content=ft.Row([ft.Icon(ft.Icons.CHECK, size=30), ft.Text("FINALIZAR", size=18, weight="bold")], alignment="center")
            )
        ], scroll=ft.ScrollMode.AUTO) # Scroll adicionado aqui!
    )

    # --- LAYOUT FINAL ORGANIZADO ---
    coluna_esquerda = ft.Column([
        card_cliente,
        ft.Container(height=5),
        card_produto,
        ft.Container(height=5),
        card_detalhes
    ], spacing=15, scroll=ft.ScrollMode.AUTO)

    return ft.Container(
        padding=20, 
        bgcolor=COR_FUNDO, 
        expand=True,
        content=ft.Row([
            ft.Container(coluna_esquerda, expand=3), # 60% da tela
            ft.Container(width=20), # Espaçamento
            ft.Container(coluna_direita, expand=2)   # 40% da tela
        ], vertical_alignment="start", spacing=0)
    )