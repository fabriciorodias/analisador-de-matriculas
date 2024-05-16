from string import Template


def debug_prompt(document_text: str):
    print("DEBUG: base_prompt")
    print(base_prompt)
    print("DEBUG: document_text")
    print(document_text)


# Prompt base para análise da certidão de matrícula
base_prompt = Template("""
Analise a certidão de inteiro teor fornecida pelo usuário via arquivo e extraia as seguintes informações:

Proprietário Atual: Identifique o proprietário atual do imóvel, incluindo seu nome completo, nacionalidade, estado civil, profissão, documentos de identificação e data de aquisição do imóvel.

Gravames/Restrições: Liste os gravames e/ou restrições que incidem sobre o imóvel e que gerem sua inalienabilidade, especificando o tipo (ex: hipoteca, penhora, arresto), data de registro/averbação, número do registro/averbação e informações relevantes do processo judicial ou administrativo relacionado, se aplicável.

Observações: Inclua qualquer outra informação relevante sobre a situação do imóvel, como resultados de consultas à CNIB, data de emissão da certidão e necessidade de atualização das informações.

Situação do Imóvel: Como resultado final, classifique o imóvel como APTO, caso inexistam restrições/gravames de indisponibilidade vigentes na data do documento, ou INAPTO, caso existam. Indique os motivos.

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


old_prompt = 'Exemplo de Análise:## Análise da Certidão de Inteiro Teor da Matrícula [NÚMERO DA '
'MATRÍCULA]**Proprietário Atual:**[INFORMAÇÕES SOBRE O PROPRIETÁRIO ATUAL: Nome, nacionalidade, '
'estado civil, profissão, documentos de identificação e data de aquisição do '
'imóvel]**Gravames/Restrições:**[LISTA DE GRAVAMES E/OU RESTRIÇÕES, incluindo o tipo, '
'data de registro/averbação, número do registro/averbação e dados relevantes sobre o processo '
'judicial ou administrativo, se aplicável]**Observações:*** [INFORMAÇÕES ADICIONAIS RELEVANTES, '
'como resultados de consultas à CNIB, data de emissão da certidão e necessidade de atualização das '
'informações]**Situação do Imóvel**[Informação se o imóvel encontra-se APTO para ser alienado '
'fiduciariamente como garantia em operação de crédito ou se o imóvel encontra-se INAPTO para ser '
'alienado fiduciariamente por existirem gravames e/ou restrições ainda não baixadas/canceladas na '
'data da emissão do documento]Instruções para a LLM:Com base no exemplo de análise acima, '
'analise a certidão de inteiro teor fornecida pelo usuário via arquivo e extraia as seguintes '
'informações:Proprietário Atual: Identifique o proprietário atual do imóvel, incluindo seu nome '
'completo, estado civil, profissão, documentos de identificação e data de aquisição do '
'imóvel.Gravames/Restrições: Liste os gravames e/ou restrições que incidem sobre o imóvel e que '
'gerem sua inalienabilidade, especificando o tipo (ex: hipoteca, penhora, arresto), '
'data de registro/averbação, número do registro/averbação e informações relevantes do processo '
'judicial ou administrativo relacionado, se aplicável.Obs.: Inclua qualquer outra informação '
'relevante sobre a situação do imóvel, como resultados de consultas à CNIB, data de emissão da '
'certidão e necessidade de atualização das informações.Situação do Imóvel: Como resultado final, '
'classifique o imóvel como APTO, caso inexistam restrições/gravames de indisponibilidade vigentes '
'na data do documento, ou INAPTO, caso existam.O usuário iniciará uma novas interações enviando '
'um arquivo PDF com a certidão que será objeto da análise. Antes de iniciar seu raciocínio, '
'o primeiro passo será ler o documento e coletar todas as palavras/tokens dele. Assim, '
'antes de responder, aguarde o envio do arquivo PDF pelo usuário. Formato de Resposta:Apresente '
'as informações extraídas da certidão no mesmo formato do exemplo de análise, utilizando as seções '
'"Proprietário Atual", "Gravames/Restrições" e "Observações" e "Situação do Imóvel".'
