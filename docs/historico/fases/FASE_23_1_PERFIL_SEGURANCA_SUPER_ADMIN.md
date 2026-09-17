# Fase 23.1 — Perfil e Segurança do Super Admin

Esta etapa adiciona gerenciamento real da conta principal do Super Admin.

## Funcionalidades

- alterar nome;
- alterar e-mail;
- alterar senha;
- exigir senha atual ao trocar o e-mail;
- exigir senha atual ao trocar a senha;
- política mínima de senha forte;
- encerrar outras sessões;
- emissão automática de novo token para manter a sessão atual;
- auditoria das alterações sensíveis;
- interface premium integrada ao Super Admin.

## Segurança de sessões

Foi adicionado `users.token_version`.

Cada JWT passa a carregar a versão da sessão (`ver`). Quando a senha é alterada ou
o Super Admin usa "Encerrar outras sessões", o `token_version` é incrementado.
Tokens anteriores deixam de ser aceitos e a sessão atual recebe um novo JWT.

## Endpoints

- `GET /api/super-admin/profile`
- `PATCH /api/super-admin/profile`
- `POST /api/super-admin/profile/password`
- `POST /api/super-admin/profile/sessions/revoke-others`

Todos exigem autenticação de `SUPER_ADMINISTRADOR`.

## Migration

`013_super_admin_account_security.py`

Adiciona:

- `users.token_version`

## Observações

Nenhuma senha é devolvida pela API.
Nenhuma senha ou token é salvo no frontend além do JWT da sessão em `sessionStorage`.
As alterações são registradas no audit log sem armazenar a senha informada.
