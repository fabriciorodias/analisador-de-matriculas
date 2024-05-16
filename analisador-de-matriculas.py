"""
Analisador de Matrículas Imobiliárias para Operações de Crédito
Versão: 0.5
Por: @fabriciorodias
"""
import logging
import os
from dotenv import load_dotenv
import google.generativeai as genai
from PyPDF2 import PdfReader
import streamlit as st
from pdf2image import convert_from_path
from openai_vision_ocr import get_text_from_image_with_vision
import tempfile
from pdf2image.exceptions import PDFPageCountError
import shutil
from tesseract_ocr import get_text_from_image_with_tesseract
from bnb_style import footer
from models import ProprietarioAtual, GravameRestricao, TextoAnalise, ResultadoAnalise
from prompts import generate_optimized_prompt
import json
import re
from pydantic import ValidationError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --------------------------------------------------------------
# Carregando variáveis de ambiente
# --------------------------------------------------------------

load_dotenv('keys.env')
G_KEY = os.getenv("GOOGLE_AI_API_KEY")

# --------------------------------------------------------------
# Configurações e inicialização do Google AI
# --------------------------------------------------------------

genai.configure(api_key=G_KEY)

# Set up the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 0,
  "max_output_tokens": 8192,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
]

# noinspection PyTypeChecker
model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                              generation_config=generation_config,
                              safety_settings=safety_settings)


# --------------------------------------------------------------
# Função para extrair objetos JSON de um texto
# --------------------------------------------------------------
def extract_json(text_response: str) -> list:
    json_objects = []
    json_str = ""
    in_json = False
    braces_count = 0

    for char in text_response:
        if char == '{':
            if not in_json:
                in_json = True
                json_str = char
            else:
                json_str += char
            braces_count += 1
        elif char == '}':
            json_str += char
            braces_count -= 1
            if braces_count == 0 and in_json:
                try:
                    json_obj = json.loads(json_str)
                    json_objects.append(json_obj)
                except json.JSONDecodeError:
                    pass
                json_str = ""
                in_json = False
        elif in_json:
            json_str += char

    return json_objects



# --------------------------------------------------------------
# Função para validar objetos JSON com um modelo Pydantic
# --------------------------------------------------------------
def validate_json_with_model(model_class, json_data):
    validated_data = []
    validation_errors = []
    if isinstance(json_data, list):
        for item in json_data:
            try:
                model_instance = model_class(**item)
                validated_data.append(model_instance.dict())
            except ValidationError as e:
                validation_errors.append({"error": str(e), "data": item})
    elif isinstance(json_data, dict):
        try:
            model_instance = model_class(**json_data)
            validated_data.append(model_instance.dict())
        except ValidationError as e:
            validation_errors.append({"error": str(e), "data": json_data})
    else:
        raise ValueError("Invalid JSON data type. Expected dict or list.")
    return validated_data, validation_errors


# --------------------------------------------------------------
# Widget de upload de arquivo PDF da Certidão de Matrícula
# --------------------------------------------------------------
def handle_file_upload():
    return st.sidebar.file_uploader("**Envie uma Certidão** de Matrícula Imobiliária num arquivo PDF (contendo apenas "
                                    "texto):", type="pdf", help="Confira se o arquivo contém todas as páginas do "
                                                                "documento, se elas estão na ordem correta e se "
                                                                "o texto está legível.")


# --------------------------------------------------------------
# Métodos de extração de texto de PDF
# --------------------------------------------------------------
def extract_pdf_pages(file) -> list[str]:
    parts = [f"--- START OF PDF ---"]

    logging.info("Iniciando extração de texto do PDF...")

    # Cria um objeto PdfReader
    pdf_reader = PdfReader(file)

    # Retorna o número de páginas no PDF
    num_pages = len(pdf_reader.pages)

    # Configura a barra de progresso
    progress_text = "Extraindo texto do PDF..."
    progress_bar = st.progress(0, progress_text)
    progress_step = 1 / num_pages

    # Verifica apenas a primeira página para determinar se o PDF é de texto ou escaneado
    first_page = pdf_reader.pages[0].extract_text()
    first_page_word_count = len(first_page.split())
    logging.info(
        f"Texto extraído da primeira página: {first_page[:100]}... (total de {first_page_word_count} palavras)")

    all_pages_as_images = first_page_word_count < 100

    if all_pages_as_images:
        logging.info("Primeira página parece ser de um documento escaneado. Inicializando OCR para todas as páginas...")
        images = convert_pdf_to_jpeg(file)
        for i, image in enumerate(images):
            text_from_image = get_text_from_image_with_tesseract(image)
            parts.append(f"--- PAGE {i} (OCR) ---")
            parts.append(text_from_image)
            progress_bar.progress(min(1.0, progress_step * (i + 1)), f"Parece que o PDF é um documento "
                                                                     f"escaneado. {progress_text}")
    else:
        logging.info("Documento identificado como PDF de texto.")
        for index in range(num_pages):
            page = pdf_reader.pages[index].extract_text()
            parts.append(f"--- PAGE {index} ---")
            parts.append(page)
            progress_bar.progress(min(1.0, progress_step * (index + 1)), progress_text)

    logging.info("Extração de texto do PDF concluída.")
    progress_bar.empty()
    return parts


# --------------------------------------------------------------
# Extração de imagens de um PDF (para documentos escaneados)
# --------------------------------------------------------------
def convert_pdf_to_jpeg(uploaded_file):
    # Criar um arquivo temporário para o PDF
    logging.info(f"uploaded_file: {uploaded_file.name}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        # Ensure the file pointer is at the start of the file
        uploaded_file.seek(0)
        shutil.copyfileobj(uploaded_file, tmp)
        # Ensure the file pointer is at the start of the file
        tmp.seek(0)
        tmp_path = tmp.name

    try:
        logging.info(f"Conteúdo da variável 'tmp_path': {tmp_path}")
        images = convert_from_path(tmp_path)
        jpeg_paths = []
        for i, image in enumerate(images):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as output_tmp:
                output_file_path = output_tmp.name
                image.save(output_file_path, 'JPEG')
                jpeg_paths.append(output_file_path)
    except PDFPageCountError:
        st.error("O arquivo enviado não é um arquivo PDF válido.")
    finally:
        os.remove(tmp_path)

    return jpeg_paths


# --------------------------------------------------------------
# Verificar se o arquivo PDF foi extraído com sucesso e
# iniciar a análise do texto extraído chamando a função
# start_chat_with_pdf_text. Caso o PDF seja uma imagem
# escaneada, exibir uma mensagem de erro.
# --------------------------------------------------------------
def handle_pdf_analysis(uploaded_file) -> dict:
    if uploaded_file is not None:
        pdf_text = extract_pdf_pages(uploaded_file)
        logging.info("Texto do PDF extraído. Enviando para análise da API...")
        response_text = start_chat_with_pdf_text(pdf_text)
        logging.info("Análise concluída. Extraindo e validando JSON...")

        json_objects = extract_json(response_text)
        validated, errors = validate_json_with_model(TextoAnalise, json_objects)

        if errors:
            st.error("Erros na validação do JSON: " + str(errors))
            return {}

        logging.info("Enviando resultado formatado para exibição...")
        return validated[0] if validated else {}
    return {}


# --------------------------------------------------------------
# Solicita análise via chat com texto extraído de um PDF e
# "priming" com few-shot learning (apenas um exemplo).
# Ao final da execução, retorna o objeto de conversa.
# --------------------------------------------------------------
def start_chat_with_pdf_text(pdf_text: list[str]):
    document_text = "\n".join(pdf_text)
    optimized_prompt = generate_optimized_prompt(document_text)

    with st.spinner('Texto da certidão em análise...'):
        response = model.generate_content(optimized_prompt)
        return response.text


def app():
    # Título da página no navegador (deve ser a primeira chamada do Streamlit)
    st.set_page_config(page_title="Analisador de Matrículas Imobiliárias")

    # Esconde o menu principal e o rodapé do Streamlit
    hide_default_format = """
           <style>
           #MainMenu {visibility: hidden;}
           footer {visibility: hidden;}
           .stDeployButton {display:none;}
           </style>
           """
    st.markdown(hide_default_format, unsafe_allow_html=True)

    # Seção central da página, onde o conteúdo será exibido
    st.markdown("<h1 style='text-align: center;'>iAnalisador - Matrículas</h1>", unsafe_allow_html=True)

    # Sidebar com o widget de upload de arquivo PDF
    st.sidebar.markdown("<h2 style='text-align: center;'>iAnalisador</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("<h5 style='text-align: center;'>v0.5 (beta)</h5>", unsafe_allow_html=True)
    st.sidebar.subheader("Instruções")
    st.sidebar.write("Verifique se o arquivo PDF:\n"
                     "1. Contém todas as páginas da certidão\n"
                     "2. Se elas estão na ordem correta\n"
                     "3. Se o texto está legível\n")
    st.sidebar.markdown("<h4 style='text-align: center;'>Envio de Arquivo</h4>", unsafe_allow_html=True)
    uploaded_file = handle_file_upload()
    result = handle_pdf_analysis(uploaded_file)

    if result:
        # Exibir a situação do imóvel
        situacao = result.get("situacao_imovel")
        if situacao == "APTO":
            st.success("O imóvel está APTO.", icon="✅")
        else:
            st.error("O imóvel está INAPTO.", icon="🚨")

        # Exibir dados do proprietário
        with st.container():
            st.subheader("Proprietário Atual")
            proprietario = result.get("proprietario_atual", {})
            for key, value in proprietario.items():
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")

        # Exibir gravames
        st.subheader("Gravames/Restrições")
        gravames = result.get("gravames_restricoes", [])
        if gravames:
            for gravame in gravames:
                with st.expander(gravame.get("tipo", "Gravame")):
                    for key, value in gravame.items():
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        else:
            st.write("Não há gravames ou restrições.")

        # Exibir observações
        with st.container():
            st.subheader("Observações")
            observacoes = result.get("observacoes", "Não há observações.")
            st.write(observacoes)

    st.sidebar.markdown(footer, unsafe_allow_html=True)


if __name__ == "__main__":
    app()
