# Fase 19.3 — Interface de Plano e Cobrança

## Objetivo
Transformar o motor de assinaturas da Fase 19.2 em uma experiência operacional para o administrador da loja e para o Super Admin.

## Admin da loja
- Plano atual, preço e ciclo.
- Status da assinatura.
- Período atual e próxima cobrança.
- Provedor e forma de pagamento.
- Uso dos limites do plano.
- Recursos habilitados.
- Histórico das últimas faturas.

## Super Admin
Nova seção **Cobrança** com:
- indicadores de assinaturas ativas, atrasadas, valores a receber e recebidos;
- estado dos gateways cadastrados;
- assinaturas por loja;
- geração manual de fatura de renovação;
- cancelamento no fim do período ou imediato;
- histórico de faturas;
- registro manual de fatura paga, falha ou cancelada;
- execução manual do motor de vencimentos.

## Segurança
As ações financeiras continuam protegidas pelas rotas de Super Admin no backend. A interface não concede privilégios e não mistura mensalidades SaaS com pagamentos de pedidos das lojas.

## Gateway real
Mercado Pago/Pix Automático/PicPay continuam desacoplados. A interface mostra apenas gateways realmente configurados como disponíveis.

## Banco de dados
Não há migration nova nesta fase. A Fase 19.3 usa as tabelas criadas nas Fases 19.1 e 19.2.
