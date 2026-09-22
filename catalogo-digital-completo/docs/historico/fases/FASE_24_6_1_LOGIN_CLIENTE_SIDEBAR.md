# Fase 24.6.1 — Login premium do cliente e sidebar compacta

## Objetivo

Melhorar a experiência visual antes do lançamento sem alterar o modelo de dados.

## Admin

- controle de recolher/expandir maior, tematizado e fora da área de rolagem;
- quando recolhida, a sidebar oculta menus, identificação da loja e rodapé;
- permanece somente uma faixa mínima com a marca principal e o controle para reabrir;
- comportamento mobile continua separado pelo menu lateral.

## Cliente final

- `cliente.html` passa a funcionar como uma tela de acesso dedicada, equivalente em qualidade aos logins de Admin e Super Admin;
- cores principal e secundária da loja dominam a composição visual;
- logo/nome da loja aparecem no login;
- login e cadastro possuem transição por abas, mostrar/ocultar senha, botões temáticos e feedback visual;
- acesso à área do cliente permanece disponível no cabeçalho da loja antes, durante e depois de uma compra;
- após autenticação, o usuário segue para o portal com pedidos e agendamentos.

## Banco

Nenhuma migration nova.

## Versão

`24.6.1`
