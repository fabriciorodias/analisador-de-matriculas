# Arquivo com os modelos de dados para a API de análise de imóveis
from pydantic import BaseModel
from typing import List, Optional
from datetime import date


# Modelo para o proprietário atual
class ProprietarioAtual(BaseModel):
    nome_completo: str
    nacionalidade: str
    estado_civil: str
    profissao: str
    documentos_identificacao: List[str]
    data_aquisicao: str


# Modelo para gravames/restrições
class GravameRestricao(BaseModel):
    tipo: str
    data_registro: str
    numero_registro: str
    detalhes_processo: Optional[str]


# Modelo principal para o texto da análise
class TextoAnalise(BaseModel):
    proprietario_atual: ProprietarioAtual
    gravames_restricoes: List[GravameRestricao]
    observacoes: str
    situacao_imovel: str


# Modelo para o resultado da análise
class ResultadoAnalise(BaseModel):
    veredito: bool
    data_emissao: date
    vigente_ate: date
    prazo_cadeia_sucessoria: Optional[str]
