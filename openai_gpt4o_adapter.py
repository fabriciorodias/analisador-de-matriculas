from openai import OpenAI
import os
import logging
from dotenv import load_dotenv


# OpenAI API Key
load_dotenv('keys.env')
api_key = os.getenv("OPENAI_API_KEY")

MODEL = "gpt-4o"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --------------------------------------------------------------
# Configurações e inicialização do OpenAI
# --------------------------------------------------------------


def get_openai_gpt_model():
    model = OpenAI(api_key=api_key)
    return model


def get_completion_from_openai_gpt(optimized_prompt):
    client = get_openai_gpt_model()
    completion = client.chat.completions.create(
      model=MODEL,
      messages=[
        {"role": "user", "content": optimized_prompt}
      ]
    )
    return completion.choices[0].message.content
