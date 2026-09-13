(function () {
  'use strict';

  // Arquivo gerado a partir de backend/app/assistant_knowledge.json.
  // Edite a fonte JSON e execute backend/scripts/sync_assistant_knowledge.py.
  window.CatalogoAssistantKnowledge = {
  "version": "24.9.0",
  "areaLabels": {
    "public": "Catálogo Digital",
    "store": "Loja e atendimento",
    "customer": "Área do cliente",
    "admin": "Painel da loja",
    "super": "Super Admin"
  },
  "sectionLabels": {
    "home": "Início",
    "dashboard": "Dashboard",
    "categories": "Categorias",
    "products": "Produtos",
    "orders": "Pedidos",
    "inventory": "Estoque",
    "coupons": "Cupons",
    "promotions": "Promoções",
    "services": "Serviços",
    "professionals": "Profissionais",
    "appointments": "Agendamentos",
    "quotes": "Orçamentos",
    "resources": "Recursos",
    "reservations": "Reservas",
    "rentalItems": "Itens de locação",
    "rentals": "Locações",
    "payments": "Pagamentos",
    "reports": "Relatórios",
    "subscription": "Meu plano",
    "privacy": "Privacidade",
    "settings": "Configurações",
    "stores": "Lojas",
    "plans": "Planos",
    "billing": "Cobrança",
    "profile": "Perfil e segurança",
    "catalog": "Produtos",
    "cart": "Carrinho",
    "contact": "Contato",
    "account": "Minha conta",
    "tracking": "Acompanhamento",
    "booking": "Agendamento"
  },
  "entries": [
    {
      "id": "overview-admin",
      "areas": [
        "admin"
      ],
      "sections": [
        "dashboard"
      ],
      "title": "Como usar o painel",
      "keywords": [
        "painel",
        "dashboard",
        "começar",
        "inicio",
        "ajuda"
      ],
      "answer": "O painel reúne a operação da sua loja. Use o menu lateral para acessar produtos, pedidos, estoque, serviços, relatórios, configurações e sua assinatura.",
      "steps": [
        "Confira o resumo no Dashboard.",
        "Escolha uma área no menu lateral.",
        "Cadastre ou edite os dados e salve.",
        "Use “Ver loja” para conferir o resultado público."
      ]
    },
    {
      "id": "categories",
      "areas": [
        "admin"
      ],
      "sections": [
        "categories"
      ],
      "title": "Categorias",
      "keywords": [
        "categoria",
        "categorias",
        "organizar",
        "grupo"
      ],
      "answer": "Categorias organizam produtos e facilitam a navegação do cliente. Crie nomes claros e evite categorias muito parecidas.",
      "steps": [
        "Abra Categorias.",
        "Clique em “+ Categoria”.",
        "Informe o nome e salve.",
        "Depois associe produtos à categoria."
      ]
    },
    {
      "id": "products",
      "areas": [
        "admin"
      ],
      "sections": [
        "products"
      ],
      "title": "Cadastrar e editar produtos",
      "keywords": [
        "produto",
        "produtos",
        "cadastrar",
        "editar",
        "preço",
        "foto",
        "imagem"
      ],
      "answer": "Produtos são os itens vendidos pela loja. Você pode definir nome, preço, categoria, imagem, estoque, variações e disponibilidade.",
      "steps": [
        "Abra Produtos.",
        "Clique em “+ Produto”.",
        "Preencha os dados principais.",
        "Envie a imagem e configure estoque/variações quando necessário.",
        "Salve e confira na loja pública."
      ]
    },
    {
      "id": "product-variations",
      "areas": [
        "admin"
      ],
      "sections": [
        "products"
      ],
      "title": "Variações e adicionais",
      "keywords": [
        "variação",
        "variacoes",
        "adicional",
        "tamanho",
        "cor",
        "sabor"
      ],
      "answer": "Use variações para opções como tamanho, cor ou sabor, e adicionais para complementos cobrados ou opcionais. Configure apenas o que o produto realmente precisa.",
      "steps": []
    },
    {
      "id": "orders",
      "areas": [
        "admin"
      ],
      "sections": [
        "orders"
      ],
      "title": "Gerenciar pedidos",
      "keywords": [
        "pedido",
        "pedidos",
        "venda",
        "status",
        "entrega"
      ],
      "answer": "Em Pedidos você acompanha as vendas e atualiza o andamento. O cliente pode acompanhar o status pelo link seguro recebido após a compra.",
      "steps": [
        "Abra Pedidos.",
        "Localize o pedido.",
        "Confira itens e dados do cliente.",
        "Atualize o status conforme a operação avança."
      ]
    },
    {
      "id": "inventory",
      "areas": [
        "admin"
      ],
      "sections": [
        "inventory"
      ],
      "title": "Controlar estoque",
      "keywords": [
        "estoque",
        "quantidade",
        "mínimo",
        "minimo",
        "sem estoque"
      ],
      "answer": "O estoque mostra as quantidades disponíveis e ajuda a evitar venda de itens indisponíveis. Ajuste quantidade e estoque mínimo conforme sua operação.",
      "steps": []
    },
    {
      "id": "coupons",
      "areas": [
        "admin"
      ],
      "sections": [
        "coupons"
      ],
      "title": "Criar cupons",
      "keywords": [
        "cupom",
        "cupons",
        "desconto",
        "codigo"
      ],
      "answer": "Cupons permitem oferecer descontos com regras controladas, como validade, limite de uso e valor mínimo.",
      "steps": [
        "Abra Cupons.",
        "Crie um novo cupom.",
        "Defina código, benefício e regras.",
        "Ative e divulgue para os clientes."
      ]
    },
    {
      "id": "promotions",
      "areas": [
        "admin"
      ],
      "sections": [
        "promotions"
      ],
      "title": "Criar promoções",
      "keywords": [
        "promoção",
        "promocoes",
        "oferta",
        "desconto"
      ],
      "answer": "Promoções destacam ofertas sem depender de um código de cupom. Use datas e condições claras para não confundir o cliente.",
      "steps": []
    },
    {
      "id": "services",
      "areas": [
        "admin"
      ],
      "sections": [
        "services"
      ],
      "title": "Cadastrar serviços",
      "keywords": [
        "serviço",
        "servicos",
        "duração",
        "duracao",
        "preço serviço"
      ],
      "answer": "Serviços são usados por negócios como barbearias, clínicas e estúdios. Cadastre nome, preço, duração e disponibilidade.",
      "steps": []
    },
    {
      "id": "professionals",
      "areas": [
        "admin"
      ],
      "sections": [
        "professionals"
      ],
      "title": "Profissionais",
      "keywords": [
        "profissional",
        "profissionais",
        "equipe",
        "agenda"
      ],
      "answer": "Cadastre profissionais quando o cliente precisar escolher quem fará o atendimento. Depois relacione-os aos serviços e horários disponíveis.",
      "steps": []
    },
    {
      "id": "appointments",
      "areas": [
        "admin"
      ],
      "sections": [
        "appointments"
      ],
      "title": "Agendamentos",
      "keywords": [
        "agendamento",
        "agenda",
        "horário",
        "horario",
        "confirmar"
      ],
      "answer": "A área de Agendamentos centraliza horários solicitados pelos clientes. Você pode acompanhar e atualizar o status de cada atendimento.",
      "steps": []
    },
    {
      "id": "quotes",
      "areas": [
        "admin"
      ],
      "sections": [
        "quotes"
      ],
      "title": "Orçamentos",
      "keywords": [
        "orçamento",
        "orcamento",
        "cotação",
        "cotacao",
        "personalizado"
      ],
      "answer": "Orçamentos atendem serviços e produtos personalizados. O cliente envia a solicitação e a loja pode analisar antes de definir condições e valor.",
      "steps": []
    },
    {
      "id": "reservations",
      "areas": [
        "admin"
      ],
      "sections": [
        "resources",
        "reservations"
      ],
      "title": "Reservas",
      "keywords": [
        "reserva",
        "reservas",
        "recurso",
        "mesa",
        "quarto"
      ],
      "answer": "Reservas servem para recursos com disponibilidade por período, como mesas, espaços ou acomodações. Cadastre os recursos e acompanhe as solicitações.",
      "steps": []
    },
    {
      "id": "rentals",
      "areas": [
        "admin"
      ],
      "sections": [
        "rentalItems",
        "rentals"
      ],
      "title": "Locações",
      "keywords": [
        "locação",
        "locacao",
        "aluguel",
        "alugar"
      ],
      "answer": "Locações controlam itens alugados por período. Cadastre os itens, disponibilidade e acompanhe cada locação.",
      "steps": []
    },
    {
      "id": "payments-admin",
      "areas": [
        "admin"
      ],
      "sections": [
        "payments"
      ],
      "title": "Pagamentos da loja",
      "keywords": [
        "pagamento",
        "pagamentos",
        "receber",
        "cliente"
      ],
      "answer": "Esta área acompanha pagamentos relacionados à operação da loja. A cobrança da assinatura do Catálogo Digital fica separada em “Meu plano”.",
      "steps": []
    },
    {
      "id": "reports",
      "areas": [
        "admin"
      ],
      "sections": [
        "reports"
      ],
      "title": "Relatórios",
      "keywords": [
        "relatório",
        "relatorio",
        "vendas",
        "resultado",
        "dashboard"
      ],
      "answer": "Relatórios ajudam a acompanhar desempenho, pedidos e operação. Use os filtros para analisar o período que realmente importa.",
      "steps": []
    },
    {
      "id": "subscription",
      "areas": [
        "admin"
      ],
      "sections": [
        "subscription"
      ],
      "title": "Meu plano e cobrança",
      "keywords": [
        "plano",
        "assinatura",
        "pix",
        "qr code",
        "mensalidade",
        "cobrança",
        "pagamento pendente"
      ],
      "answer": "Em Meu plano você vê sua assinatura, uso, cobranças e opções de upgrade. Se houver um Pix pendente, use “Ver QR Code” para reabrir a mesma cobrança sem gerar outra.",
      "steps": [
        "Abra Meu plano.",
        "Escolha um plano quando quiser contratar ou alterar.",
        "Gere o Pix.",
        "Pague pelo banco.",
        "A ativação ocorre automaticamente após a confirmação do Mercado Pago."
      ]
    },
    {
      "id": "settings",
      "areas": [
        "admin"
      ],
      "sections": [
        "settings"
      ],
      "title": "Configurações e identidade visual",
      "keywords": [
        "configuração",
        "configuracao",
        "cor",
        "cores",
        "logo",
        "banner",
        "nome",
        "whatsapp"
      ],
      "answer": "Configurações controla dados da loja e identidade visual. As cores escolhidas se espalham pela experiência pública e partes do painel.",
      "steps": [
        "Abra Configurações.",
        "Ajuste dados, nome, cores, logo ou banner.",
        "Salve.",
        "Use “Ver loja” para conferir o resultado."
      ]
    },
    {
      "id": "privacy",
      "areas": [
        "admin"
      ],
      "sections": [
        "privacy"
      ],
      "title": "Privacidade e LGPD",
      "keywords": [
        "privacidade",
        "lgpd",
        "dados",
        "cliente"
      ],
      "answer": "A área de Privacidade reúne controles e orientações para tratamento responsável dos dados. Evite coletar informações que não sejam necessárias para a operação.",
      "steps": []
    },
    {
      "id": "super-dashboard",
      "areas": [
        "super"
      ],
      "sections": [
        "dashboard"
      ],
      "title": "Visão geral da plataforma",
      "keywords": [
        "super admin",
        "dashboard",
        "plataforma",
        "resumo"
      ],
      "answer": "O Dashboard do Super Admin mostra a visão geral da plataforma: lojas, assinaturas e indicadores principais.",
      "steps": []
    },
    {
      "id": "super-stores",
      "areas": [
        "super"
      ],
      "sections": [
        "stores"
      ],
      "title": "Gerenciar lojas",
      "keywords": [
        "loja",
        "lojas",
        "cadastrar loja",
        "ativar loja",
        "bloquear loja"
      ],
      "answer": "Em Lojas você administra os estabelecimentos do SaaS, acompanha status e acessa os dados administrativos necessários.",
      "steps": []
    },
    {
      "id": "super-plans",
      "areas": [
        "super"
      ],
      "sections": [
        "plans"
      ],
      "title": "Editar planos",
      "keywords": [
        "plano",
        "planos",
        "preço",
        "limite",
        "recurso",
        "mais escolhido"
      ],
      "answer": "Os planos são editáveis pelo Super Admin. Você pode alterar nome, preço, descrição, limites, recursos, destaque e disponibilidade para novas assinaturas.",
      "steps": []
    },
    {
      "id": "super-billing",
      "areas": [
        "super"
      ],
      "sections": [
        "billing"
      ],
      "title": "Cobrança SaaS",
      "keywords": [
        "cobrança",
        "financeiro",
        "pix",
        "mercado pago",
        "assinatura",
        "inadimplente"
      ],
      "answer": "Cobrança reúne as mensalidades das lojas. O Pix é processado pelo Mercado Pago e a assinatura é atualizada após a confirmação segura do pagamento.",
      "steps": []
    },
    {
      "id": "super-profile",
      "areas": [
        "super"
      ],
      "sections": [
        "profile"
      ],
      "title": "Perfil e segurança",
      "keywords": [
        "perfil",
        "senha",
        "segurança",
        "seguranca"
      ],
      "answer": "Perfil e segurança concentra os dados da conta de Super Admin e controles de acesso. Use senhas fortes e não compartilhe credenciais.",
      "steps": []
    },
    {
      "id": "store-products",
      "areas": [
        "store",
        "public"
      ],
      "sections": [
        "catalog",
        "home"
      ],
      "title": "Comprar produtos",
      "keywords": [
        "produto",
        "produtos",
        "comprar",
        "catálogo",
        "catalogo",
        "buscar"
      ],
      "answer": "Use a busca, categorias e os cards da vitrine para encontrar produtos. Quando um item tiver opções, escolha as variações antes de adicionar ao carrinho.",
      "steps": []
    },
    {
      "id": "store-cart",
      "areas": [
        "store"
      ],
      "sections": [
        "cart",
        "catalog"
      ],
      "title": "Carrinho e finalização",
      "keywords": [
        "carrinho",
        "finalizar",
        "checkout",
        "comprar",
        "pedido"
      ],
      "answer": "O carrinho fica no topo da loja. Abra para revisar itens e total; depois use “Finalizar pedido” para informar os dados necessários e concluir.",
      "steps": []
    },
    {
      "id": "store-coupons",
      "areas": [
        "store"
      ],
      "sections": [
        "catalog"
      ],
      "title": "Usar cupom",
      "keywords": [
        "cupom",
        "desconto",
        "código",
        "codigo"
      ],
      "answer": "Se a loja oferecer cupons, consulte a área de ofertas e informe o código no momento indicado do checkout. O servidor valida as regras antes de aplicar o benefício.",
      "steps": []
    },
    {
      "id": "store-services",
      "areas": [
        "store"
      ],
      "sections": [
        "services",
        "booking"
      ],
      "title": "Serviços e agendamento",
      "keywords": [
        "serviço",
        "servico",
        "agendar",
        "agendamento",
        "horário",
        "horario"
      ],
      "answer": "Escolha um serviço, profissional quando disponível e um horário livre. Após confirmar, você recebe acesso ao acompanhamento do agendamento.",
      "steps": []
    },
    {
      "id": "store-account",
      "areas": [
        "store",
        "customer"
      ],
      "sections": [
        "account",
        "home"
      ],
      "title": "Conta do cliente",
      "keywords": [
        "conta",
        "entrar",
        "login",
        "cadastro",
        "cliente"
      ],
      "answer": "A conta do cliente guarda seu histórico daquela loja. Ela é separada do Admin e do Super Admin e mostra apenas seus próprios pedidos e agendamentos.",
      "steps": []
    },
    {
      "id": "customer-orders",
      "areas": [
        "customer"
      ],
      "sections": [
        "orders"
      ],
      "title": "Meus pedidos",
      "keywords": [
        "meus pedidos",
        "pedido",
        "histórico",
        "historico",
        "acompanhar"
      ],
      "answer": "Em Meus pedidos você vê seu histórico e pode abrir o acompanhamento quando o pedido possui link disponível.",
      "steps": []
    },
    {
      "id": "customer-appointments",
      "areas": [
        "customer"
      ],
      "sections": [
        "appointments"
      ],
      "title": "Meus agendamentos",
      "keywords": [
        "meus agendamentos",
        "agendamento",
        "agenda",
        "horário"
      ],
      "answer": "Em Meus agendamentos você confere os horários vinculados à sua conta e o andamento de cada atendimento.",
      "steps": []
    },
    {
      "id": "tracking",
      "areas": [
        "store",
        "customer"
      ],
      "sections": [
        "tracking"
      ],
      "title": "Acompanhar pedido ou agendamento",
      "keywords": [
        "acompanhar",
        "rastreamento",
        "status",
        "pedido",
        "agendamento"
      ],
      "answer": "A página de acompanhamento mostra a evolução usando um link seguro. Em pedidos, o status pode avançar de recebido até entregue; em agendamentos, de solicitado até concluído.",
      "steps": []
    },
    {
      "id": "contact",
      "areas": [
        "store"
      ],
      "sections": [
        "contact"
      ],
      "title": "Falar com a loja",
      "keywords": [
        "contato",
        "whatsapp",
        "telefone",
        "falar"
      ],
      "answer": "Use os canais oficiais exibidos na seção Contato da loja. Quando o WhatsApp estiver disponível, o botão abre a conversa diretamente com o estabelecimento.",
      "steps": []
    },
    {
      "id": "what-is-platform",
      "areas": [
        "public"
      ],
      "sections": [
        "home"
      ],
      "title": "O que é o Catálogo Digital",
      "keywords": [
        "o que é",
        "como funciona",
        "catalogo digital",
        "plataforma"
      ],
      "answer": "O Catálogo Digital é uma plataforma multi-loja e multi-segmento para catálogo, pedidos, serviços, agendamentos, reservas, locações, orçamentos e gestão.",
      "steps": []
    },
    {
      "id": "assistant-ai",
      "areas": [
        "public",
        "store",
        "customer",
        "admin",
        "super"
      ],
      "sections": [
        "home",
        "dashboard"
      ],
      "title": "Assistente com IA",
      "keywords": [
        "assistente",
        "ia",
        "chatbot",
        "ajuda",
        "perguntar",
        "como usar"
      ],
      "answer": "O assistente usa a base oficial do Catálogo Digital para explicar funcionalidades de forma curta e contextual. Quando a IA externa estiver indisponível, a ajuda local continua funcionando.",
      "steps": [
        "Abra o botão de ajuda.",
        "Digite a dúvida com o nome da função.",
        "Confira a resposta contextual da área atual."
      ]
    },
    {
      "id": "segment-personalizados",
      "areas": [
        "admin",
        "super",
        "public"
      ],
      "sections": [
        "settings",
        "stores",
        "home"
      ],
      "title": "Estamparia, personalizados e brindes",
      "keywords": [
        "estamparia",
        "personalizados",
        "brindes",
        "camisa",
        "caneca",
        "adesivo",
        "moletom",
        "chinelo"
      ],
      "answer": "O segmento Estamparia / Personalizados / Brindes usa o modelo híbrido: pode vender produtos prontos e também receber serviços, encomendas e orçamentos de personalização."
    },
    {
      "id": "billing-production-pix",
      "areas": [
        "admin",
        "super"
      ],
      "sections": [
        "subscription",
        "billing"
      ],
      "title": "Pix real da assinatura",
      "keywords": [
        "pix real",
        "produção",
        "producao",
        "aguardando pagamento",
        "mercado pago",
        "qr code"
      ],
      "answer": "Em produção, o Pix permanece pendente até o cliente pagar pelo banco. Depois da confirmação do Mercado Pago via webhook, a cobrança é aprovada e o plano é ativado automaticamente."
    },
    {
      "id": "store-online-payments",
      "areas": [
        "admin",
        "store",
        "customer"
      ],
      "sections": [
        "payments",
        "orders",
        "appointments",
        "reservations",
        "rentals"
      ],
      "title": "Pix online dos clientes da loja",
      "keywords": [
        "pix online",
        "mercado pago",
        "receber pagamento",
        "conectar mercado pago",
        "qr code",
        "pagamento cliente"
      ],
      "answer": "Cada loja pode conectar a própria conta Mercado Pago. Quando o cliente escolhe Pix online, o valor vai direto para a conta da loja e a confirmação do pagamento é automática.",
      "steps": [
        "No Admin, abra Pagamentos.",
        "Conecte a conta Mercado Pago da loja.",
        "No checkout, o cliente escolhe Pix online e informa e-mail e CPF/CNPJ.",
        "O QR Code é gerado e o status muda automaticamente após o pagamento."
      ]
    }
  ]
};
})();
