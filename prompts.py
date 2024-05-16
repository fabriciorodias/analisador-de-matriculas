from string import Template


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
