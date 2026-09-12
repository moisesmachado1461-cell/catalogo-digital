from datetime import datetime, time, timezone
from decimal import Decimal

from app.database import SessionLocal
from app.models import (
    BusinessCategory,
    BusinessModel,
    Category,
    Inventory,
    Product,
    PaymentSettings,
    Plan,
    Subscription,
    Resource,
    RentalItem,
    Coupon,
    Promotion,
    PromotionItem,
    Professional,
    ProfessionalHours,
    ProfessionalService,
    Service,
    Store,
    User,
)
from app.security import hash_password
from app.utils.text import slugify
from app.services.subscription_service import snapshot_subscription_terms

MODELS = [
    ("Varejo", "VAREJO", "Compra produtos", "COMPRAR", {"catalog": True, "cart": True, "checkout": True, "inventory": True, "payments": True}),
    ("Alimentação", "ALIMENTACAO", "Pede comida", "PEDIR", {"catalog": True, "cart": True, "checkout": True, "delivery": True, "payments": True}),
    ("Agendamento", "AGENDAMENTO", "Agenda serviços", "AGENDAR", {"services": True, "appointments": True, "payments": True}),
    ("Orçamento", "ORCAMENTO", "Solicita orçamento", "SOLICITAR_ORCAMENTO", {"services": True, "quotes": True}),
    ("Reserva", "RESERVA", "Reserva períodos", "RESERVAR", {"reservations": True, "payments": True}),
    ("Locação", "LOCACAO", "Aluga itens", "ALUGAR", {"rentals": True, "payments": True}),
    ("Serviços", "SERVICOS", "Contrata serviços", "CONTRATAR", {"services": True, "payments": True}),
    ("Híbrido", "HIBRIDO", "Combina fluxos", "EXPLORAR", {"catalog": True, "services": True, "cart": True, "payments": True}),
]

CATS = [
    ("Mercado / Supermercado", "mercado-supermercado", "VAREJO"),
    ("Loja de roupas", "loja-de-roupas", "VAREJO"),
    ("Loja de calçados", "loja-de-calcados", "VAREJO"),
    ("Loja de eletrônicos e informática", "loja-eletronicos-informatica", "VAREJO"),
    ("Farmácia / Drogaria", "farmacia-drogaria", "VAREJO"),
    ("Cosméticos e perfumaria", "cosmeticos-perfumaria", "VAREJO"),
    ("Pet Shop", "pet-shop", "HIBRIDO"),
    ("Materiais de construção", "materiais-construcao", "VAREJO"),
    ("Móveis e decoração", "moveis-decoracao", "VAREJO"),
    ("Autopeças", "autopecas", "VAREJO"),
    ("Restaurante", "restaurante", "ALIMENTACAO"),
    ("Lanchonete / Hamburgueria", "lanchonete-hamburgueria", "ALIMENTACAO"),
    ("Pizzaria", "pizzaria", "ALIMENTACAO"),
    ("Padaria", "padaria", "ALIMENTACAO"),
    ("Doceria / Confeitaria", "doceria-confeitaria", "ALIMENTACAO"),
    ("Barbearia", "barbearia", "AGENDAMENTO"),
    ("Salão de beleza", "salao-de-beleza", "AGENDAMENTO"),
    ("Manicure / Nail designer", "manicure-nail-designer", "AGENDAMENTO"),
    ("Clínica de estética", "clinica-estetica", "AGENDAMENTO"),
    ("Massoterapia / Spa", "massoterapia-spa", "AGENDAMENTO"),
    ("Oficina mecânica", "oficina-mecanica", "HIBRIDO"),
    ("Eletricista", "eletricista", "ORCAMENTO"),
    ("Encanador", "encanador", "ORCAMENTO"),
    ("Pintor", "pintor", "ORCAMENTO"),
    ("Limpeza e conservação", "limpeza-conservacao", "ORCAMENTO"),
    ("Assistência técnica", "assistencia-tecnica", "ORCAMENTO"),
    ("Fotógrafo / Estúdio fotográfico", "fotografo-estudio", "AGENDAMENTO"),
    ("Hotel / Pousada", "hotel-pousada", "RESERVA"),
    ("Espaço para eventos / Festas", "espaco-eventos-festas", "RESERVA"),
    ("Aluguel de equipamentos e produtos", "aluguel-equipamentos-produtos", "LOCACAO"),
    ("Estamparia / Personalizados / Brindes", "estamparia-personalizados-brindes", "HIBRIDO"),
    ("Outro negócio", "outro-negocio", "HIBRIDO"),
]

CATEGORY_CAPABILITY_OVERRIDES = {
    "estamparia-personalizados-brindes": {
        "catalog": True,
        "services": True,
        "cart": True,
        "checkout": True,
        "inventory": True,
        "quotes": True,
        "payments": True,
        "delivery": True,
        "coupons": True,
        "promotions": True,
    },
}


SUPER_ADMIN_EMAIL = "superadmin@catalogodigital.dev"
SUPER_ADMIN_PASSWORD = "SuperAdmin@2026"


def ensure_super_admin(db, now):
    user = db.query(User).filter(User.email == SUPER_ADMIN_EMAIL).first()
    if not user:
        user = User(
            name="Super Administrador",
            email=SUPER_ADMIN_EMAIL,
            password_hash=hash_password(SUPER_ADMIN_PASSWORD),
            role="SUPER_ADMINISTRADOR",
            store_id=None,
            is_active=True,
            email_verified=True,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
    return user

DEMO_CATEGORIES = ["Hortifruti", "Bebidas", "Mercearia", "Laticínios", "Limpeza"]
DEMO_PRODUCTS = [
    ("Banana Prata", "Hortifruti", "HORT-001", "6.99", 50),
    ("Maçã Gala", "Hortifruti", "HORT-002", "9.90", 40),
    ("Tomate", "Hortifruti", "HORT-003", "7.49", 35),
    ("Água Mineral 1,5L", "Bebidas", "BEB-001", "3.49", 80),
    ("Refrigerante Cola 2L", "Bebidas", "BEB-002", "10.99", 45),
    ("Suco de Laranja 1L", "Bebidas", "BEB-003", "8.50", 30),
    ("Arroz 5kg", "Mercearia", "MER-001", "29.90", 25),
    ("Feijão Carioca 1kg", "Mercearia", "MER-002", "8.99", 40),
    ("Macarrão 500g", "Mercearia", "MER-003", "5.49", 60),
    ("Café 500g", "Mercearia", "MER-004", "19.90", 30),
    ("Leite Integral 1L", "Laticínios", "LAT-001", "5.99", 70),
    ("Queijo Muçarela 500g", "Laticínios", "LAT-002", "24.90", 20),
    ("Iogurte Natural", "Laticínios", "LAT-003", "4.79", 35),
    ("Detergente 500ml", "Limpeza", "LIM-001", "2.99", 55),
    ("Sabão em Pó 1kg", "Limpeza", "LIM-002", "14.90", 25),
]

BARBER_SERVICES = [
    ("Corte Masculino", "40.00", 45),
    ("Barba", "30.00", 30),
    ("Corte + Barba", "65.00", 70),
    ("Sobrancelha", "20.00", 20),
]




HOTEL_RESOURCES = [
    ("Quarto Standard", "QUARTO", 2, "189.90"),
    ("Quarto Família", "QUARTO", 4, "289.90"),
    ("Suíte Premium", "SUITE", 2, "379.90"),
]

RENTAL_ITEMS = [
    ("Furadeira Profissional", "LOC-001", "49.90", "150.00", 4),
    ("Lavadora de Alta Pressão", "LOC-002", "79.90", "250.00", 3),
    ("Escada Extensível", "LOC-003", "39.90", "100.00", 5),
]
ELECTRICIAN_SERVICES = [
    ("Visita técnica", "0.00", 60),
    ("Instalação elétrica", "0.00", 90),
    ("Manutenção e reparo elétrico", "0.00", 90),
    ("Quadro elétrico e disjuntores", "0.00", 120),
    ("Iluminação e luminárias", "0.00", 60),
]


def ensure_user(db, *, store, name, email, password, now):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role="ADMINISTRADOR_DA_LOJA",
            store_id=store.id,
            is_active=True,
            email_verified=True,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
    return user


def seed_market(db, mmap, now):
    business_category = db.query(BusinessCategory).filter_by(slug="mercado-supermercado").one()
    store = db.query(Store).filter_by(slug="mercado-bom-preco").first()
    if not store:
        store = Store(
            name="Mercado Bom Preço",
            slug="mercado-bom-preco",
            business_category_id=business_category.id,
            business_model_id=mmap["VAREJO"].id,
            capabilities={**mmap["VAREJO"].default_capabilities, "coupons": True, "promotions": True},
            description="Loja demonstrativa",
            primary_color="#7C3AED",
            secondary_color="#4F46E5",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(store)
        db.flush()

    ensure_user(
        db,
        store=store,
        name="Administrador Demo",
        email="admin@mercadobompreco.com",
        password="Admin@12345",
        now=now,
    )
    db.flush()

    category_map = {}
    for index, name in enumerate(DEMO_CATEGORIES, 1):
        category = db.query(Category).filter_by(store_id=store.id, slug=slugify(name)).first()
        if not category:
            category = Category(
                store_id=store.id,
                name=name,
                slug=slugify(name),
                sort_order=index,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            db.add(category)
            db.flush()
        category_map[name] = category

    for name, category_name, sku, price, stock in DEMO_PRODUCTS:
        product = db.query(Product).filter_by(store_id=store.id, sku=sku).first()
        if not product:
            product = Product(
                store_id=store.id,
                category_id=category_map[category_name].id,
                name=name,
                slug=slugify(name),
                description=f"Produto demonstrativo: {name}",
                sku=sku,
                price=Decimal(price),
                is_active=True,
                track_inventory=True,
                created_at=now,
                updated_at=now,
            )
            db.add(product)
            db.flush()
        inventory = db.query(Inventory).filter(
            Inventory.store_id == store.id,
            Inventory.product_id == product.id,
            Inventory.variant_id.is_(None),
        ).first()
        if not inventory:
            db.add(Inventory(
                store_id=store.id,
                product_id=product.id,
                variant_id=None,
                quantity=stock,
                reserved_quantity=0,
                min_quantity=5,
                updated_at=now,
            ))
    return store


def seed_tech_store(db, mmap, now):
    business_category = db.query(BusinessCategory).filter_by(slug="loja-eletronicos-informatica").one()
    store = db.query(Store).filter_by(slug="loja-tech-demo").first()
    if not store:
        store = Store(
            name="Loja Tech Demo",
            slug="loja-tech-demo",
            business_category_id=business_category.id,
            business_model_id=mmap["VAREJO"].id,
            capabilities={**mmap["VAREJO"].default_capabilities, "coupons": True, "promotions": True},
            description="Segunda loja usada para validar isolamento multi-tenant.",
            primary_color="#2563EB",
            secondary_color="#0F172A",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(store)
        db.flush()

    ensure_user(
        db,
        store=store,
        name="Administrador Loja Tech",
        email="admin@lojatechdemo.com",
        password="Admin@67890",
        now=now,
    )
    category = db.query(Category).filter_by(store_id=store.id, slug="acessorios").first()
    if not category:
        category = Category(
            store_id=store.id,
            name="Acessórios",
            slug="acessorios",
            description="Acessórios de informática.",
            sort_order=1,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(category)
        db.flush()

    product = db.query(Product).filter_by(store_id=store.id, sku="TECH-001").first()
    if not product:
        product = Product(
            store_id=store.id,
            category_id=category.id,
            name="Mouse Gamer Demo",
            slug="mouse-gamer-demo",
            description="Produto exclusivo da Loja Tech Demo.",
            sku="TECH-001",
            price=Decimal("99.90"),
            is_active=True,
            track_inventory=True,
            created_at=now,
            updated_at=now,
        )
        db.add(product)
        db.flush()
    inventory = db.query(Inventory).filter(
        Inventory.store_id == store.id,
        Inventory.product_id == product.id,
        Inventory.variant_id.is_(None),
    ).first()
    if not inventory:
        db.add(Inventory(
            store_id=store.id,
            product_id=product.id,
            variant_id=None,
            quantity=10,
            reserved_quantity=0,
            min_quantity=2,
            updated_at=now,
        ))
    return store


def seed_barbershop(db, mmap, now):
    business_category = db.query(BusinessCategory).filter_by(slug="barbearia").one()
    store = db.query(Store).filter_by(slug="barbearia-central-demo").first()
    if not store:
        store = Store(
            name="Barbearia Central Demo",
            slug="barbearia-central-demo",
            business_category_id=business_category.id,
            business_model_id=mmap["AGENDAMENTO"].id,
            capabilities={**mmap["AGENDAMENTO"].default_capabilities},
            description="Barbearia demonstrativa para validar serviços e agendamentos.",
            primary_color="#7A4B2A",
            secondary_color="#1F2937",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(store)
        db.flush()

    ensure_user(
        db,
        store=store,
        name="Administrador Barbearia Demo",
        email="admin@barbeariacentral.com",
        password="Admin@24680",
        now=now,
    )

    category = db.query(Category).filter_by(store_id=store.id, slug="servicos-barbearia").first()
    if not category:
        category = Category(
            store_id=store.id,
            name="Serviços de Barbearia",
            slug="servicos-barbearia",
            sort_order=1,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(category)
        db.flush()

    service_map = {}
    for name, price, duration in BARBER_SERVICES:
        service = db.query(Service).filter_by(store_id=store.id, slug=slugify(name)).first()
        if not service:
            service = Service(
                store_id=store.id,
                category_id=category.id,
                name=name,
                slug=slugify(name),
                description=f"Serviço demonstrativo: {name}",
                price=Decimal(price),
                duration_minutes=duration,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            db.add(service)
            db.flush()
        service_map[name] = service

    professional_specs = [
        ("João Silva", ["Corte Masculino", "Barba", "Corte + Barba", "Sobrancelha"]),
        ("Carlos Mendes", ["Corte Masculino", "Barba", "Corte + Barba"]),
    ]
    professionals = {}
    for name, service_names in professional_specs:
        professional = db.query(Professional).filter_by(store_id=store.id, name=name).first()
        if not professional:
            professional = Professional(
                store_id=store.id,
                name=name,
                description="Profissional demonstrativo",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            db.add(professional)
            db.flush()
        professionals[name] = professional

        for service_name in service_names:
            service = service_map[service_name]
            link = db.query(ProfessionalService).filter_by(
                professional_id=professional.id,
                service_id=service.id,
            ).first()
            if not link:
                db.add(ProfessionalService(
                    store_id=store.id,
                    professional_id=professional.id,
                    service_id=service.id,
                ))

        for day in range(6):  # segunda(0) a sábado(5)
            row = db.query(ProfessionalHours).filter_by(
                professional_id=professional.id,
                day_of_week=day,
            ).first()
            if not row:
                db.add(ProfessionalHours(
                    store_id=store.id,
                    professional_id=professional.id,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(18, 0),
                    is_active=True,
                ))
    return store


def seed_electrician(db, mmap, now):
    business_category = db.query(BusinessCategory).filter_by(slug="eletricista").one()
    store = db.query(Store).filter_by(slug="eletrica-sol-demo").first()
    if not store:
        store = Store(
            name="Elétrica Sol Demo",
            slug="eletrica-sol-demo",
            business_category_id=business_category.id,
            business_model_id=mmap["ORCAMENTO"].id,
            capabilities={**mmap["ORCAMENTO"].default_capabilities},
            description="Empresa demonstrativa para solicitações de orçamento elétrico.",
            primary_color="#D97706",
            secondary_color="#1F2937",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(store)
        db.flush()

    ensure_user(
        db,
        store=store,
        name="Administrador Elétrica Sol",
        email="admin@eletricasoldemo.com",
        password="Admin@13579",
        now=now,
    )

    category = db.query(Category).filter_by(store_id=store.id, slug="servicos-eletricos").first()
    if not category:
        category = Category(
            store_id=store.id,
            name="Serviços Elétricos",
            slug="servicos-eletricos",
            description="Tipos de serviço que podem receber solicitação de orçamento.",
            sort_order=1,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(category)
        db.flush()

    for name, price, duration in ELECTRICIAN_SERVICES:
        service = db.query(Service).filter_by(store_id=store.id, slug=slugify(name)).first()
        if not service:
            service = Service(
                store_id=store.id,
                category_id=category.id,
                name=name,
                slug=slugify(name),
                description=f"Serviço sob orçamento: {name}",
                price=Decimal(price),
                duration_minutes=duration,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            db.add(service)
    return store




def seed_hotel(db, mmap, now):
    business_category = db.query(BusinessCategory).filter_by(slug="hotel-pousada").one()
    store = db.query(Store).filter_by(slug="pousada-serena-demo").first()
    if not store:
        store = Store(
            name="Pousada Serena Demo", slug="pousada-serena-demo",
            business_category_id=business_category.id, business_model_id=mmap["RESERVA"].id,
            capabilities={**mmap["RESERVA"].default_capabilities},
            description="Pousada demonstrativa com reservas de quartos e suítes.",
            primary_color="#0F766E", secondary_color="#164E63", is_active=True, created_at=now, updated_at=now,
        )
        db.add(store); db.flush()
    ensure_user(db, store=store, name="Administrador Pousada Serena", email="admin@pousadaserena.com", password="Admin@11223", now=now)
    for name, kind, capacity, price in HOTEL_RESOURCES:
        row = db.query(Resource).filter_by(store_id=store.id, slug=slugify(name)).first()
        if not row:
            db.add(Resource(store_id=store.id, name=name, slug=slugify(name), description=f"Hospedagem demonstrativa: {name}", resource_type=kind, capacity=capacity, price_per_day=Decimal(price), is_active=True, created_at=now, updated_at=now))
    return store


def seed_rental_store(db, mmap, now):
    business_category = db.query(BusinessCategory).filter_by(slug="aluguel-equipamentos-produtos").one()
    store = db.query(Store).filter_by(slug="aluga-facil-demo").first()
    if not store:
        store = Store(
            name="Aluga Fácil Demo", slug="aluga-facil-demo",
            business_category_id=business_category.id, business_model_id=mmap["LOCACAO"].id,
            capabilities={**mmap["LOCACAO"].default_capabilities},
            description="Locação demonstrativa de ferramentas e equipamentos.",
            primary_color="#EA580C", secondary_color="#7C2D12", is_active=True, created_at=now, updated_at=now,
        )
        db.add(store); db.flush()
    ensure_user(db, store=store, name="Administrador Aluga Fácil", email="admin@alugafacildemo.com", password="Admin@44556", now=now)
    for name, sku, rate, deposit, qty in RENTAL_ITEMS:
        row = db.query(RentalItem).filter_by(store_id=store.id, sku=sku).first()
        if not row:
            db.add(RentalItem(store_id=store.id, name=name, slug=slugify(name), description=f"Item demonstrativo para locação: {name}", sku=sku, daily_rate=Decimal(rate), deposit_amount=Decimal(deposit), quantity_total=qty, is_active=True, created_at=now, updated_at=now))
    return store


def seed_marketing(db, market_store, now):
    coupon = db.query(Coupon).filter_by(store_id=market_store.id, code="BEMVINDO10").first()
    if not coupon:
        coupon = Coupon(
            store_id=market_store.id, code="BEMVINDO10", description="10% de desconto no primeiro teste",
            discount_type="PERCENT", value=Decimal("10.00"), min_order_value=Decimal("20.00"),
            max_discount=Decimal("25.00"), usage_limit=1000, usage_count=0, is_active=True,
            created_at=now, updated_at=now,
        )
        db.add(coupon)

    promo = db.query(Promotion).filter_by(store_id=market_store.id, name="Oferta Café").first()
    cafe = db.query(Product).filter_by(store_id=market_store.id, sku="MER-004").first()
    if cafe and not promo:
        promo = Promotion(
            store_id=market_store.id, name="Oferta Café", description="15% de desconto automático no Café 500g",
            discount_type="PERCENT", value=Decimal("15.00"), is_active=True, created_at=now, updated_at=now,
        )
        db.add(promo); db.flush()
        db.add(PromotionItem(store_id=market_store.id, promotion_id=promo.id, product_id=cafe.id, created_at=now))

def seed_payment_settings(db, now):
    eligible = {"VAREJO", "ALIMENTACAO", "AGENDAMENTO", "RESERVA", "LOCACAO", "SERVICOS", "HIBRIDO"}
    for store in db.query(Store).all():
        model_code = store.business_model.code if store.business_model else None
        if model_code in eligible:
            caps = dict(store.capabilities or {})
            caps["payments"] = True
            store.capabilities = caps

        settings = db.query(PaymentSettings).filter_by(store_id=store.id).first()
        if not settings:
            is_market_demo = store.slug == "mercado-bom-preco"
            settings = PaymentSettings(
                store_id=store.id,
                pix_enabled=is_market_demo,
                pix_key_type="EMAIL" if is_market_demo else None,
                pix_key="pix-demo@catalogodigital.local" if is_market_demo else None,
                pix_receiver_name="Mercado Bom Preço — DEMO" if is_market_demo else None,
                pix_receiver_city="São Paulo" if is_market_demo else None,
                cash_enabled=True,
                card_on_delivery_enabled=True,
                whatsapp_enabled=True,
                online_gateway="NONE",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            db.add(settings)



PLANS = [
    {
        "name": "Gratuito", "code": "GRATUITO",
        "description": "Plano interno de contingência da plataforma.",
        "monthly_price": Decimal("0.00"), "yearly_price": None,
        "limits": {"products": 20, "services": 10, "professionals": 1},
        "features": {"coupons": False, "promotions": False, "custom_branding": False, "reports": False, "priority_support": False, "custom_domain": False, "online_payments": False},
        "sort_order": 0, "trial_days": 0, "grace_days": 0, "is_public": False, "is_featured": False, "badge": None,
    },
    {
        "name": "Essencial", "code": "ESSENCIAL",
        "description": "Para pequenos negócios que querem vender e atender com uma presença digital profissional.",
        "monthly_price": Decimal("49.90"), "yearly_price": None,
        "limits": {"products": 150, "services": 40, "professionals": 4},
        "features": {"coupons": True, "promotions": False, "custom_branding": True, "reports": False, "priority_support": False, "custom_domain": False, "online_payments": False},
        "sort_order": 1, "trial_days": 7, "grace_days": 5, "is_public": True, "is_featured": False, "badge": "Comece profissional",
    },
    {
        "name": "Profissional", "code": "PROFISSIONAL",
        "description": "Para empresas em crescimento que precisam de marketing, relatórios e maior capacidade operacional.",
        "monthly_price": Decimal("89.90"), "yearly_price": None,
        "limits": {"products": 600, "services": 150, "professionals": 20},
        "features": {"coupons": True, "promotions": True, "custom_branding": True, "reports": True, "priority_support": False, "custom_domain": False, "online_payments": True},
        "sort_order": 2, "trial_days": 7, "grace_days": 5, "is_public": True, "is_featured": True, "badge": "Mais escolhido",
    },
    {
        "name": "Premium", "code": "PREMIUM",
        "description": "Para operações maiores que querem todos os recursos, limites amplos e atendimento prioritário.",
        "monthly_price": Decimal("149.90"), "yearly_price": None,
        "limits": {"products": -1, "services": -1, "professionals": -1},
        "features": {"coupons": True, "promotions": True, "custom_branding": True, "reports": True, "priority_support": True, "custom_domain": True, "online_payments": True},
        "sort_order": 3, "trial_days": 7, "grace_days": 7, "is_public": True, "is_featured": False, "badge": "Tudo liberado",
    },
]



def seed_plans_and_subscriptions(db, now):
    plan_map = {}
    for spec in PLANS:
        plan = db.query(Plan).filter_by(code=spec["code"]).first()
        if not plan:
            plan = Plan(
                name=spec["name"], code=spec["code"], description=spec["description"],
                monthly_price=spec["monthly_price"], yearly_price=spec["yearly_price"],
                limits=spec["limits"], features=spec["features"], is_active=True,
                sort_order=spec["sort_order"], trial_days=spec["trial_days"], grace_days=spec["grace_days"],
                is_public=spec["is_public"], is_featured=spec["is_featured"], badge=spec["badge"],
                created_at=now, updated_at=now,
            )
            db.add(plan); db.flush()
        # Planos existentes são deliberadamente preservados: o Super Admin é a fonte de verdade comercial.
        plan_map[spec["code"]] = plan

    professional = plan_map["PROFISSIONAL"]
    for store in db.query(Store).all():
        has_any = db.query(Subscription.id).filter(Subscription.store_id == store.id).first()
        if not has_any:
            subscription = Subscription(
                store_id=store.id, plan_id=professional.id, status="ACTIVE", billing_cycle="MONTHLY",
                starts_at=now, current_period_start=now, provider="MANUAL", created_at=now, updated_at=now,
            )
            snapshot_subscription_terms(subscription, professional, now=now)
            db.add(subscription)
    return plan_map

def main():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        ensure_super_admin(db, now)
        for i, (name, code, desc, action, caps) in enumerate(MODELS, 1):
            model = db.query(BusinessModel).filter_by(code=code).first()
            if not model:
                model = BusinessModel(
                    name=name,
                    code=code,
                    description=desc,
                    primary_action=action,
                    default_capabilities=caps,
                    sort_order=i,
                    active=True,
                    created_at=now,
                    updated_at=now,
                )
                db.add(model)
            else:
                model.default_capabilities = caps
                model.updated_at = now
        db.commit()

        mmap = {m.code: m for m in db.query(BusinessModel).all()}
        for i, (name, slug, code) in enumerate(CATS, 1):
            category = db.query(BusinessCategory).filter_by(slug=slug).first()
            category_capabilities = {
                **(mmap[code].default_capabilities or {}),
                **CATEGORY_CAPABILITY_OVERRIDES.get(slug, {}),
            }
            if not category:
                category = BusinessCategory(
                    name=name,
                    slug=slug,
                    business_model_id=mmap[code].id,
                    default_capabilities=category_capabilities,
                    sort_order=i,
                    active=True,
                    created_at=now,
                    updated_at=now,
                )
                db.add(category)
            else:
                category.name = name
                category.business_model_id = mmap[code].id
                category.default_capabilities = category_capabilities
                category.sort_order = i
                category.updated_at = now
        db.commit()

        market_store = seed_market(db, mmap, now)
        seed_marketing(db, market_store, now)
        seed_tech_store(db, mmap, now)
        seed_barbershop(db, mmap, now)
        seed_electrician(db, mmap, now)
        seed_hotel(db, mmap, now)
        seed_rental_store(db, mmap, now)
        seed_payment_settings(db, now)
        seed_plans_and_subscriptions(db, now)
        db.commit()

        print("Seed da Fase 13 concluído.")
        print(f"Super Admin: {SUPER_ADMIN_EMAIL} / {SUPER_ADMIN_PASSWORD}")
        print("Mercado: admin@mercadobompreco.com / Admin@12345")
        print("Loja Tech: admin@lojatechdemo.com / Admin@67890")
        print("Barbearia: admin@barbeariacentral.com / Admin@24680")
        print("Elétrica Sol: admin@eletricasoldemo.com / Admin@13579")
        print("Barbearia Central Demo: 4 serviços, 2 profissionais, horários de segunda a sábado, 09:00-18:00")
        print("Elétrica Sol Demo: 5 tipos de serviço e capability de orçamentos habilitada")
        print("Marketing demo: cupom BEMVINDO10 e promoção automática no Café 500g")
        print("Pousada Serena: admin@pousadaserena.com / Admin@11223")
        print("Aluga Fácil: admin@alugafacildemo.com / Admin@44556")
        print("Pagamentos: PIX manual, dinheiro, cartão no atendimento/entrega e WhatsApp")
        print("PIX demo do Mercado usa chave fictícia; configure sua chave real no painel antes de uso comercial")
        print("Planos: Essencial, Profissional e Premium (Gratuito interno de contingência)")
        print("Lojas existentes recebem o plano Profissional apenas se ainda não possuírem assinatura")
    finally:
        db.close()


if __name__ == "__main__":
    main()
