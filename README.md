##Analisador de Matrículas Imobiliárias para Operações de Crédito

Este projeto é um analisador de matrículas imobiliárias para operações de crédito. Ele foi desenvolvido por @fabriciorodias e utiliza a API do Google AI para analisar documentos PDF e extrair informações relevantes.  
Requisitos
Para executar este projeto, você precisará das seguintes bibliotecas Python:  
streamlit
PyPDF2
google-generativeai
python-dotenv
Você pode instalar todas as dependências necessárias com o seguinte comando:
```
pip install -r requirements.txt
```
Além disso, você precisará de uma chave de API do Google AI, que deve ser armazenada em um arquivo .env na raiz do projeto.  
Uso
Para executar o aplicativo, use o seguinte comando:
```
streamlit run analisador-de-matriculas.py
```
Depois de executar o comando acima, você pode acessar a interface do usuário do Streamlit em seu navegador.  O aplicativo permite que você faça upload de um arquivo PDF. Ele então extrai o texto do PDF e solicita à API do Google AI que analise o texto. O resultado da análise é então exibido na interface do usuário.  
Contribuindo
Contribuições são bem-vindas! Por favor, sinta-se à vontade para abrir uma issue ou pull request.  
Licença
Este projeto está licenciado sob os termos da licença MIT.