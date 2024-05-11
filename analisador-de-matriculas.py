"""
Analisador de Matrículas Imobiliárias para Operações de Crédito
Versão: 0.1
Por: @fabriciorodias
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai
from PyPDF2 import PdfReader
import streamlit as st

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

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                              generation_config=generation_config,
                              safety_settings=safety_settings)


# --------------------------------------------------------------
# Métodos de extração de texto de PDF (apenas PDF's com texto)
# --------------------------------------------------------------
def extract_pdf_pages(file) -> list[str]:
    parts = [f"--- START OF PDF ---"]

    print("Iniciando extração de texto do PDF...")

    # Create a PDF file reader object
    pdf_reader = PdfReader(file)

    # Get the number of pages in the PDF
    num_pages = len(pdf_reader.pages)

    # For each page in the PDF
    for index in range(num_pages):
        # Extract the text from the page
        page = pdf_reader.pages[index].extract_text()

        # Append the page text to the parts list
        parts.append(f"--- PAGE {index} ---")
        parts.append(page)

    print("Extração de texto do PDF concluída.")

    return parts


# --------------------------------------------------------------
# Solicita análise via chat com texto extraído de um PDF e
# "priming" com few-shot learning (apenas um exemplo).
# Ao final da execução, retorna o objeto de conversa.
# --------------------------------------------------------------
def start_chat_with_pdf_text(pdf_text: list[str]):

    with st.spinner('Processando...'):
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
    st.markdown("<h1 style='text-align: center;'>Analisador de Matrículas Imobiliárias para Operações de Crédito</h1>",
                unsafe_allow_html=True)

    uploaded_file = st.sidebar.file_uploader("Envie uma Certidão de Matrícula Imobiliária num arquivo PDF (contendo "
                                             "apenas texto):", type="pdf")
    if uploaded_file is not None:
        pdf_text = extract_pdf_pages(uploaded_file)
        print("PDF Text:", pdf_text)
        print("Iniciando análise...")
        convo = start_chat_with_pdf_text(pdf_text)
        print("Análise iniciada pela API...")
        st.write(convo.last.text)
        print("Análise finalizada e exibida na tela.")


if __name__ == "__main__":
    app()
