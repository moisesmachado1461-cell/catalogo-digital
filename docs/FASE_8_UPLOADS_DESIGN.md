# Fase 8 — Uploads de imagens e vitrine profissional

A Fase 8 transforma a personalização visual em uma funcionalidade real do painel, sem exigir que o administrador hospede imagens manualmente em outro site.

## Entregas

- Upload autenticado de imagens para cada loja.
- Logo e banner enviados diretamente no painel.
- Upload de imagens para produtos, categorias, serviços e profissionais.
- Isolamento de arquivos por `store_id`.
- Arquivos renomeados com UUID, sem confiar no nome enviado pelo usuário.
- Validação de formato e tamanho.
- Conversão e otimização automática para WebP.
- Redimensionamento automático conforme o tipo de imagem.
- Pasta `uploads/` servida pelo FastAPI em desenvolvimento.
- Nova vitrine pública com hero, banner, logo, filtros em chips, cards mais completos e carrinho mobile.
- Meta description e título atualizados com os dados da empresa.

## Segurança do upload

O endpoint administrativo é:

`POST /api/admin/uploads/images`

Ele aceita somente JPG, PNG e WebP, limita o arquivo a 8 MB, valida o conteúdo como imagem e determina a loja usando o usuário autenticado. O frontend não envia nem escolhe `store_id`.

Cada arquivo é salvo em uma estrutura semelhante a:

`uploads/store_1/product/<uuid>.webp`

## Desenvolvimento x produção

Nesta fase, os arquivos são guardados no disco local porque o projeto ainda está sendo executado localmente. Em produção, a mesma abstração deverá ser migrada para armazenamento de objetos, como S3 ou Cloudflare R2. O banco continua armazenando somente a URL da imagem.

## Banco de dados

Não há migration nova. As colunas `logo_url`, `banner_url` e `image_url` já existiam nas tabelas necessárias.

## Nova dependência

A Fase 8 adiciona `Pillow`, usado para validar, redimensionar e converter imagens.

Ao atualizar uma instalação existente, execute:

```powershell
pip install -r requirements.txt
```

## Arquivos locais que devem ser preservados

- `backend/.venv`
- `backend/.env`
- `backend/catalogo.db`
- `backend/uploads/`, depois que começar a enviar imagens

A versão da API passa para `8.0.0`.
