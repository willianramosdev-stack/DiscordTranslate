# DiscordTranslate

Uma aplicação desktop que abre o Discord Web em uma janela nativa e traduz automaticamente suas mensagens do **português para o inglês** antes de enviá-las, usando inteligência artificial.

## O que faz?

- Abre o [Discord Web](https://discord.com/app) em uma janela WebView embutida
- Adiciona um botão **"Translate"** flutuante no canto inferior direito da tela
- Quando ativado, intercepta cada mensagem que você digita e a traduz de português para inglês usando a API da [Groq](https://groq.com) com o modelo `llama-3.3-70b-versatile`
- A tradução preserva gírias, expressões de internet e o tom casual da conversa
- Quando desativado, as mensagens são enviadas normalmente, sem tradução

## Como funciona

1. A aplicação injeta um script JavaScript no Discord Web que intercepta as requisições de envio de mensagem (via `XMLHttpRequest`)
2. Ao detectar um envio, o texto original é enviado para a API da Groq, que retorna a tradução em inglês
3. A mensagem traduzida é então enviada no Discord no lugar da original

## Requisitos

- Python 3.8+
- [pywebview](https://pywebview.flowrl.com/)
- [groq](https://pypi.org/project/groq/)

Instale as dependências com:

```bash
pip install pywebview groq
```

## Configuração

1. Crie uma conta em [groq.com](https://groq.com/signup) e obtenha uma chave de API gratuita
2. Abra o arquivo `DiscordTranslate.py` e defina sua chave na variável:

```python
GROQ_API_KEY = "sua-chave-aqui"
```

## Como usar

Execute o script:

```bash
python DiscordTranslate.py
```

A janela do Discord será aberta. Clique no botão **"Translate: OFF"** no canto inferior direito para ativar a tradução automática. O botão ficará verde e exibirá **"Translate: ON"** enquanto estiver ativo.
