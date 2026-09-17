# Fase 16 — Multi-dispositivo, responsividade e PWA

## Objetivo
Garantir que a mesma loja e os mesmos painéis funcionem em celular, tablet, notebook e desktop, sem criar versões separadas.

## Alterações
- Layout responsivo reforçado em 320px+, tablets, desktop e telas grandes.
- Alvos de toque com pelo menos ~44px, inputs com 16px para evitar zoom automático no iPhone e suporte a safe-area.
- Tabelas e menus com rolagem horizontal segura no touch.
- API detecta automaticamente o hostname do frontend em ambiente local/LAN.
- CORS de desenvolvimento permite origens privadas da rede local (10.x, 172.16-31.x e 192.168.x). Produção continua restrita às origens configuradas.
- Manifest + service worker: base PWA para instalação em dispositivos quando servido por HTTPS (ou localhost).
- Respeito a `prefers-reduced-motion`.

## Teste em outro aparelho na mesma Wi-Fi
Backend:
`uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

Frontend:
`python -m http.server 5500 --bind 0.0.0.0`

No Windows, descubra o IPv4 com `ipconfig`. No celular, use:
`http://SEU_IP:5500`

Exemplo: `http://192.168.0.15:5500`.

O PC e o celular precisam estar na mesma rede e o Firewall do Windows deve permitir Python em rede privada.

## Produção
Quando publicado com HTTPS, qualquer aparelho usa a mesma URL. O frontend utiliza a API no mesmo domínio por padrão, salvo configuração explícita em `catalogo_api_base`.
