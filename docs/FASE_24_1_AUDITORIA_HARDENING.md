# Fase 24.1 — Auditoria automatizada e hardening

Primeiro bloco da Fase 24. O objetivo é reduzir regressões antes da preparação comercial sem alterar regras centrais de negócio.

## Hardening aplicado

- versão do backend centralizada em `app/version.py`;
- verificação de senha com custo simulado também quando o e-mail não existe, reduzindo vazamento por tempo;
- validação mais rígida de algoritmo JWT, duração do token e limites de login;
- validação mais rígida das origens CORS em produção;
- IDs de requisição externos passam a ser aceitos apenas em formato curto e seguro;
- respostas autenticadas/sensíveis recebem `Cache-Control: no-store`;
- rate limiter de login ganhou limpeza periódica e limite de memória;
- frontend usa `cache: no-store` nas chamadas da API e timeout de 90 segundos;
- cache PWA atualizado para a Fase 24.1.

## Ferramentas de auditoria

`backend/scripts/phase24_project_audit.py` verifica sintaxe Python/JavaScript, cadeia Alembic, higiene de segredos, `.gitignore`, referências locais do frontend, versão e guardas básicas de Admin/Super Admin.

`backend/scripts/production_smoke_check.py` testa health, cabeçalhos de segurança, CORS e páginas públicas do deploy sem autenticação e sem alterar dados.

`backend/scripts/verify_backup.py` verifica se um arquivo de backup lógico `.json.gz` está íntegro estruturalmente. Isso **não é** um teste real de restauração.

## Pontos que continuam pendentes antes do lançamento comercial

- automação de backup/offsite e teste real de restauração;
- rotação de credenciais que possam ter sido expostas durante desenvolvimento;
- reduzir a permissão da chave Cloudinary para privilégio mínimo;
- trocar senhas de demonstração;
- gateway automático real de cobrança SaaS, quando houver conta elegível/autorizada;
- revisão funcional autenticada cruzando duas lojas distintas.

Não há migration nesta fase. Backend: `24.1.0`.
