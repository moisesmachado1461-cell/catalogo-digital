# Fase 5 — Frontend visual e painel administrativo

Esta fase conecta o backend já existente a uma interface em HTML, CSS e JavaScript puro.

## Páginas

- `frontend/index.html`: apresentação e atalhos para lojas demonstrativas.
- `frontend/loja.html?slug=...`: loja pública dinâmica, adaptada às capabilities.
- `frontend/admin.html`: login e painel administrativo dinâmico.

## Funcionalidades visuais

### Loja pública
- identidade visual por loja;
- catálogo, busca e filtro por categoria;
- carrinho e checkout;
- serviços;
- consulta de disponibilidade e agendamento;
- solicitação de orçamento;
- contato/WhatsApp.

### Painel administrativo
- autenticação JWT;
- dashboard;
- produtos, pedidos e estoque quando `catalog=true`;
- serviços quando `services=true`;
- profissionais e agendamentos quando `appointments=true`;
- orçamentos quando `quotes=true`;
- edição básica da identidade e contatos da loja.

## Novos endpoints

- `GET /api/public/stores/{slug}`
- `GET /api/admin/store`
- `PATCH /api/admin/store`

Não há migration nova nesta fase.

## Rodar localmente

Backend, dentro de `backend/`:

```powershell
uvicorn app.main:app --reload
```

Frontend, em um segundo terminal, dentro de `frontend/`:

```powershell
python -m http.server 5500
```

Abra `http://127.0.0.1:5500`.
