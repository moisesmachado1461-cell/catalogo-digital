# Plano de Recuperação de Desastre — Catálogo Digital

## Prioridades

1. Não alterar o banco de produção durante investigação.
2. Confirmar se o incidente é aplicação, banco, credencial ou infraestrutura.
3. Preservar logs/Sentry e registrar horário do incidente.
4. Selecionar o backup íntegro mais recente.
5. Restaurar primeiro em banco separado.
6. Validar contagens, login, lojas, pedidos, assinaturas e isolamento multi-tenant.
7. Só depois decidir sobre troca controlada do banco da aplicação.

## RPO e RTO atuais

Com backup diário, o objetivo operacional provisório é RPO de até 24 horas. O RTO depende da criação/restauração do PostgreSQL e dos testes; ainda não há SLA comercial contratado.

## Checklist de restore

- baixar artifact criptografado;
- manter `BACKUP_ENCRYPTION_KEY` disponível em local seguro;
- executar `verify_backup.py`;
- provisionar banco PostgreSQL vazio e separado;
- executar migrations;
- executar `restore_database.py`;
- validar contagens e smoke tests;
- testar Admin/Super Admin e uma loja pública;
- conferir pedidos, estoque, agendamentos, cupons e cobrança;
- somente então planejar a mudança de `DATABASE_URL` de produção.

## Rotação de credenciais após incidente

Se houver suspeita de exposição, rotacionar conforme aplicável: senha/URL do PostgreSQL, JWT secret, Cloudinary API secret, Sentry DSN quando necessário e credenciais de gateways de pagamento. Atualizar secrets na infraestrutura sem commitá-los.
