import flet as ft

class Sidebar(ft.Container):
    def __init__(self, page):
        super().__init__()
        self.page = page
        # Configurações visuais da barra lateral
        self.width = 250
        self.bgcolor = ft.colors.BLUE_GREY_900 
        self.padding = 20
        self.content = self.build_content()

    def build_content(self):
        return ft.Column(
            controls=[
                # --- CABEÇALHO DO MENU (Logo/Título) ---
                ft.Row(
                    [
                        ft.Icon(ft.icons.DASHBOARD, color=ft.colors.BLUE_400, size=30), # Ícone seguro
                        ft.Text("GestãoPro", size=22, weight="bold", color=ft.colors.WHITE)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Divider(height=20, color=ft.colors.TRANSPARENT),
                
                # --- BOTÕES DE NAVEGAÇÃO (Ícones corrigidos para v0.25.2) ---
                self.criar_botao("Dashboard", ft.icons.DASHBOARD, ativo=True),
                self.criar_botao("Nova Venda", ft.icons.SHOPPING_CART), # Corrigido
                self.criar_botao("Clientes", ft.icons.PEOPLE),          # Corrigido
                self.criar_botao("Produção", ft.icons.BUILD),           # Corrigido (era Construction)
                self.criar_botao("Estoque", ft.icons.STORE),            # Corrigido (era Inventory)
                self.criar_botao("Financeiro", ft.icons.ATTACH_MONEY),
                
                ft.Divider(height=20, color=ft.colors.GREY_800),
                
                # --- RODAPÉ DO MENU ---
                self.criar_botao("Configurações", ft.icons.SETTINGS),   # Corrigido
                self.criar_botao("Sair", ft.icons.EXIT_TO_APP, color=ft.colors.RED_400, on_click_action=self.logout),
            ]
        )

    def criar_botao(self, texto, icone, ativo=False, color=ft.colors.WHITE, on_click_action=None):
        """ Cria um botão padronizado do menu com efeito de hover """
        
        # Se não passar uma função específica, usa um print genérico
        action = on_click_action if on_click_action else lambda e: print(f"Navegar para: {texto}")

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icone, color=color if not ativo else ft.colors.BLUE_400),
                    ft.Text(texto, color=color if not ativo else ft.colors.BLUE_400, size=16, weight="bold" if ativo else "normal")
                ]
            ),
            padding=ft.padding.only(left=10, top=15, bottom=15),
            border_radius=10,
            bgcolor=ft.colors.BLUE_GREY_800 if ativo else None, 
            
            # Efeitos e interatividade
            on_hover=lambda e: self.highlight_botao(e.control, e.data),
            ink=True, 
            on_click=action
        )

    def highlight_botao(self, container, is_hovered):
        """ Muda a cor do botão quando o mouse passa por cima """
        if is_hovered == "true":
            if container.bgcolor != ft.colors.BLUE_GREY_800:
                container.bgcolor = ft.colors.BLUE_GREY_700
        else:
            if container.content.controls[1].weight != "bold": 
                container.bgcolor = None
        container.update()

    def logout(self, e):
        print("Saindo do sistema...")
        # Aqui futuramente chamaremos uma função para voltar à tela de login