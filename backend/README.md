# Upthon backend (refatorado)

## Rodar

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # opcional
python run.py               # ou: uvicorn app.main:app --port 5000
```

Os endpoints são os mesmos de antes (`/api/...`), então o front não precisa mudar.

## Rodar tudo com um comando (uso local)

```bash
python start.py      # na pasta do projeto (onde estão backend/ e frontend/)
```

Ele monta o front (yarn ou npm) só se não existir build ou se o código do front mudou, e sobe o back.
Opções: `--rebuild` (força o build) e `--no-build`. Os passos manuais, se preferir:

```bash
cd frontend && npm install && npm run build     # uma vez, e de novo quando mudar o front
cd ../backend && python run.py                  # abra http://localhost:5000
```

O back serve a pasta `frontend/build` (e entrega o `index.html` nas rotas do React, como `/dashboard`).
Sem a pasta `build`, só a API sobe, como antes. Para desenvolver o front use `npm start` (porta 3000).

## Versão de terminal (sem front)

```bash
cd backend
python upthon.py --root /caminho/dos/cursos     # a raiz fica salva em cli_config.json
python upthon.py                                 # usa a raiz salva
```

Lista as subpastas numeradas (com contagem de vídeos/PDFs). Comandos: `<n>` upar a pasta n, `a <n>` abrir,
`..` voltar, `r` raiz, `u` upar a pasta atual, `d` definir raiz, `p` pendentes, `q` sair.
Ao escolher o índice ele pergunta o tipo (canal privado ou supergrupo com tópicos), o nome do canal
(Enter = nome da pasta) e confirma. Em `p` lista os pendentes (enviados/total) e retoma pelo índice; o tipo
vem da fila quando já há tópicos criados, senão ele pergunta. Se não houver login salvo, pede api_id, api_hash,
telefone e código. Ctrl+C interrompe; nada é reenviado ao retomar. Usa o mesmo banco e as mesmas filas da API.

## Testar

```bash
pip install -r requirements-dev.txt
pytest
```

## Estrutura

```
backend/
├── run.py                      # ponto de entrada (antigo main.py)
├── app/
│   ├── main.py                 # create_app: CORS, handlers de erro, routers
│   ├── container.py            # monta e liga os services (antigo app.state.*)
│   ├── core/                   # config.py (env + constantes), errors.py, logging.py
│   ├── api/
│   │   ├── deps.py
│   │   └── routes/             # auth, files, uploads, bots, dashboard (só HTTP)
│   ├── schemas/                # modelos Pydantic (antigo model.py, parte 1)
│   ├── db/repository.py        # SQLite (antigo model.py, parte 2)
│   ├── services/
│   │   ├── telegram_session.py # login, auto-login, perfil (admin)
│   │   ├── workers.py          # TelegramWorker + WorkerPool + envio de álbuns
│   │   ├── channels.py         # criar canal, tópicos, acesso dos workers
│   │   ├── upload_service.py   # orquestra o upload (antigo controller.upload)
│   │   ├── scanner.py          # varre a pasta, plano de tags, ordenação
│   │   ├── rendering.py        # textos HTML enviados ao Telegram
│   │   ├── queue_store.py      # fila assets/upload_<id>.json
│   │   ├── media.py            # thumbnails, ffmpeg, upload paralelo
│   │   ├── file_browser.py     # árvore, mover, reordenar
│   │   ├── dashboard.py        # estatísticas das filas
│   │   ├── bot_service.py      # valida token na Bot API
│   │   └── folder_picker.py    # tkinter, importado sob demanda
│   └── utils/                  # só helpers puros: text.py, paths.py
└── tests/
```

De onde veio cada coisa: `controller.py` virou `workers`, `channels`, `upload_service` e `rendering`;
`utils.py` virou `scanner`, `rendering`, `queue_store`, `media` e `utils/`; `main.py` virou `main`
+ `routes/*`; `model.py` virou `schemas/*`, `db/repository` e `telegram_session`.

## Variáveis de ambiente (todas opcionais)

| Variável | Padrão |
|---|---|
| `UPTHON_DB_PATH` | `backend/db.db` (antes dependia da pasta de onde você rodava) |
| `UPTHON_ASSETS_DIR` | `backend/assets` |
| `UPTHON_CORS_ORIGINS` | `http://localhost:3000` (separar por vírgula) |
| `UPTHON_DEFAULT_THUMBNAIL` | `assets/default_thumb.jpg` (antes: `D:\ghost\upthon\backend\test\upload\bio.jpg`) |
| `UPTHON_SEPARATOR_STICKER_SET` | `vizualseparator` |
| `UPTHON_HOST` / `UPTHON_PORT` | `127.0.0.1` / `5000` |
| `UPTHON_FRONTEND_DIR` | `../frontend/build` |
| `UPTHON_FFMPEG_PRESET` | `veryfast` (antes: `fast`; `slow` = menor arquivo, mais lento) |

Se o seu `db.db` ficava em outra pasta, aponte `UPTHON_DB_PATH` para ele.

## Contrato com o front

Erros são sempre `{"detail": ...}` (o front mostra essa mensagem). Dois pontos mudaram por segurança:
`GET /api/bots/infos` não devolve mais `bot_token` (vem `token_preview`, e o avatar é uma `data:` URI) e
`POST /api/auth/verify` não devolve mais a string de sessão. Veja `../MUDANCAS.md`.
