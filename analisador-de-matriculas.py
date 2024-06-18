"""
Analisador de Matrículas Imobiliárias para Operações de Crédito
Versão: 0.8 (beta)
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
from datetime import datetime, timedelta
from google_gemini_adapter import get_google_gemini_model
from openai_gpt4o_adapter import get_completion_from_openai_gpt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_completion_from_google_gemini(prompt: str):
    model = get_google_gemini_model()
    response = model.generate_content(prompt)
    return response


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

    # Verificar se a chave 'resultado_analise' está presente e preservar a estrutura original
    for item in validated_data:
        if "resultado_analise" not in item:
            original_item = next((d for d in json_data if d.get("resultado_analise")), None)
            if original_item:
                item["resultado_analise"] = original_item["resultado_analise"]

    return validated_data, validation_errors


# --------------------------------------------------------------
# Funções auxiliares para cálculos de datas e prazos
# --------------------------------------------------------------
def calcular_data_validade(data_emissao_str, prazo_validade=180):
    data_emissao = datetime.strptime(data_emissao_str, "%Y-%m-%d")
    data_validade = data_emissao + timedelta(days=prazo_validade)
    return data_validade.strftime("%Y-%m-%d")


def calcular_prazo_cadeia_sucessoria(data_emissao_str, matriculas_originarias=[]):
    data_emissao = datetime.strptime(data_emissao_str, "%Y-%m-%d")
    tempos_cadeia = []
    for data_nascimento_str in matriculas_originarias:
        data_nascimento = datetime.strptime(data_nascimento_str, "%Y-%m-%d")
        tempo_total = (data_emissao - data_nascimento).days
        tempos_cadeia.append(tempo_total)
    return tempos_cadeia


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
        logging.info(f"JSON extraído: {json_objects}")
        validated, errors = validate_json_with_model(TextoAnalise, json_objects)

        if errors:
            st.error("Erros na validação do JSON: " + str(errors))
            return {}

        # Calcular data de validade e prazo da cadeia sucessória
        analysis_result = validated[0] if validated else {}
        logging.info(f"Analysis result after validation: {analysis_result}")

        # Verifique se a chave 'resultado_analise' existe no dicionário
        resultado_analise = analysis_result.get("resultado_analise")
        if not resultado_analise:
            logging.warning("Chave 'resultado_analise' não encontrada no resultado da análise. Criando chave padrão.")
            resultado_analise = {}
            analysis_result["resultado_analise"] = resultado_analise

        logging.info(f"Resultado da análise antes da atualização: {resultado_analise}")

        data_emissao = resultado_analise.get("data_emissao", None)

        # Verifica se a data de emissão é válida antes de calcular a data de validade
        if data_emissao and data_emissao != "N/A":
            try:
                # Verifique se a data está no formato correto antes de converter
                if re.match(r'\d{4}-\d{2}-\d{2}', data_emissao):
                    datetime.strptime(data_emissao, "%Y-%m-%d")
                    prazo_validade_dias = 180  # Assumindo 180 dias se não especificado
                    data_validade = calcular_data_validade(data_emissao, prazo_validade_dias)
                    matriculas_originarias = resultado_analise.get("matriculas_originarias", [])
                    prazo_cadeia = calcular_prazo_cadeia_sucessoria(data_emissao, matriculas_originarias)
                    resultado_analise["vigente_ate"] = data_validade
                    resultado_analise["prazo_cadeia_sucessoria"] = prazo_cadeia
                else:
                    logging.error("Formato de data de emissão inválido.")
                    resultado_analise["vigente_ate"] = "Data de emissão inválida"
                    resultado_analise["prazo_cadeia_sucessoria"] = "Data de emissão inválida"
            except ValueError as e:
                logging.error(f"Erro ao converter data de emissão: {e}")
                resultado_analise["vigente_ate"] = "Data de emissão inválida"
                resultado_analise["prazo_cadeia_sucessoria"] = "Data de emissão inválida"
        else:
            resultado_analise["vigente_ate"] = "Data de emissão inválida"
            resultado_analise["prazo_cadeia_sucessoria"] = "Data de emissão inválida"

        logging.info(f"Resultado da análise após a atualização: {analysis_result['resultado_analise']}")
        return analysis_result

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
        # response = get_completion_from_google_gemini(optimized_prompt).text
        response = get_completion_from_openai_gpt(optimized_prompt)
        return response


def app():
    # Título da página no navegador
    st.set_page_config(page_title="iAnalisadora - Matrículas Imobiliárias")

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
    st.markdown("<h1 style='text-align: center;'>iAnalisadora - Matrículas</h1>", unsafe_allow_html=True)

    # Sidebar com o widget de upload de arquivo PDF
    st.sidebar.markdown("<h2 style='text-align: center;'>iAnalisadora</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("<h5 style='text-align: center;'>v0.8 (beta)</h5>", unsafe_allow_html=True)
    st.sidebar.subheader("Instruções")
    st.sidebar.write("Verifique se o arquivo PDF:\n"
                     "1. Contém todas as páginas da certidão\n"
                     "2. Se elas estão na ordem correta\n"
                     "3. Se o texto está legível\n")
    st.sidebar.markdown("<h4 style='text-align: center;'>Envio de Arquivo</h4>", unsafe_allow_html=True)
    uploaded_file = handle_file_upload()

    # Usar variável de estado para armazenar resultado da análise
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None

    if uploaded_file is not None:
        result = handle_pdf_analysis(uploaded_file)
        st.session_state.analysis_result = result

    if st.session_state.analysis_result:
        analysis_result = st.session_state.analysis_result

        situacao_imovel = analysis_result.get("situacao_imovel", "INAPTO")
        if situacao_imovel == "APTO":
            st.success("O imóvel está APTO.", icon="✅")
        else:
            st.error("O imóvel está INAPTO.", icon="🚨")

        with st.container():
            st.subheader("Proprietário Atual")
            proprietario = analysis_result.get("proprietario_atual", {})
            nome_completo = proprietario.get("nome_completo", "Proprietário")
            with st.expander(nome_completo):
                for key, value in proprietario.items():
                    if key != "nome_completo":
                        st.write(f"**{key.replace('_', ' ').capitalize()}:** {value}")

        gravames = analysis_result.get("gravames_restricoes", [])
        if gravames:
            st.subheader("Gravames e Restrições Vigentes")
            for gravame in gravames:
                tipo = gravame.get("tipo", "Gravame")
                numero_registro = gravame.get("numero_registro", "N/A")
                with st.expander(f"{tipo} - {numero_registro}"):
                    for key, value in gravame.items():
                        st.write(f"**{key.replace('_', ' ').capitalize()}:** {value}")
        else:
            st.subheader("Gravames e Restrições Vigentes")
            st.write("Não há gravames ou restrições vigentes.")

        with st.container():
            st.subheader("Fatos Relevantes")
            observacoes = analysis_result.get("observacoes", "Nenhuma observação disponível.")
            st.write(observacoes)

        with st.container():
            st.subheader("Data da Certidão")
            resultado_analise = analysis_result.get("resultado_analise", {})
            data_emissao = resultado_analise.get("data_emissao", "N/A")
            if data_emissao != "N/A":
                data_emissao = datetime.strptime(data_emissao, "%Y-%m-%d").strftime("%d-%m-%Y")
            vigente_ate = resultado_analise.get("vigente_ate", "N/A")
            if vigente_ate != "N/A":
                vigente_ate_dt = datetime.strptime(vigente_ate, "%Y-%m-%d")
                vigente_ate = vigente_ate_dt.strftime("%d-%m-%Y")
                hoje = datetime.now()
                icone = "✅" if vigente_ate_dt >= hoje else "🚨"
            else:
                icone = ""
            prazo_cadeia = resultado_analise.get("prazo_cadeia_sucessoria", "N/A")
            st.write(f"**Data de emissão:** {data_emissao}")
            st.write(f"**Vigente até:** {vigente_ate} {icone}")
            # st.write(f"**Prazo da cadeia sucessória:** {prazo_cadeia}")

    st.sidebar.markdown(footer, unsafe_allow_html=True)


if __name__ == "__main__":
    app()
