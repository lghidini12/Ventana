# 🪟 Ventana v1.0

Uma ferramenta de contagem de tokens versátil e refinada para arquivos e diretórios locais. 
Suporta os principais tokenizadores de LLM (Grandes Modelos de Linguagem) com uma interface gráfica (GUI) limpa em modo claro.

Desenvolvido por Luis Augusto Malaquias Ghidini.

---

## ✨ Recursos

- **Contagem de tokens em tempo real**: para arquivos e diretórios inteiros (de forma recursiva).
- **Suporte multimodelos**: GPT-4o, GPT-4, Claude (aproximado), LLaMA, LLaMA3, Gemma, Qwen e outros.
- **Instalador automático**: instala automaticamente as dependências ausentes na primeira inicialização.
- **Contagem assíncrona (Threads)**: a interface gráfica permanece responsiva com barra de progresso durante a leitura de diretórios.
- **Lista de arquivos ordenável**: clique nos cabeçalhos das colunas para ordenar os arquivos por nome ou quantidade de tokens.
- **Cores de linha alternadas**: facilidade de leitura visual para listas extensas de arquivos.
- **Detecção de arquivos binários**: ignora binários automaticamente e os sinaliza de forma clara.
- **Ações de menu de contexto**: clique com o botão direito em qualquer linha da tabela para copiar o caminho, abrir a pasta correspondente ou apagar o arquivo.
- **Configurações persistentes**: armazena em cache o último tokenizador selecionado e o tamanho da janela da interface gráfica.
- **Compatibilidade multiplataforma**: roda nativamente no Windows, macOS e Linux.
- **Integração com menus de contexto**: suporte ao clique direito no Windows Explorer (automático via instalador), no Finder do macOS (via Automator) e em gerenciadores de arquivos do Linux.

---

## 🛠️ Instalação e Requisitos

1. Requer **Python 3.9** ou superior instalado.
2. **Instalação e Integração Visual (Windows)**:
   
   O Ventana possui um instalador visual próprio que gerencia as dependências necessárias e configura a integração com o Windows Explorer de forma simples.
   
   * **Método Direto (Recomendado)**: Dê um duplo clique sobre o arquivo `instalar.pyw` no Windows Explorer.
   * **Via Terminal (Alternativo)**: Se preferir, execute no terminal:
     ```cmd
     python instalar.pyw
     ```
   
   *(O instalador abrirá uma tela amigável permitindo que você instale/atualize as dependências ou remova a integração com apenas um clique, solicitando privilégios de administrador de forma nativa).*

### 🍎 Compatibilidade com macOS e Linux

O aplicativo principal (`app/ventana.pyw`) é multiplataforma e roda nativamente no macOS e Linux.

1. **Instale as dependências via terminal**:
   ```bash
   pip3 install tiktoken Pillow transformers anthropic
   ```
2. **Execute o aplicativo**:
   ```bash
   python3 app/ventana.pyw <caminho_do_arquivo_ou_pasta>
   ```

> **Dica para Mac**: Para integrar ao clique direito do Finder no macOS, abra o aplicativo nativo **Automator**, crie uma **Ação Rápida (Quick Action)** que receba arquivos/pastas no Finder, adicione a ação *"Executar Script do Shell"* passando a entrada como argumento e coloque o comando `python3 "/caminho/para/app/ventana.pyw" "$1"`.

> **Dica para Linux (Nautilus)**: Para integrar ao clique direito do gerenciador de arquivos Nautilus, crie um script em `~/.local/share/nautilus/scripts/Ventana` com o comando `python3 "/caminho/para/app/ventana.pyw" "$1"` e dê permissão de execução a ele (`chmod +x`).

---

## 💡 Como Usar

### Pela linha de comando

```bash
python ventana.pyw <caminho_do_arquivo_ou_pasta>
```

### Pelo Windows Explorer

Após realizar a instalação opcional acima, basta clicar com o botão direito sobre qualquer arquivo ou diretório no seu Windows Explorer e selecionar **Ventana**.

---

## 🤖 Tokenizadores Disponíveis

| Grupo | Modelos Suportados |
| :--- | :--- |
| **OpenAI** | gpt-4o, gpt-4o-mini, o1, o1-mini, o3, o3-mini, o4-mini, gpt-4, gpt-3.5-turbo |
| **Anthropic** | claude (por aproximação estatística) |
| **Meta** | llama, llama3 |
| **Google** | gemma |
| **Alibaba** | qwen |

> **Nota:** Como o tokenizador do Claude é proprietário e não está disponível publicamente de forma aberta no Python, a contagem de tokens para Claude utiliza um algoritmo aproximado com margem de erro estimada de ±10–15%.
>
> Os tokenizadores hospedados no HuggingFace (LLaMA, Gemma, Qwen) realizam o download automático de seus respectivos arquivos na primeira utilização. Esse processo pode demorar alguns instantes de acordo com a velocidade de conexão com a Internet.
>
> **Tratamento de Binários:** Arquivos que não possuem texto puro (como imagens, arquivos de áudio, vídeos, PDFs e executáveis compactados) são identificados automaticamente. O aplicativo atribui contagem zero a eles e os sinaliza como "Binário" na tabela para manter a precisão do contexto de texto.

---

## 🔧 Adicionando um Tokenizador Personalizado

Se desejar expandir os modelos disponíveis:
1. Encontre a referência do tokenizador no [HuggingFace](https://huggingface.co/docs/transformers) (dê preferência a variantes do tipo `...Fast`).
2. Adicione uma cláusula `elif` na função `get_tokenizer()` dentro do arquivo `app/ventana.pyw`.
3. Adicione o novo identificador de modelo nas constantes `TOKENIZER_GROUPS` e `FLAT_TOKENIZERS` do script.

---

## 🩺 Resolução de Problemas

Caso a interface gráfica feche ou apresente comportamento atípico, execute o aplicativo diretamente pelo terminal/console do Windows para analisar a saída e erros:

```bash
python app/ventana.pyw app/ventana.pyw
```

---

## 📄 Licença

O aplicativo **Ventana** é um software livre sob os termos da licença **GNU Affero General Public License v3**. Consulte o arquivo [LICENSE](LICENSE) para ler os termos integrais.

*Baseado no projeto original [token-counter](https://github.com/tropptr-torrptrop/token-counter) de autoria de NickNau.*
