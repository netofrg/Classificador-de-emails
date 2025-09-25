import os
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from google import genai
from google.genai import types 
from werkzeug.utils import secure_filename

# --- IMPORTAÇÕES PARA LEITURA DE ARQUIVOS ---
import PyPDF2 
from docx import Document 

# --- Configuração Inicial ---
load_dotenv() 

app = Flask(__name__)

# Configurações para Upload de Arquivos
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    print(f"ATENÇÃO: Erro ao inicializar o cliente Gemini. Verifique a chave de API e reinicie o servidor. Erro: {e}")


# --- Funções de Extração de Texto ---
def extrair_texto_do_arquivo(filepath):
    ext = filepath.rsplit('.', 1)[1].lower()
    
    if ext == 'pdf':
        try:
            with open(filepath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
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

# --- Função de Processamento com IA (GEMINI) ---
def processar_email_com_ia(texto_email):
    """
    Usa o texto original para o modelo Gemini para classificação.
    """
    
    if client is None:
        return {
            "classificacao": "ERRO",
            "resposta_sugerida": "O serviço de IA não está configurado. Verifique a chave de API e reinicie o servidor."
        }
    
    # Prompt Engineering
    system_prompt = """
    Você é um assistente de triagem de emails/documentos altamente eficiente para uma grande empresa do setor financeiro. 
    Sua tarefa é analisar o conteúdo do email/documento e realizar duas ações:

    1. CLASSIFICAR: O email deve ser classificado em uma das duas categorias, e APENAS estas:
        - 'Produtivo': Requer ação, resposta específica ou é uma solicitação de acompanhamento (ex: 'dúvida sobre o sistema', 'solicitação de status').
        - 'Improdutivo': Não requer ação imediata e pode ser ignorado ou arquivado (ex: 'agradecimentos', 'mensagens de felicitações').
    
    2. GERAR RESPOSTA: Sugerir uma resposta profissional e breve em Português (BR) adequada à classificação e ao teor do email. Para Produtivos, a resposta deve ser proativa.
    
    3. FORMATO DE SAÍDA: O resultado DEVE ser um objeto JSON válido, com as chaves minúsculas e no formato:
        {
          "classificacao": "Produtivo" ou "Improdutivo",
          "resposta_sugerida": "Texto da resposta profissional e breve."
        }
    """
    
    try:
        # Sintaxe Simplificada de Conteúdo
        contents = [
            ("system", system_prompt),
            # Envia o TEXTO ORIGINAL para o modelo
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


# --- Endpoint para a Interface Web (Root) ---
@app.route('/')
def index():
    return render_template('index.html')


# --- Endpoint UNIFICADO de Processamento (API) ---
@app.route('/api/processar', methods=['POST'])
def processar_entrada():
    texto_email = ""
    
    # 1. Tenta pegar o Texto Colado (JSON)
    dados = request.get_json(silent=True)
    if dados and 'email' in dados:
        texto_email = dados.get('email', '')
        if texto_email:
            return jsonify(processar_email_com_ia(texto_email))

    # 2. Tenta pegar o Arquivo de Upload (Multipart Form Data)
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
                return jsonify(processar_email_com_ia(texto_email))
            else:
                return jsonify({"erro": f"Não foi possível extrair o texto do arquivo {file.filename}."}), 400

    return jsonify({"erro": "Nenhum texto colado nem arquivo válido foi fornecido."}), 400


# --- Execução do Servidor ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))