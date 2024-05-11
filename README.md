### Analisador de Matrículas Imobiliárias para Operações de Crédito

Faz a análise da certidão de um imóvel e informa se ele está APTO ou INAPTO para ser usado como garantia numa operação de crédito bancário.

Este app é o projeto de @fabriciorodias para a Imersão IA Alura - Google.

Feito com Python, Streamlit e Google AI.

Ele já está online e disponível via Heroku. Para acessá-lo, basta clicar no link abaixo:

https://analisador-de-matriculas-874a9c6e8cb5.herokuapp.com/

#### Como utilizar
Duas certidões de matrícula imobiliária estão disponíveis no diretório 'certidoes'. Para testar o app, basta fazer o upload de uma dessas certidões na interface do usuário.

São duas certidões públicas, utilizadas para fins de teste.

O app funciona com qualquer certidão de matrícula imobiliária, desde que esteja em formato PDF (texto).

Este projeto é um analisador de matrículas imobiliárias para operações de crédito. Ele foi desenvolvido por @fabriciorodias e utiliza a API do Google AI para analisar documentos PDF e extrair informações relevantes.

O aplicativo permite que você faça upload de um arquivo PDF. Ele então extrai o texto do PDF e solicita à API do Google AI que analise o texto. O resultado da análise é então exibido na interface do usuário.

A análise inclui informações como o nome do proprietário, o endereço do imóvel, a área do terreno, a área construída, o número da matrícula, a data de registro, a data de atualização, a data de validade e o cartório de registro.
Por fim, a análise informa se o imóvel está APTO ou INAPTO para ser usado como garantia em uma operação de crédito bancárias.

#### Google Colab
O projeto também está disponível no Google Colab. Para acessá-lo, clique no link abaixo:

https://colab.research.google.com/drive/1hqVXuSI32w68xXiC55gIcGOTJ3RcS-_u?usp=sharing


#### Requisitos
Para executar este projeto, você precisará das seguintes bibliotecas Python:  
streamlit
PyPDF2
google-generativeai
python-dotenv

Você pode instalar todas as dependências necessárias com o seguinte comando:
```
pip install -r requirements.txt
```
Para executar localmente, você precisará de uma chave de API do Google AI, que deve ser armazenada no arquivo 'keys.env' na raiz do projeto.  

Uso
Para executar o aplicativo, use o seguinte comando:

```
streamlit run analisador-de-matriculas.py
```

Depois de executar o comando acima, você pode acessar a interface do usuário do Streamlit em seu navegador.

#### Contribuindo
Contribuições são bem-vindas! Por favor, sinta-se à vontade para abrir uma issue ou pull request.  

#### Licença
Este projeto está licenciado sob os termos da licença MIT.