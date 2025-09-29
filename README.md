📧 Classificador Inteligente de Emails e Documentos com Gemini
Este projeto é um classificador web desenvolvido em Python (Flask) que utiliza a inteligência artificial do Google Gemini para categorizar conteúdos (emails, documentos de texto, PDFs) como "PRODUTIVO" ou "IMPRODUTIVO" e gerar respostas sugeridas automaticamente.

O grande diferencial é o painel de administração protegido, que permite que o administrador altere o System Prompt da IA, adaptando o comportamento do classificador a diferentes regras de negócio sem tocar no código.

✨ Funcionalidades
Classificação Inteligente: Determina se um documento ou email exige acompanhamento (PRODUTIVO) ou pode ser arquivado (IMPRODUTIVO).

Processamento Unificado: Aceita entrada via texto colado ou upload de arquivos nos formatos PDF, DOCX e TXT.

Geração de Resposta: Sugere uma resposta profissional e proativa baseada na classificação e no conteúdo original.

Painel de Administração: Permite editar o System Prompt do Gemini para reconfigurar as regras de classificação da IA, protegido por login.

Design Responsivo: Interface web construída com Tailwind CSS para uma experiência otimizada em desktop e mobile.

🛠️ Tecnologias Utilizadas
Backend: Python 3.x, Flask

IA/LLM: Google Gemini API (gemini-2.5-flash)

Front-end: HTML e Tailwind CSS

Parsing de Documentos: PyPDF2 (para PDFs) e python-docx (para DOCX)

⚙️ Pré-requisitos
Para rodar este projeto, você precisará:

Python 3.x (Recomendado 3.8+) instalado em sua máquina.

Uma Chave de API do Google Gemini (Você pode obtê-la no Google AI Studio).

🚀 Como Executar Localmente
Siga os passos abaixo para configurar e iniciar o servidor Flask em seu ambiente:

1. Preparação do Ambiente
Crie e ative um ambiente virtual Python (opcional, mas recomendado):

# Cria o ambiente virtual
python3 -m venv venv

# Ativa o ambiente virtual (Linux/macOS)
source venv/bin/activate

# Ativa o ambiente virtual (Windows)
venv\Scripts\activate

2. Instalação das Dependências
Instale todas as bibliotecas Python necessárias:

pip install flask python-dotenv google-genai PyPDF2 python-docx

3. Configuração da Chave de API
Crie um arquivo chamado .env na raiz do seu projeto e adicione sua chave de API do Gemini:

# .env file
GEMINI_API_KEY="SUA_CHAVE_DO_GEMINI_AQUI"
SECRET_KEY="SUA_CHAVE_SECRETA_PARA_SESSAO"

4. Estrutura de Arquivos
Certifique-se de que a estrutura de arquivos do seu projeto esteja correta:

.
├── app.py
├── .env
├── prompt_config.json (Criado automaticamente)
└── templates/
    ├── index.html
    ├── login.html
    └── admin.html

(Os arquivos index.html, login.html, e admin.html devem ser colocados na pasta templates/.)

5. Iniciar o Servidor
Execute o script principal:

python app.py

O servidor será iniciado. Abra seu navegador e acesse: http://127.0.0.1:5000/

🔒 Acesso e Credenciais
Acesso Público
Rota: / (Página inicial)

Uso: Análise de emails/documentos.

Acesso Administrativo
Rota: /login ou botão Admin na página inicial.

Função: Configurar o System Prompt da IA.

Credenciais (Padrão):

Usuário: admin

Senha: senha123
