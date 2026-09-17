# Fase 24.9.1 — OAuth/PKCE Marketplace

Hotfix do fluxo de conexão das lojas com Mercado Pago.

## Correção

A URL de autorização PKCE passa a enviar `code_method=S256`, conforme a documentação atual do Mercado Pago.

Também foram adicionadas mensagens mais específicas para erros de autorização, estado, expiração e troca de token.

Não altera banco nem regras de pagamento.
