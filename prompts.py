from string import Template


def debug_prompt(document_text: str):
    print("DEBUG: base_prompt")
    print(base_prompt)
    print("DEBUG: document_text")
    print(document_text)


# Prompt base para análise da certidão de matrícula
base_prompt = Template("""
Analise a certidão de inteiro teor fornecida pelo usuário via arquivo e extraia as seguintes informações:

Proprietário Atual: Identifique o proprietário atual do imóvel, incluindo seu nome completo, nacionalidade, 
estado civil, profissão, documentos de identificação e data de aquisição do imóvel.

Gravames/Restrições: Liste os gravames e/ou restrições que incidem sobre o imóvel e que gerem sua inalienabilidade, 
especificando o tipo (ex: hipoteca, penhora, arresto), data de registro/averbação, número do registro/averbação e 
informações relevantes do processo judicial ou administrativo relacionado, se aplicável.

Observações: Inclua qualquer outra informação relevante sobre a situação do imóvel, como resultados de consultas à 
CNIB, data de emissão da certidão e necessidade de atualização das informações. Caso o imóvel tenha tido algum gravame 
ou ocorrência jurídica relevante que já tenha sido baixada, inclua essa informação de maneira clara, mas resumida e não
considere como motivo de inaptidão. Inclua também o tempo total de cadeia sucessória da matrícula atual do imóvel.
Se a cadeia sucessória da matrícula atual envolver a retroação ao período de matrículas anteriores, especifique o prazo
de retroação total considerando todas as matrículas originárias que estejam na certidão. IMPORTANTE, garanta qua a
sua análise neste campo seja completa e detalhada, rica em informações e bem organizada, podendo ter vários parágrafos
ou tópicos, listas, etc., desde que bem organizados num campo de texto. O nível de detalhamento e recomendações
é muito importante aqui, pois subsidiará a tomada de decisão do usuário quanto à adequabilidade ou não do imóvel
para a finalidade de garantia bancária.

Situação do Imóvel: Como resultado final, classifique o imóvel como APTO, caso inexistam restrições/gravames de 
indisponibilidade vigentes na data do documento, ou INAPTO, caso existam. Indique os motivos.

Apresente sua resposta no formato JSON, seguindo o modelo abaixo:

{
  "proprietario_atual": {
    "nome_completo": "string",
    "nacionalidade": "string",
    "estado_civil": "string",
    "profissao": "string",
    "documentos_identificacao": ["string"],
    "data_aquisicao": "string"
  },
  "gravames_restricoes": [
    {
      "tipo": "string",
      "data_registro": "string",
      "numero_registro": "string",
      "detalhes_processo": "string"
    }
  ],
  "observacoes": "string",
  "situacao_imovel": "string",
  "resultado_analise": {
    "veredito": "boolean",
    "data_emissao": "date",
    "vigente_ate": "date",
    "prazo_cadeia_sucessoria": "string"
  }
}

Document text: $document_text
""")


def generate_optimized_prompt(document_text: str) -> str:
    debug_prompt(document_text)  # Adicionando depuração
    return base_prompt.substitute(document_text=document_text)
