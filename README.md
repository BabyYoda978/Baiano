# Bot de convites (Discord)

Este projeto cria um bot que identifica qual invite foi usado quando alguém entra no servidor e envia uma mensagem no canal configurado com a contagem atual de convites do usuário.

## Requisitos

- Python 3.11+
- Token do bot e permissões de `Guilds`, `Guild Members` e `Guild Invites`.

## Configuração

1. Copie o arquivo de exemplo e preencha os dados:

```bash
cp config.example.json config.json
```

2. Edite `config.json`:

```json
{
  "token": "SEU_TOKEN",
  "guild_id": 123456789012345678,
  "log_channel_id": 123456789012345678,
  "message_template": "{member} FOI CONVIDADO POR {inviter} E AGORA TEM {count} invites."
}
```

- `message_template` aceita `{member}`, `{inviter}` e `{count}`.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Executar

```bash
python bot.py
```

## Observações

- O bot persiste a contagem em `data/invites.json`.
- Na primeira execução, o bot sincroniza os invites existentes.
- Para servidores grandes, garanta que o bot tenha intent de membros habilitado no Portal do Discord.
