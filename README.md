
## Início rápido (web)

### Linux Mint (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-tk ffmpeg nodejs npm
sudo npm install -g yarn        # opcional: sem o yarn ele usa o npm

git clone https://github.com/catenem/upthon
cd upthon
python3 start.py
```

### Windows

Instale antes (PowerShell, com o `winget` do Windows 10/11):

```powershell
winget install Git.Git
winget install Python.Python.3.12
winget install Gyan.FFmpeg
winget install OpenJS.NodeJS.LTS
npm install -g yarn             # opcional: sem o yarn ele usa o npm
```

Feche e abra o PowerShell (para o PATH atualizar) e rode:

```powershell
git clone https://github.com/catenem/upthon
cd upthon
python start.py
```

No Windows o tkinter já vem com o Python. Se o `python` não for encontrado, use `py start.py`.
Para ativar o venv à mão (usar a CLI): `venv\Scripts\activate`.
O fluxo de Windows está descrito a partir do código (caminhos e comandos tratados para os dois sistemas),
mas foi testado só no Linux.

Abra **http://localhost:5000**. Na primeira vez ele cria o `./venv`, instala o `backend/requirements.txt`,
instala as dependências do front e monta o build. Nas seguintes só refaz o que mudou.

### Flags do `start.py`

| Flag | O que faz |
|---|---|
| *(nenhuma)* | cria o venv se faltar, instala dependências se mudaram, monta o front se mudou, sobe o back |
| `--rebuild` | força o build do front |
| `--install` | força `yarn install` (ou `npm install`) antes do build |
| `--no-build` | não mexe no front, só sobe o back |
| `--no-venv` | usa o Python atual, sem criar nem usar o venv |

Exemplos: `python start.py --install --rebuild` (reinstala e remonta o front), `python start.py --no-build` (só a API).

## Terminal (CLI)

```bash
cd backend
python upthon.py --root /caminho/dos/cursos     # a raiz fica salva em cli_config.json
python upthon.py                                 # usa a raiz salva
```

Se não estiver dentro do venv, ative-o antes: `source ../venv/bin/activate`.

| Flag | O que faz |
|---|---|
| `--root PASTA` | pasta com os cursos (subpastas numeradas); fica salva para as próximas vezes |

### Comandos dentro da CLI

| Comando | Ação |
|---|---|
| `<n>` | upar a pasta de índice n (pergunta o tipo do canal, o nome e confirma) |
| `a <n>` | abrir a pasta n |
| `..` | voltar (não sai da raiz fixa) |
| `r` | ir para a pasta raiz |
| `u` | upar a pasta atual |
| `d` | definir a pasta raiz |
| `p` | listar uploads pendentes e retomar pelo índice |
| `q` | sair |

Tipo do canal: `1` canal privado, `2` supergrupo com tópicos. Se não houver login salvo, a CLI pede
api_id, api_hash, telefone e o código do Telegram. **Ctrl+C** interrompe; retome depois em `p`.

## Estrutura de uma pasta de curso

```
Meu Curso/
├── 01_Modulo/            <- vira uma matéria (tópico, se for supergrupo)
│   ├── 01_Aula/          <- subpasta (ganha cabeçalho e separador)
│   │   ├── 01_intro.mp4
│   │   └── 01_apostila.pdf   <- PDF herda a tag do vídeo de mesmo número
│   └── 02_extra.pdf
└── thumb.jpg             <- thumbnail/abertura (procura subindo as pastas)
```


## Segurança

- `backend/db.db` guarda suas credenciais e a **sessão do Telegram** (equivale à senha da conta).
  Nunca commite nem compartilhe esse arquivo; ele já está no `.gitignore`.
- A API foi feita para uso local (`127.0.0.1`). Não exponha a porta na internet.
- A API nunca devolve o token dos bots nem a string de sessão.

## Problemas comuns

| Sintoma | Causa / solução |
|---|---|
| `react-scripts: not found` | dependências do front incompletas: `python start.py --install --rebuild` |
| "Could not find a required file: index.html" | falta `frontend/public/index.html` |
| Botão "Selecionar Pasta" dá erro | instale `python3-tk` ou digite o caminho |
| Arquivos foram para o tópico General | use a versão atual: ela mapeia/cria todos os tópicos antes de enviar |
| FloodWait | com uma só conta ele espera o tempo pedido; cadastre bots para girar entre contas |
