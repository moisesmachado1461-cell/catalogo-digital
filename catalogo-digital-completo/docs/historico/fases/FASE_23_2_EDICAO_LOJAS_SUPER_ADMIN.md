# Fase 23.2 — Edição de lojas no Super Admin

A Fase 23.2 restaura e amplia a edição de lojas diretamente no Super Admin.

## O Super Admin pode editar
- nome da loja;
- slug/endereço público;
- segmento/categoria de negócio;
- cores principal e secundária;
- descrição;
- WhatsApp, telefone e e-mail da loja;
- endereço, cidade, UF e CEP;
- nome e e-mail do administrador principal.

A edição preserva o `store_id`, pedidos, clientes, produtos, agendamentos, assinatura e histórico.

## Segurança
- rota protegida por Super Admin;
- validação de slug duplicado;
- validação de e-mail duplicado do administrador;
- auditoria da alteração;
- nenhuma senha é alterada por esta tela.

Não há migration de banco nesta fase.
