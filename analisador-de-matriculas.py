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

    # Para cada página no PDF
    for index in range(num_pages):
        # Extrai o texto da página
        page = pdf_reader.pages[index].extract_text()
        word_count = len(page.split())
        logging.info(f"Texto extraído da página {index}: {page[:100]}... (total de {word_count} palavras)")

        # Se menos de 100 palavras foram extraídas, assume que a página é uma imagem escaneada
        # ATENÇÃO!!!!!!!: Corrigir para que, uma vez que tenha chegado aqui na primeira iteração, não
        # seja necessário verificar as demais páginas para a existência de texto, tratar todas
        # as páginas como imagens escaneadas.
        if word_count < 100:
            logging.info(f"Página {index} parece ser de um documento escaneado. Inicializando OCR...")
            images = convert_pdf_to_jpeg(file)
            logging.info(f"Imagem extraída do PDF salva em: {images}")
            logging.info("Chamando a função de extração de texto da imagem...")

            # DESATIVADO para testes com Tesseract OCR
            # Extrai o texto da imagem com a API da OpenAI (GPT-4o)
            # parts = get_text_from_image_with_vision(output_file_path)

            # Itera sobre todas as imagens (uma por página) e extrai o texto com Tesseract OCR
            for i, image in enumerate(images):
                text_from_image = get_text_from_image_with_tesseract(image)
                parts.append(f"--- PAGE {i} (OCR) ---")
                parts.append(text_from_image)
                # Atualiza a barra de progresso
                progress_bar.progress(min(1.0, progress_step * (index + 1 + i)), progress_text)

            break  # Todas as páginas foram tratadas como imagens, então sair do loop

        # Append the page text to the parts list
        parts.append(f"--- PAGE {index} ---")
        parts.append(page)

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

    images = []
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

    return jpeg_paths


# --------------------------------------------------------------
# Verificar se o arquivo PDF foi extraído com sucesso e
# iniciar a análise do texto extraído chamando a função
# start_chat_with_pdf_text. Caso o PDF seja uma imagem
# escaneada, exibir uma mensagem de erro.
# --------------------------------------------------------------
def handle_pdf_analysis(uploaded_file) -> str:
    if uploaded_file is not None:
        pdf_text = extract_pdf_pages(uploaded_file)
        logging.info("Texto do PDF extraído. Enviando para análise da API...")
        convo = start_chat_with_pdf_text(pdf_text)
        logging.info("Análise concluída.")
        return convo.last.text
    return ""


# --------------------------------------------------------------
# Solicita análise via chat com texto extraído de um PDF e
# "priming" com few-shot learning (apenas um exemplo).
# Ao final da execução, retorna o objeto de conversa.
# --------------------------------------------------------------
def start_chat_with_pdf_text(pdf_text: list[str]):

    with st.spinner('Texto da certidão em análise...'):
        convo = model.start_chat(history=[
            {
                "role": "user",
                "parts": [
                    "Exemplo de Análise:## Análise da Certidão de Inteiro Teor da Matrícula [NÚMERO DA "
                    "MATRÍCULA]**Proprietário Atual:**[INFORMAÇÕES SOBRE O PROPRIETÁRIO ATUAL: Nome, nacionalidade, "
                    "estado civil, profissão, documentos de identificação e data de aquisição do "
                    "imóvel]**Gravames/Restrições:**[LISTA DE GRAVAMES E/OU RESTRIÇÕES, incluindo o tipo, "
                    "data de registro/averbação, número do registro/averbação e dados relevantes sobre o processo "
                    "judicial ou administrativo, se aplicável]**Observações:*** [INFORMAÇÕES ADICIONAIS RELEVANTES, "
                    "como resultados de consultas à CNIB, data de emissão da certidão e necessidade de atualização das "
                    "informações]**Situação do Imóvel**[Informação se o imóvel encontra-se APTO para ser alienado "
                    "fiduciariamente como garantia em operação de crédito ou se o imóvel encontra-se INAPTO para ser "
                    "alienado fiduciariamente por existirem gravames e/ou restrições ainda não baixadas/canceladas na "
                    "data da emissão do documento]Instruções para a LLM:Com base no exemplo de análise acima, "
                    "analise a certidão de inteiro teor fornecida pelo usuário via arquivo e extraia as seguintes "
                    "informações:Proprietário Atual: Identifique o proprietário atual do imóvel, incluindo seu nome "
                    "completo, estado civil, profissão, documentos de identificação e data de aquisição do "
                    "imóvel.Gravames/Restrições: Liste os gravames e/ou restrições que incidem sobre o imóvel e que "
                    "gerem sua inalienabilidade, especificando o tipo (ex: hipoteca, penhora, arresto), "
                    "data de registro/averbação, número do registro/averbação e informações relevantes do processo "
                    "judicial ou administrativo relacionado, se aplicável.Obs.: Inclua qualquer outra informação "
                    "relevante sobre a situação do imóvel, como resultados de consultas à CNIB, data de emissão da "
                    "certidão e necessidade de atualização das informações.Situação do Imóvel: Como resultado final, "
                    "classifique o imóvel como APTO, caso inexistam restrições/gravames de indisponibilidade vigentes "
                    "na data do documento, ou INAPTO, caso existam.O usuário iniciará uma novas interações enviando "
                    "um arquivo PDF com a certidão que será objeto da análise. Antes de iniciar seu raciocínio, "
                    "o primeiro passo será ler o documento e coletar todas as palavras/tokens dele. Assim, "
                    "antes de responder, aguarde o envio do arquivo PDF pelo usuário. Formato de Resposta:Apresente "
                    "as informações extraídas da certidão no mesmo formato do exemplo de análise, utilizando as seções "
                    "\"Proprietário Atual\", \"Gravames/Restrições\" e \"Observações\" e \"Situação do Imóvel\"."]
            },
            {
                "role": "user",
                "parts": pdf_text
            },
        ])

        convo.send_message("Pode analisar a certidão fornecida!")

    return convo


def app():
    # Título da página no navegador
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
    st.markdown("<h1 style='text-align: center;'>iAnalisador - Matrículas</h1>",
                unsafe_allow_html=True)

    # Sidebar com o widget de upload de arquivo PDF
    st.sidebar.markdown("<h2 style='text-align: center;'>iAnalisador</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("<h5 style='text-align: center;'>v0.5 (beta)</h5>",
                        unsafe_allow_html=True)
    st.sidebar.subheader("Instruções")
    st.sidebar.write("Verifique se o arquivo PDF:\n"
                     "1. Contém todas as páginas da certidão\n"
                     "2. Se elas estão na ordem correta\n"
                     "3. Se o texto está legível\n")
    st.sidebar.markdown("<h4 style='text-align: center;'>Envio de Arquivo</h4>", unsafe_allow_html=True)
    uploaded_file = handle_file_upload()
    result = handle_pdf_analysis(uploaded_file)
    if result:
        st.markdown(f"<h2 style='text-align: center;'>Resultado da Análise</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>{result}</p>", unsafe_allow_html=True)

    st.sidebar.markdown(footer, unsafe_allow_html=True)


if __name__ == "__main__":
    app()
