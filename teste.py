import flet as ft

def main(page: ft.Page):
    page.title = "Teste de Vida"
    page.add(ft.Text("Se você está lendo isso, o Flet está funcionando!", size=30))
    page.update()

ft.app(target=main)