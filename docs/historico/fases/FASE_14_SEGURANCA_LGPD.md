# Fase 14 — Segurança, LGPD e preparação para produção

Esta fase fortalece a base antes do deploy público.

## Incluído

- migration `010_security_lgpd`;
- bloqueio temporário após tentativas repetidas de login;
- registro de último login e IP;
- trilha de auditoria (`audit_logs`);
- solicitações LGPD por loja (`privacy_requests`);
- painel de privacidade e auditoria para o administrador;
- páginas públicas de Privacidade e Termos;
- cabeçalhos HTTP de segurança;
- `X-Request-ID` por requisição;
- validação de `JWT_SECRET` e CORS quando `ENVIRONMENT=production`;
- token administrativo movido para `sessionStorage`, reduzindo persistência no navegador.

## Limites desta fase

Esta fase não torna o projeto automaticamente pronto para produção. Antes de publicar comercialmente ainda são necessários HTTPS, PostgreSQL, backups, monitoramento, domínio, gateway de pagamento quando aplicável, revisão jurídica dos textos e testes finais de segurança.

## LGPD

O fluxo público registra solicitações de ACESSO, CORRECAO, EXCLUSAO, PORTABILIDADE e REVOGACAO. O sistema não entrega dados automaticamente ao solicitante: a solicitação entra como pendente para análise da loja, reduzindo o risco de exposição sem verificação de identidade.
