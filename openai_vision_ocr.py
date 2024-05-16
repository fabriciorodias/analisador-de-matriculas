import os
import logging
import base64
import requests
from dotenv import load_dotenv

# OpenAI API Key
load_dotenv('keys.env')
api_key = os.getenv("OPENAI_API_KEY")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --------------------------------------------------------------
# Função para codificar uma imagem em base64, necessária para
# enviar para a API da OpenAI
# --------------------------------------------------------------
def encode_image(image_path):
    logging.info(f"Codificando a imagem para base64...")
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# --------------------------------------------------------------
# Extração de texto de uma imagem (para documentos escaneados)
# usando a API da OpenAI (GPT-4o)
# --------------------------------------------------------------
def get_text_from_image_with_vision(image_path: str):

    base64_image = encode_image(image_path)

    logging.info("Configurando a requisição para a API da OpenAI...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract text from this image."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 3000
    }

    logging.info("Enviando a requisição para a API da OpenAI...")
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    json_data = response.json()

    # Extract the messages content from the response
    parts = [choice['message']['content'] for choice in json_data.get('choices', [])]

    # Extract the token usage details
    prompt_tokens = json_data.get('usage', {}).get('prompt_tokens', 0)
    completion_tokens = json_data.get('usage', {}).get('completion_tokens', 0)
    total_tokens = json_data.get('usage', {}).get('total_tokens', 0)

    logging.info("Resposta da API da OpenAI:")
    logging.info(parts)
    logging.info(f"Prompt tokens used: {prompt_tokens}")
    logging.info(f"Completion tokens used: {completion_tokens}")
    logging.info(f"Total tokens used: {total_tokens}")

    return parts
