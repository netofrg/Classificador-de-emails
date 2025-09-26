import os
import json
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from dotenv import load_dotenv
from google import genai
from google.genai import types 
from werkzeug.utils import secure_filename
from functools import wraps 

# --- IMPORTAÇÕES PARA LEITURA DE ARQUIVOS ---
import PyPDF2 
from docx import Document 

# --- Configuração Inicial ---
load_dotenv() 

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave_secreta_muito_forte_aqui") 

# Configurações para Upload de Arquivos
UPLOAD_FOLDER = '/tmp/uploads' if os.environ.get('PORT') else 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
PROMPT_CONFIG_FILE = 'prompt_config.json'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Prompt Padrão (Fallback) ---
DEFAULT_SYSTEM_PROMPT = """
Você é um assistente de triagem de emails/documentos altamente eficiente para uma grande empresa do setor financeiro. 
Sua tarefa é analisar o conteúdo do email/documento e realizar duas ações:

1. CLASSIFICAR: O email deve ser classificado em uma das duas categorias, e APENAS estas:
    - 'PRODUTIVO': Requer ação, resposta específica ou é uma solicitação de acompanhamento (ex: 'dúvida sobre o sistema', 'solicitação de status').
    - 'IMPRODUTIVO': Não requer ação imediata e pode ser ignorado ou arquivado (ex: 'agradecimentos', 'mensagens de felicitações').
    
2. GERAR RESPOSTA: Sugerir uma resposta profissional e breve em Português (BR) adequada à classificação e ao teor do email. Para Produtivos, a resposta deve ser proativa.

3. FORMATO DE SAÍDA: O resultado DEVE ser um objeto JSON válido, com as chaves minúsculas e no formato:
    {
      "classificacao": "PRODUTIVO" ou "IMPRODUTIVO",
      "resposta_sugerida": "Texto da resposta profissional e breve."
    }
"""

# --- Funções para Salvar/Carregar o Prompt ---
def load_prompt():
    if os.path.exists(PROMPT_CONFIG_FILE):
        with open(PROMPT_CONFIG_FILE, 'r') as f:
            data = json.load(f)
            return data.get('system_prompt', DEFAULT_SYSTEM_PROMPT)
    return DEFAULT_SYSTEM_PROMPT

def save_prompt(prompt_text):
    with open(PROMPT_CONFIG_FILE, 'w') as f:
        json.dump({'system_prompt': prompt_text}, f)

# Inicializa o arquivo de prompt se ele não existir
if not os.path.exists(PROMPT_CONFIG_FILE):
    save_prompt(DEFAULT_SYSTEM_PROMPT)

# --- Inicialização do Cliente Gemini ---
client = None
try:
    api_key = os.getenv("GEMINI_API_KEY") 
    if api_key:
        client = genai.Client(api_key=api_key)
        print("Serviço de IA (Gemini) inicializado com sucesso.")
    else:
        raise ValueError("GEMINI_API_KEY não encontrada nas variáveis de ambiente.")
        
except Exception as e:
    print(f"ATENÇÃO: Erro ao inicializar o cliente Gemini. Verifique a chave de API. Erro: {e}")

# --- Decorator para Requerer Login ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Funções de Extração de Texto ---
def extrair_texto_do_arquivo(filepath):
    ext = filepath.rsplit('.', 1)[1].lower()
    
    if ext == 'pdf':
        try:
            with open(filepath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = "".join(page.extract_text() or "" for page in reader.pages)
                return text
        except Exception as e:
            print(f"Erro ao ler PDF: {e}")
            return None
    elif ext == 'docx':
        try:
            doc = Document(filepath)
            return '\n'.join([p.text for p in doc.paragraphs])
        except Exception as e:
            print(f"Erro ao ler DOCX: {e}")
            return None
    elif ext == 'txt':
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Erro ao ler TXT: {e}")
            return None
    return None

# --- Função de Processamento com IA ---
def processar_email_com_ia(texto_email, system_prompt):
    if client is None:
        return {
            "classificacao": "ERRO",
            "resposta_sugerida": "O serviço de IA não está configurado. Verifique a chave de API e reinicie o servidor."
        }
    
    try:
        contents = [
            ("system", system_prompt),
            ("user", f"Analise o seguinte documento/email: \n\n{texto_email}") 
        ]
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        resposta_json_str = response.text
        return json.loads(resposta_json_str)
        
    except Exception as e:
        print(f"Erro na comunicação com a API de IA: {e}")
        return {
            "classificacao": "ERRO",
            "resposta_sugerida": f"Não foi possível processar o documento devido a um erro na API. Detalhe: {e}"
        }

# --- Rota para a Interface Web (Página Principal - ACESSO PÚBLICO) ---
@app.route('/')
def index():
    # Carrega o prompt do arquivo, sem necessidade de login
    current_prompt = load_prompt()
    return render_template('index.html', current_prompt=current_prompt)

# --- Rota de Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'senha123':
            session['logged_in'] = True
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('admin')) # Redireciona para a página de admin
        else:
            flash('Credenciais inválidas. Tente novamente.', 'danger')
    
    if session.get('logged_in'):
        return redirect(url_for('admin'))
        
    return render_template('login.html')

# --- Rota de Logout ---
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index')) # Redireciona para a página inicial

# --- Rota de Administração (Configuração do Prompt - PROTEGIDA) ---
@app.route('/admin', methods=['GET', 'POST'])
@login_required 
def admin():
    current_prompt = load_prompt()

    if request.method == 'POST':
        new_prompt = request.form.get('system_prompt_area')
        if new_prompt and new_prompt.strip():
            save_prompt(new_prompt.strip())
            flash('Prompt do Sistema atualizado com sucesso!', 'success')
            current_prompt = new_prompt.strip()
        else:
            flash('O prompt não pode ser vazio.', 'danger')

    return render_template('admin.html', current_prompt=current_prompt)

# --- Endpoint UNIFICADO de Processamento (API - ACESSO PÚBLICO) ---
@app.route('/api/processar', methods=['POST'])
def processar_entrada():
    texto_email = ""
    
    # Carrega o prompt do arquivo
    system_prompt = load_prompt()

    dados = request.get_json(silent=True)
    if dados and 'email' in dados:
        texto_email = dados.get('email', '')
        if texto_email:
            return jsonify(processar_email_com_ia(texto_email, system_prompt))

    if 'file' in request.files:
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"erro": "Nenhum arquivo selecionado."}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            texto_email = extrair_texto_do_arquivo(filepath)
            os.remove(filepath)
            
            if texto_email:
                return jsonify(processar_email_com_ia(texto_email, system_prompt))
            else:
                return jsonify({"erro": f"Não foi possível extrair o texto do arquivo {file.filename}."}), 400

    return jsonify({"erro": "Nenhum texto colado nem arquivo válido foi fornecido."}), 400

# --- Execução do Servidor ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))