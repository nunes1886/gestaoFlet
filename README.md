# 🟦 GestãoPro - Sistema para Gráficas

Sistema de gestão desktop desenvolvido em **Python** e **Flet**, focado no controle de pequenas gráficas e comunicação visual.

## 🚀 Tecnologias Usadas

- **Linguagem:** Python 3.10+
- **Interface:** Flet
- **Banco de Dados:** SQLite (SQLAlchemy)
- **Relatórios:** FPDF2
- **Build:** PyInstaller

## ✨ Funcionalidades

- **🖥️ Dashboard:** Visão geral com gráficos e métricas.
- **🛒 Vendas:** Orçamentos, busca de clientes e geração de PDF automático.
- **💬 Chat Interno:** Comunicação em tempo real entre setores (sem internet).
- **🏭 Produção:** Kanban interativo (Fila, Impressão, Acabamento, Entregue).
- **🎨 Criação:** Fluxo exclusivo para designers e aprovação de artes.
- **📂 Auditoria:** Correção de lançamentos financeiros e "Arquivo Morto".
- **📦 Estoque:** Controle de entrada e saída de materiais.

## 🔐 Acesso Padrão (Primeiro Acesso)

Se o banco de dados for resetado, o usuário mestre é:

- **Usuário:** `admin`
- **Senha:** `admin`

---

## 📦 Como rodar este projeto (Desenvolvimento)

1. **Clonar o repositório**
   ```bash
   git clone [https://github.com/nunes1886/gestaoFlet.git](https://github.com/nunes1886/gestaoFlet.git)
   cd gestaoFlet
   ```
2. **Criar ambiente virtual e instalar dependências**

python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

3. **Executar**

python main.py

4. **Como Gerar o Executável (Build)**
pyinstaller --name GestaoPro --noconsole --icon=assets/favicon.png --add-data "assets;assets" main.py

5.**⚠️ Pós-Build (Obrigatório)**

O PyInstaller cria a pasta dist/GestaoPro. Para o sistema funcionar, você deve manualmente:

Copiar o arquivo de banco de dados (gestaopro_2026.db) para dentro da pasta.

Criar as seguintes pastas vazias dentro da pasta do executável:

📁 os_pdfs

📁 relatorios

📁 temp_img

Verificar se a pasta assets contém logo.png e favicon.png
