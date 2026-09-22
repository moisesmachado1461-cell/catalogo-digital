const params = new URLSearchParams(location.search);
const slug = params.get('slug') || 'mercado-bom-preco';
let store = null, catalog = null, serviceData = null, promotions = [], publicCoupons = [], resourcesData = null, rentalItemsData = null, paymentOptions = [];
let selectedCouponCode = null;
let validatedCoupon = null;
let storePaymentPollTimer = null;
let cart = JSON.parse(localStorage.getItem(`cart_${slug}`) || '[]');
const { query: $, queryAll: $$, initials } = window.CatalogoUtils;

function firstStoreSection() {
  const caps = store?.capabilities || {};
  if (caps.catalog) return { id: 'catalogSection', label: 'Ver produtos' };
  if (caps.services) return { id: 'servicesSection', label: caps.appointments ? 'Agendar horário' : 'Ver serviços' };
  if (caps.reservations) return { id: 'reservationsSection', label: 'Fazer reserva' };
  if (caps.rentals) return { id: 'rentalsSection', label: 'Ver locações' };
  return { id: 'contactSection', label: 'Falar com a empresa' };
}

function renderPremiumShell() {
  const category = store.business_category?.name || store.business_model?.name || 'Negócio';
  const logoHtml = store.logo_url
    ? `<img alt="Logo de ${escapeHtml(store.name)}" src="${escapeHtml(assetUrl(store.logo_url))}">`
    : escapeHtml(initials(store.name));
  $('#headerStoreMark').innerHTML = logoHtml;
  $('#footerStoreMark').innerHTML = logoHtml;
  $('#headerStoreName').textContent = store.name;
  $('#headerStoreCategory').textContent = category;
  $('#footerStoreName').textContent = store.name;
  const customerAccountLink = $('#customerAccountLink');
  if (customerAccountLink) {
    customerAccountLink.href = `cliente.html?slug=${encodeURIComponent(slug)}`;
    const accountLabel = $('#customerAccountLabel');
    const hasCustomerSession = Boolean(sessionStorage.getItem(`catalogo_customer_token_${slug}`));
    if (accountLabel) accountLabel.textContent = hasCustomerSession ? 'Minha conta' : 'Entrar';
    customerAccountLink.title = hasCustomerSession ? 'Abrir minha conta' : 'Entrar ou criar conta';
  }

  const primary = firstStoreSection();
  const primaryButton = $('#headerPrimaryAction');
  primaryButton.textContent = primary.label;
  primaryButton.classList.remove('hidden');
  primaryButton.onclick = () => openStoreSection(primary.id);
  const contactButton = $('#headerContactAction');
  contactButton.classList.remove('hidden');
  contactButton.onclick = () => openStoreSection('contactSection');

  // A vitrine pública prioriza conteúdo útil da loja; textos promocionais genéricos foram removidos.

}

function setTheme() {
  const primary = store.primary_color || '#7C3AED';
  const secondary = store.secondary_color || '#4F46E5';
  document.documentElement.style.setProperty('--brand', primary);
  document.documentElement.style.setProperty('--brand2', secondary);
  $('meta[name="theme-color"]')?.setAttribute('content', primary);
  document.title = `${store.name} — Catálogo Digital`;
  $('#storeMetaDescription').setAttribute('content', store.description || `Conheça ${store.name} no Catálogo Digital.`);
  $('#storeName').textContent = store.name;
  $('#contactStoreName').textContent = store.name;
  $('#storeDescription').textContent = store.description || 'Bem-vindo ao nosso catálogo digital.';
  $('#storeType').textContent = store.business_category?.name || store.business_model?.name || 'Negócio';
  renderPremiumShell();

  const logo = $('#storeLogo');
  if (store.logo_url) logo.innerHTML = `<img alt="Logo de ${escapeHtml(store.name)}" src="${escapeHtml(assetUrl(store.logo_url))}">`;
  else logo.textContent = initials(store.name);

  const hero = $('#storeHero');
  if (store.banner_url) {
    hero.classList.add('has-banner');
    hero.style.backgroundImage = `url("${String(assetUrl(store.banner_url)).replace(/"/g, '')}")`;
  } else {
    hero.style.backgroundImage = `linear-gradient(125deg, ${primary}, ${secondary})`;
  }

  const facts = [];
  if (store.city || store.state) facts.push([store.city, store.state].filter(Boolean).join(' · '));
  if (store.phone) facts.push(store.phone);
  if (store.business_model?.name) facts.push(store.business_model.name);
  $('#storeHeroFacts').innerHTML = facts.map(item => `<span>${escapeHtml(item)}</span>`).join('');

  const caps = store.capabilities || {};
  const actions = [];
  if (caps.catalog) actions.push(`<button class="btn store-cta" onclick="openStoreSection('catalogSection')">Explorar produtos</button>`);
  if (caps.services) actions.push(`<button class="btn store-cta" onclick="openStoreSection('servicesSection')">${caps.appointments ? 'Agendar atendimento' : 'Explorar serviços'}</button>`);
  if (caps.reservations) actions.push(`<button class="btn store-cta" onclick="openStoreSection('reservationsSection')">Reservar</button>`);
  if (caps.rentals) actions.push(`<button class="btn store-cta" onclick="openStoreSection('rentalsSection')">Ver locações</button>`);
  if (store.whatsapp) {
    const number = store.whatsapp.replace(/\D/g, '');
    actions.push(`<a class="btn store-cta secondary" target="_blank" rel="noopener" href="https://wa.me/${number}">WhatsApp</a>`);
  }
  $('#storeHeroActions').innerHTML = actions.join('');
}

function addTab(id, label) {
  const btn = document.createElement('button');
  btn.className = 'tab-btn';
  btn.textContent = label;
  btn.dataset.target = id;
  btn.onclick = () => showSection(id, btn);
  $('#storeTabs').appendChild(btn);
  return btn;
}

function showSection(id, btn) {
  $$('.store-section').forEach(x => x.classList.add('hidden'));
  $$('.tab-btn').forEach(x => x.classList.remove('active'));
  const section = $(`#${id}`);
  if (!section) return;
  section.classList.remove('hidden');
  btn?.classList.add('active');
}

window.openStoreSection = function openStoreSection(id) {
  const btn = $(`[data-target="${id}"]`);
  showSection(id, btn);
  $('.store-nav')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
};



function publicCouponDiscountLabel(coupon) {
  return coupon.discount_type === 'PERCENT' ? `${Number(coupon.value)}% OFF` : `${money(coupon.value)} OFF`;
}

function publicCouponRules(coupon) {
  const rules = [];
  if (Number(coupon.min_order_value || 0) > 0) rules.push(`Pedido mínimo ${money(coupon.min_order_value)}`);
  if ((coupon.product_ids || []).length) rules.push('Válido em produtos selecionados');
  if (coupon.max_discount != null) rules.push(`Desconto máximo ${money(coupon.max_discount)}`);
  if (coupon.ends_at) rules.push(`Válido até ${new Date(coupon.ends_at).toLocaleDateString('pt-BR')}`);
  if (coupon.usage_remaining != null) rules.push(`${coupon.usage_remaining} uso(s) restante(s)`);
  return rules.length ? rules.join(' · ') : 'Sem pedido mínimo informado';
}

function checkoutTotalsPayload() {
  const subtotal = cart.reduce((sum, item) => sum + Number(item.price) * Number(item.quantity), 0);
  const grouped = new Map();
  cart.forEach(item => grouped.set(Number(item.product_id), (grouped.get(Number(item.product_id)) || 0) + Number(item.price) * Number(item.quantity)));
  return { subtotal, items: [...grouped].map(([product_id, line_total]) => ({ product_id, line_total })) };
}

function renderCheckoutSummary(preview = null, message = '') {
  const { subtotal } = checkoutTotalsPayload();
  const discount = Number(preview?.discount_amount || 0);
  const total = Number(preview?.total ?? subtotal);
  const summary = $('#checkoutSummary');
  if (summary) summary.innerHTML = `<div><b>Subtotal</b><span>${money(subtotal)}</span></div>${discount > 0 ? `<div class="checkout-discount"><b>Desconto aplicado</b><span>− ${money(discount)}</span></div>` : ''}<div class="checkout-preview-total"><b>Total</b><strong>${money(total)}</strong></div><small>${escapeHtml(message || 'Digite o cupom e clique em Aplicar cupom.')}</small>`;
}

async function validateCheckoutCoupon(showSuccess = true) {
  const field = $('#checkoutCouponCode');
  const code = (field?.value || '').trim().toUpperCase().replaceAll(' ', '');
  const hint = $('#checkoutCouponHint');
  if (!code) {
    validatedCoupon = null;
    selectedCouponCode = null;
    if (hint) hint.classList.add('hidden');
    renderCheckoutSummary();
    return null;
  }
  const button = $('#applyCheckoutCouponBtn');
  if (button) { button.disabled = true; button.textContent = 'Validando...'; }
  try {
    const totals = checkoutTotalsPayload();
    const preview = await api(`/api/public/stores/${encodeURIComponent(slug)}/coupons/validate`, { method: 'POST', body: JSON.stringify({ code, ...totals }) });
    validatedCoupon = preview;
    selectedCouponCode = preview.code;
    if (field) field.value = preview.code;
    const message = `Cupom ${preview.code} aplicado: você economiza ${money(preview.discount_amount)}.`;
    if (hint) { hint.textContent = message; hint.classList.remove('hidden', 'error'); hint.classList.add('success'); }
    renderCheckoutSummary(preview, message);
    if (showSuccess) showToast('Cupom aplicado com sucesso.');
    return preview;
  } catch (error) {
    validatedCoupon = null;
    selectedCouponCode = null;
    if (hint) { hint.textContent = error.message; hint.classList.remove('hidden', 'success'); hint.classList.add('error'); }
    renderCheckoutSummary(null, error.message);
    throw error;
  } finally {
    if (button) { button.disabled = false; button.textContent = 'Aplicar cupom'; }
  }
}

async function loadPublicCoupons() {
  try {
    publicCoupons = await api(`/api/public/stores/${encodeURIComponent(slug)}/coupons`);
  } catch (_error) {
    publicCoupons = [];
  }
  renderPublicCoupons();
  return publicCoupons;
}

function renderPublicCoupons() {
  const root = $('#publicCouponGrid');
  if (!root) return;
  const count = $('#couponResultsCount');
  if (count) count.textContent = `${publicCoupons.length} ${publicCoupons.length === 1 ? 'cupom' : 'cupons'}`;
  root.innerHTML = publicCoupons.length ? publicCoupons.map(coupon => `
    <article class="public-coupon-card">
      <div class="public-coupon-card-top"><span class="public-coupon-badge">${escapeHtml(publicCouponDiscountLabel(coupon))}</span><span class="public-coupon-code">${escapeHtml(coupon.code)}</span></div>
      <h3>${escapeHtml(coupon.description || 'Cupom especial da loja')}</h3>
      <p>${escapeHtml(publicCouponRules(coupon))}</p>
      <div class="public-coupon-actions"><button class="btn primary small" type="button" onclick="usePublicCoupon('${String(coupon.code).replace(/'/g, "\\'")}')">Usar cupom</button><button class="btn ghost small" type="button" onclick="copyPublicCoupon('${String(coupon.code).replace(/'/g, "\\'")}')">Copiar código</button></div>
    </article>`).join('') : '<div class="empty empty-wide">Nenhum cupom público disponível no momento.</div>';
}

window.copyPublicCoupon = async function copyPublicCoupon(code) {
  try { await navigator.clipboard.writeText(code); } catch (_error) {}
  showToast(`Cupom ${code} copiado.`);
};

window.usePublicCoupon = async function usePublicCoupon(code) {
  selectedCouponCode = code;
  const input = $('#checkoutCouponCode');
  if (input) input.value = code;
  const hint = $('#checkoutCouponHint');
  validatedCoupon = null;
  if (hint) { hint.textContent = `Cupom ${code} selecionado. Clique em Aplicar cupom no checkout.`; hint.classList.remove('hidden'); }
  try { await navigator.clipboard.writeText(code); } catch (_error) {}
  if (cart.length) showToast(`Cupom ${code} selecionado. Finalize o pedido para aplicar.`);
  else showToast(`Cupom ${code} copiado. Adicione produtos ao carrinho para usar.`);
};

async function loadPaymentOptions() {
  if (!store?.capabilities?.payments) {
    paymentOptions = [];
    renderPaymentSelects();
    return;
  }
  try {
    const data = await api(`/api/public/stores/${encodeURIComponent(slug)}/payment-options`);
    paymentOptions = data.options || [];
  } catch (_error) {
    paymentOptions = [];
  }
  renderPaymentSelects();
}

function updatePaymentDocumentField(select) {
  const form = select.closest('form');
  const field = form?.querySelector('.online-pix-document-field');
  const input = field?.querySelector('[name="payment_document"]');
  const online = select.value === 'PIX_ONLINE';
  field?.classList.toggle('hidden', !online);
  if (input) {
    input.required = online;
    if (!online) input.value = '';
  }
  const email = form?.querySelector('[name="email"]');
  if (email) email.required = online;
}

function renderPaymentSelects() {
  $$('.payment-method-select').forEach((select) => {
    const current = select.value;
    if (!paymentOptions.length) {
      select.innerHTML = '<option value="">Pagamento a combinar</option>';
      select.required = false;
      updatePaymentDocumentField(select);
      return;
    }
    select.required = true;
    select.innerHTML = '<option value="">Selecione</option>' + paymentOptions.map(item => `<option value="${escapeHtml(item.code)}">${escapeHtml(item.label)}</option>`).join('');
    if (current && paymentOptions.some(item => item.code === current)) select.value = current;
    select.onchange = () => updatePaymentDocumentField(select);
    updatePaymentDocumentField(select);
  });
}

function paymentResultHtml(payment) {
  if (!payment) return '';
  const status = escapeHtml(payment.status || 'PENDENTE');
  const method = escapeHtml(payment.method_label || payment.method || 'Pagamento');
  const base = `<div class="payment-card"><div class="payment-card-head"><div><small>Forma de pagamento</small><strong>${method}</strong></div><span class="status ${status}">${status}</span></div><div class="payment-amount">${money(payment.amount)}</div><p>${escapeHtml(payment.instructions || '')}</p>`;
  if (payment.method === 'PIX_ONLINE') {
    const qrImage = payment.pix_qr_code_base64 ? (String(payment.pix_qr_code_base64).startsWith('data:') ? payment.pix_qr_code_base64 : `data:image/png;base64,${payment.pix_qr_code_base64}`) : '';
    const qr = payment.pix_qr_code || '';
    if (payment.status === 'PAGO') return `${base}<div class="online-pix-paid"><strong>✓ Pagamento confirmado</strong><small>A loja já recebeu a confirmação automática.</small></div></div>`;
    return `${base}<div class="online-pix-box">${qrImage ? `<img class="online-pix-qr" src="${escapeHtml(qrImage)}" alt="QR Code Pix">` : ''}<div class="online-pix-copy"><small>Pix Copia e Cola</small><code>${escapeHtml(qr)}</code><button class="btn primary small" type="button" onclick="copyOnlinePix('${String(qr).replace(/'/g, "\\'")}')">Copiar Pix</button></div><small class="online-pix-wait">Aguardando pagamento. Esta tela atualiza automaticamente.</small></div></div>`;
  }
  if (payment.method === 'PIX') {
    const informed = payment.status === 'INFORMADO';
    const paid = payment.status === 'PAGO';
    const pixCode = payment.pix_qr_code || '';
    return `${base}<div class="pix-box"><small>Chave PIX ${payment.pix_key_type ? `· ${escapeHtml(payment.pix_key_type)}` : ''}</small><div class="pix-key-row"><code>${escapeHtml(payment.pix_key || '')}</code><button class="btn ghost small" type="button" onclick="copyPixKey('${String(payment.pix_key || '').replace(/'/g, "\\'")}')">Copiar chave</button></div>${pixCode ? `<div class="online-pix-copy"><small>Pix Copia e Cola com o valor final</small><code>${escapeHtml(pixCode)}</code><button class="btn primary small" type="button" onclick="copyOnlinePix('${String(pixCode).replace(/'/g, "\\'")}')">Copiar Pix</button></div>` : ''}${payment.pix_receiver_name ? `<small>Recebedor: ${escapeHtml(payment.pix_receiver_name)}${payment.pix_receiver_city ? ` · ${escapeHtml(payment.pix_receiver_city)}` : ''}</small>` : ''}${paid ? '<div class="online-pix-paid"><strong>✓ Pagamento confirmado</strong></div>' : informed ? '<div class="payment-informed"><strong>Pagamento informado</strong><small>A loja verificará o recebimento antes de confirmar.</small></div>' : `<button class="btn primary full-btn" type="button" onclick="informPaymentPaid('${escapeHtml(payment.public_token || '')}', this)">Já paguei</button>`}</div></div>`;
  }
  return `${base}</div>`;
}

window.copyOnlinePix = async function copyOnlinePix(value) {
  try {
    await navigator.clipboard.writeText(value);
    showToast('Código Pix copiado.');
  } catch (_error) {
    showToast('Não foi possível copiar automaticamente.', 'error');
  }
};

function watchOnlinePayment(payment, targetSelector) {
  if (!payment || payment.method !== 'PIX_ONLINE' || payment.status !== 'PENDENTE' || !payment.public_token) return;
  if (storePaymentPollTimer) clearInterval(storePaymentPollTimer);
  let attempts = 0;
  storePaymentPollTimer = setInterval(async () => {
    attempts += 1;
    try {
      const fresh = await api(`/api/public/stores/${encodeURIComponent(slug)}/payments/${encodeURIComponent(payment.public_token)}`);
      const target = $(targetSelector);
      if (target) target.innerHTML = paymentResultHtml(fresh);
      if (fresh.status !== 'PENDENTE' || attempts >= 60) {
        clearInterval(storePaymentPollTimer);
        storePaymentPollTimer = null;
        if (fresh.status === 'PAGO') showToast('Pagamento Pix confirmado!');
      }
    } catch (_error) {
      if (attempts >= 60) { clearInterval(storePaymentPollTimer); storePaymentPollTimer = null; }
    }
  }, 5000);
}

window.copyPixKey = async function copyPixKey(value) {
  try {
    await navigator.clipboard.writeText(value);
    showToast('Chave PIX copiada.');
  } catch (_error) {
    showToast('Não foi possível copiar automaticamente. Selecione a chave manualmente.', 'error');
  }
};

window.informPaymentPaid = async function informPaymentPaid(token, button) {
  if (!token || !confirm('Você já concluiu o pagamento? A loja ainda verificará o recebimento.')) return;
  button.disabled = true;
  button.textContent = 'Informando...';
  try {
    const payment = await api(`/api/public/stores/${encodeURIComponent(slug)}/payments/${encodeURIComponent(token)}/inform-paid`, { method: 'POST' });
    const card = button.closest('.payment-card');
    if (card) card.outerHTML = paymentResultHtml(payment);
    showToast('Pagamento informado. Aguarde a confirmação da loja.');
  } catch (error) {
    button.disabled = false;
    button.textContent = 'Já paguei';
    showToast(error.message, 'error');
  }
};

function showPaymentModal(payment, title = 'Instruções de pagamento') {
  if (!payment) return;
  $('#paymentModalTitle').textContent = title;
  $('#paymentModalContent').innerHTML = paymentResultHtml(payment);
  openModal('paymentModal');
  watchOnlinePayment(payment, '#paymentModalContent');
}

async function init() {
  try {
    store = await api(`/api/public/stores/${encodeURIComponent(slug)}`);
    setTheme();
    await loadPaymentOptions();
    const caps = store.capabilities || {};
    const cartButton = $('#storeCartButton');
    if (cartButton) cartButton.classList.toggle('hidden', !caps.catalog);
    if (caps.coupons) await loadPublicCoupons();
    let first = null;
    if (caps.catalog) { const b = addTab('catalogSection', 'Produtos'); first ||= b; await loadCatalog(); }
    if (publicCoupons.length) addTab('couponsSection', 'Cupons');
    if (caps.services) { const b = addTab('servicesSection', 'Serviços'); first ||= b; await loadServices(); }
    if (caps.reservations) { const b = addTab('reservationsSection', 'Reservas'); first ||= b; await loadResources(); }
    if (caps.rentals) { const b = addTab('rentalsSection', 'Locações'); first ||= b; await loadRentalItems(); }
    const contact = addTab('contactSection', 'Contato'); first ||= contact;
    renderContact();
    if (first) showSection(first.dataset.target, first);
  } catch (err) {
    $('#errorBox').textContent = err.message;
    $('#errorBox').classList.remove('hidden');
    $('#storeName').textContent = 'Não foi possível carregar a loja';
    $('#storeDescription').textContent = err.message;
  }
}

async function loadCatalog() {
  [catalog, promotions] = await Promise.all([
    api(`/api/public/stores/${encodeURIComponent(slug)}/catalog`),
    api(`/api/public/stores/${encodeURIComponent(slug)}/promotions`).catch(() => []),
  ]);
  $('#categoryFilter').innerHTML = '<option value="">Todas as categorias</option>' + catalog.categories.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
  $('#searchInput').oninput = renderProducts;
  $('#categoryFilter').onchange = () => { renderProducts(); renderCategoryChips(); };
  renderCategoryChips();
  renderProducts();
  renderCart();
}

function renderCategoryChips() {
  const box = $('#categoryChips');
  if (!box || !catalog) return;
  const selected = $('#categoryFilter').value;
  box.innerHTML = [`<button class="category-chip ${selected === '' ? 'active' : ''}" data-category="">Todos</button>`, ...catalog.categories.map(c => `<button class="category-chip ${String(c.id) === selected ? 'active' : ''}" data-category="${c.id}">${escapeHtml(c.name)}</button>`)].join('');
  box.querySelectorAll('[data-category]').forEach(btn => {
    btn.onclick = () => {
      $('#categoryFilter').value = btn.dataset.category;
      renderCategoryChips();
      renderProducts();
    };
  });
}


function activePromotion(productId) {
  return promotions.find((promotion) => (promotion.product_ids || []).includes(productId)) || null;
}

function discountedBasePrice(product, variant = null) {
  const base = Number(variant?.price ?? product.price);
  const promo = activePromotion(product.id);
  if (!promo) return { price: base, original: base, promotion: null };
  let discount = promo.discount_type === 'PERCENT' ? base * (Number(promo.value) / 100) : Number(promo.value);
  discount = Math.max(0, Math.min(base, discount));
  return { price: Math.max(0, base - discount), original: base, promotion: promo };
}

function productUnitPrice(product, variant = null, selectedItemIds = []) {
  const base = discountedBasePrice(product, variant);
  const extras = (product.options || []).flatMap(o => o.items || []).filter(i => selectedItemIds.includes(i.id)).reduce((sum, item) => sum + Number(item.price_adjustment || 0), 0);
  return { ...base, price: base.price + extras, extras };
}

function renderProducts() {
  if (!catalog) return;
  const q = ($('#searchInput').value || '').toLowerCase().trim();
  const cat = $('#categoryFilter').value;
  const rows = catalog.products.filter(p => (!cat || String(p.category_id) === cat) && (!q || `${p.name} ${p.description || ''}`.toLowerCase().includes(q)));
  const countLabel = $('#catalogResultsCount');
  if (countLabel) countLabel.textContent = `${rows.length} ${rows.length === 1 ? 'produto' : 'produtos'}`;
  $('#productGrid').innerHTML = rows.length ? rows.map(p => {
    const inventory = p.inventory?.quantity;
    const unavailable = p.track_inventory && p.inventory && Number(inventory) <= 0 && !(p.variants || []).length;
    const offer = discountedBasePrice(p);
    const productCoupon = publicCoupons.find(coupon => (coupon.product_ids || []).includes(p.id));
    return `<article class="product-card product-card-v2 product-card-clickable" tabindex="0" role="button" aria-label="Ver detalhes de ${escapeHtml(p.name)}" onclick="if (!event.target.closest('button')) openProductDetails(${p.id})" onkeydown="if ((event.key === 'Enter' || event.key === ' ') && !event.target.closest('button')) { event.preventDefault(); openProductDetails(${p.id}); }">
      <div class="product-image product-image-v2">${p.image_url ? `<img src="${escapeHtml(assetUrl(p.image_url))}" alt="${escapeHtml(p.name)}" loading="lazy">` : `<span class="image-placeholder">${initials(p.name)}</span>`}${(p.compare_at_price || offer.promotion) ? `<span class="promo-tag">${offer.promotion ? escapeHtml(offer.promotion.name) : 'Oferta'}</span>` : ''}${productCoupon ? `<button class="product-coupon-tag" type="button" onclick="event.stopPropagation(); usePublicCoupon('${String(productCoupon.code).replace(/'/g, "\\'")}')" title="Usar cupom ${escapeHtml(productCoupon.code)}">Cupom ${escapeHtml(productCoupon.code)}</button>` : ''}<span class="product-view-hint">Ver detalhes</span></div>
      <div class="card-body">
        <div class="product-category">${escapeHtml(catalog.categories.find(c => c.id === p.category_id)?.name || 'Produto')}</div>
        <h3>${escapeHtml(p.name)}</h3>
        <p>${escapeHtml(p.description || 'Produto disponível neste catálogo.')}</p>
        <div class="product-footer">
          <div><div class="price-line">${offer.promotion ? `<small class="old-price">${money(offer.original)}</small>` : (p.compare_at_price ? `<small class="old-price">${money(p.compare_at_price)}</small>` : '')}<div class="price">${money(offer.price)}</div></div><div class="stock ${unavailable ? 'out' : ''}">${unavailable ? 'Sem estoque' : ((p.variants || []).length ? `${p.variants.length} opção(ões) de variante` : (p.track_inventory && p.inventory ? `${inventory} em estoque` : 'Disponível'))}</div></div>
          <button class="btn primary small" onclick="addToCart(${p.id})" ${unavailable ? 'disabled' : ''}>${unavailable ? 'Indisponível' : (((p.variants || []).length || (p.options || []).length) ? 'Escolher' : 'Adicionar')}</button>
        </div>
      </div>
    </article>`;
  }).join('') : '<div class="empty empty-wide">Nenhum produto encontrado com esses filtros.</div>';
}

window.openProductDetails = function openProductDetails(id) {
  const p = catalog?.products.find(x => x.id === id);
  if (!p) return;
  const category = catalog.categories.find(c => c.id === p.category_id)?.name || 'Produto';
  const inventory = p.inventory?.quantity;
  const unavailable = p.track_inventory && p.inventory && Number(inventory) <= 0 && !(p.variants || []).length;
  const offer = discountedBasePrice(p);
  const variants = (p.variants || []).map(v => `<li><span>${escapeHtml(v.name)}</span><b>${money(v.price ?? p.price)}</b>${v.inventory ? `<small>${Number(v.inventory.quantity) > 0 ? `${v.inventory.quantity} disponível(is)` : 'Sem estoque'}</small>` : ''}</li>`).join('');
  const options = (p.options || []).map(option => `<div class="product-detail-option"><b>${escapeHtml(option.name)}</b><span>${(option.items || []).map(item => `${escapeHtml(item.name)}${Number(item.price_adjustment) ? ` (+ ${money(item.price_adjustment)})` : ''}`).join(' · ')}</span></div>`).join('');
  const image = p.image_url
    ? `<img src="${escapeHtml(assetUrl(p.image_url))}" alt="${escapeHtml(p.name)}">`
    : `<span class="product-details-placeholder">${initials(p.name)}</span>`;
  $('#productDetailsTitle').textContent = p.name;
  $('#productDetailsContent').innerHTML = `
    <div class="product-details-grid">
      <div class="product-details-media">${image}${offer.promotion ? `<span class="promo-tag">${escapeHtml(offer.promotion.name)}</span>` : ''}</div>
      <div class="product-details-info">
        <span class="product-category">${escapeHtml(category)}</span>
        <h3>${escapeHtml(p.name)}</h3>
        <p class="product-details-description">${escapeHtml(p.description || 'A loja ainda não informou uma descrição para este produto.')}</p>
        <div class="product-details-price">${offer.promotion || p.compare_at_price ? `<small>${money(offer.promotion ? offer.original : p.compare_at_price)}</small>` : ''}<strong>${money(offer.price)}</strong></div>
        <div class="product-details-badges"><span class="${unavailable ? 'is-out' : ''}">${unavailable ? 'Sem estoque' : ((p.variants || []).length ? 'Disponível em opções' : (p.track_inventory && p.inventory ? `${inventory} em estoque` : 'Disponível'))}</span>${p.sku ? `<span>Código: ${escapeHtml(p.sku)}</span>` : ''}</div>
        ${variants ? `<div class="product-details-section"><h4>Variações disponíveis</h4><ul class="product-details-variants">${variants}</ul></div>` : ''}
        ${options ? `<div class="product-details-section"><h4>Opções e adicionais</h4>${options}</div>` : ''}
        <button class="btn primary full-btn product-details-action" type="button" onclick="closeModal('productDetailsModal'); addToCart(${p.id})" ${unavailable ? 'disabled' : ''}>${unavailable ? 'Produto indisponível' : (((p.variants || []).length || (p.options || []).length) ? 'Escolher opções' : 'Adicionar ao carrinho')}</button>
      </div>
    </div>`;
  openModal('productDetailsModal');
};

window.addToCart = function addToCart(id) {
  const p = catalog.products.find(x => x.id === id);
  if (!p) return;
  if ((p.variants || []).length || (p.options || []).length) return openProductConfig(id);
  if (p.track_inventory && p.inventory && Number(p.inventory.quantity) <= 0) return showToast('Produto sem estoque.', 'error');
  const pricing = productUnitPrice(p);
  const key = `${id}:base:none`;
  const existing = cart.find(x => x.key === key);
  if (existing) existing.quantity++;
  else cart.push({ key, product_id: id, variant_id: null, selected_option_item_ids: [], selected_options: [], quantity: 1, name: p.name, variant_name: null, price: pricing.price });
  saveCart();
  showToast(`${p.name} adicionado ao carrinho.`);
};

window.openProductConfig = function openProductConfig(id) {
  const p = catalog.products.find(x => x.id === id);
  if (!p) return;
  const form = $('#productConfigForm');
  form.product_id.value = id;
  $('#productConfigTitle').textContent = p.name;
  const variantHtml = (p.variants || []).length ? `<div class="field"><label>Variante</label><select class="select" name="variant_id" required><option value="">Selecione</option>${p.variants.map(v => `<option value="${v.id}">${escapeHtml(v.name)} · ${money(v.price ?? p.price)}${v.inventory ? ` · estoque ${v.inventory.quantity}` : ''}</option>`).join('')}</select></div>` : '';
  const optionHtml = (p.options || []).map(option => `<fieldset class="option-group" data-option-id="${option.id}" data-min="${Math.max(option.required ? 1 : 0, option.min_selections || 0)}" data-max="${option.max_selections || 1}"><legend>${escapeHtml(option.name)} ${option.required ? '<span class="required-mark">obrigatório</span>' : ''}</legend>${(option.items || []).map(item => `<label class="option-choice"><input type="checkbox" name="option_item" value="${item.id}"> <span>${escapeHtml(item.name)}</span><b>${Number(item.price_adjustment) ? `+ ${money(item.price_adjustment)}` : 'sem acréscimo'}</b></label>`).join('')}</fieldset>`).join('');
  $('#productConfigContent').innerHTML = `${variantHtml}${optionHtml || '<div class="notice">Sem adicionais disponíveis.</div>'}`;
  const update = () => {
    const variant = p.variants.find(v => String(v.id) === String(form.variant_id?.value || '')) || null;
    const ids = [...form.querySelectorAll('input[name="option_item"]:checked')].map(x => Number(x.value));
    $('#productConfigPrice').textContent = money(productUnitPrice(p, variant, ids).price);
  };
  form.querySelectorAll('input,select').forEach(el => el.onchange = update);
  update(); openModal('productConfigModal');
};

$('#productConfigForm').onsubmit = (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const p = catalog.products.find(x => x.id === Number(form.product_id.value));
  const variant = p.variants.find(v => String(v.id) === String(form.variant_id?.value || '')) || null;
  if ((p.variants || []).length && !variant) return showToast('Escolha uma variante.', 'error');
  for (const group of form.querySelectorAll('.option-group')) {
    const count = group.querySelectorAll('input:checked').length;
    const min = Number(group.dataset.min || 0), max = Number(group.dataset.max || 1);
    if (count < min) return showToast(`Escolha pelo menos ${min} item(ns) em ${group.querySelector('legend').textContent.trim()}.`, 'error');
    if (count > max) return showToast(`Escolha no máximo ${max} item(ns) neste grupo.`, 'error');
  }
  const selectedIds = [...form.querySelectorAll('input[name="option_item"]:checked')].map(x => Number(x.value));
  const selectedOptions = (p.options || []).flatMap(o => (o.items || []).filter(i => selectedIds.includes(i.id)).map(i => `${o.name}: ${i.name}`));
  const pricing = productUnitPrice(p, variant, selectedIds);
  if (p.track_inventory) {
    const inv = variant ? variant.inventory : p.inventory;
    if (inv && Number(inv.quantity) <= 0) return showToast('Essa opção está sem estoque.', 'error');
  }
  const key = `${p.id}:${variant?.id || 'base'}:${[...selectedIds].sort((a,b)=>a-b).join('-') || 'none'}`;
  const existing = cart.find(x => x.key === key);
  if (existing) existing.quantity++;
  else cart.push({ key, product_id: p.id, variant_id: variant?.id || null, selected_option_item_ids: selectedIds, selected_options: selectedOptions, quantity: 1, name: p.name, variant_name: variant?.name || null, price: pricing.price });
  saveCart(); closeModal('productConfigModal'); showToast(`${p.name} adicionado ao carrinho.`);
};

function saveCart() {
  localStorage.setItem(`cart_${slug}`, JSON.stringify(cart));
  renderCart();
}

function changeQty(i, d) {
  cart[i].quantity += d;
  if (cart[i].quantity <= 0) cart.splice(i, 1);
  saveCart();
}
window.changeQty = changeQty;

function renderCart() {
  const box = $('#cartItems');
  if (!box) return;
  const totalQty = cart.reduce((sum, item) => sum + item.quantity, 0);
  renderPaymentSelects();
  const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  box.innerHTML = cart.length ? cart.map((x, i) => `<div class="cart-item"><div><b>${escapeHtml(x.name)}</b>${x.variant_name ? `<br><small>${escapeHtml(x.variant_name)}</small>` : ''}${(x.selected_options || []).length ? `<br><small>${x.selected_options.map(escapeHtml).join(' · ')}</small>` : ''}<br><small>${money(x.price)} × ${x.quantity}</small></div><div class="cart-actions"><button class="qty" onclick="changeQty(${i},-1)">−</button><b>${x.quantity}</b><button class="qty" onclick="changeQty(${i},1)">+</button></div></div>`).join('') : '<div class="empty">Seu carrinho está vazio.</div>';
  $('#cartTotal').textContent = money(total);
  $('#cartCountBadge').textContent = totalQty;
  const topBadge = $('#storeCartBadge');
  if (topBadge) {
    topBadge.textContent = totalQty;
    topBadge.classList.toggle('has-items', totalQty > 0);
  }
  const cartButton = $('#storeCartButton');
  if (cartButton) {
    cartButton.classList.toggle('has-items', totalQty > 0);
    cartButton.setAttribute('aria-label', totalQty ? `Abrir carrinho com ${totalQty} ${totalQty === 1 ? 'item' : 'itens'}` : 'Abrir carrinho vazio');
  }
}

function setCartDrawer(open) {
  const drawer = $('#cartPanel');
  const backdrop = $('#cartDrawerBackdrop');
  const trigger = $('#storeCartButton');
  if (!drawer || !backdrop) return;
  drawer.classList.toggle('open', open);
  backdrop.classList.toggle('open', open);
  drawer.setAttribute('aria-hidden', String(!open));
  backdrop.setAttribute('aria-hidden', String(!open));
  trigger?.setAttribute('aria-expanded', String(open));
  document.body.classList.toggle('cart-drawer-open', open);
  if (open) setTimeout(() => $('#cartCloseButton')?.focus(), 120);
}

function openCartDrawer() { setCartDrawer(true); }
function closeCartDrawer() { setCartDrawer(false); }
window.openCartDrawer = openCartDrawer;
window.closeCartDrawer = closeCartDrawer;
$('#storeCartButton')?.addEventListener('click', openCartDrawer);
$('#cartCloseButton')?.addEventListener('click', closeCartDrawer);
$('#cartDrawerBackdrop')?.addEventListener('click', closeCartDrawer);
document.addEventListener('keydown', (event) => { if (event.key === 'Escape') closeCartDrawer(); });

async function loadServices() {
  serviceData = await api(`/api/public/stores/${encodeURIComponent(slug)}/services`);
  const caps = store.capabilities || {};
  const serviceCount = $('#serviceResultsCount');
  if (serviceCount) serviceCount.textContent = `${(serviceData.services || []).length} ${(serviceData.services || []).length === 1 ? 'serviço disponível' : 'serviços disponíveis'}`;
  $('#serviceGrid').innerHTML = serviceData.services.length ? serviceData.services.map(s => `<article class="service-card service-card-v2">
    <div class="service-media">${s.image_url ? `<img src="${escapeHtml(assetUrl(s.image_url))}" alt="${escapeHtml(s.name)}" loading="lazy">` : `<span>${initials(s.name)}</span>`}</div>
    <div class="card-body">
      <div class="service-meta"><span class="badge">${s.duration_minutes} min</span>${Number(s.price) > 0 ? '<span>Preço definido</span>' : '<span>Sob orçamento</span>'}</div>
      <h3>${escapeHtml(s.name)}</h3>
      <p>${escapeHtml(s.description || 'Serviço disponível para atendimento.')}</p>
      <div class="service-footer"><span class="price">${Number(s.price) > 0 ? money(s.price) : 'Sob orçamento'}</span><div class="row-actions">${caps.appointments ? `<button class="btn primary small" onclick="openAppointment(${s.id})">Agendar</button>` : ''}${caps.quotes ? `<button class="btn ghost small" onclick="openQuote(${s.id})">Orçamento</button>` : ''}</div></div>
    </div>
  </article>`).join('') : '<div class="empty empty-wide">Nenhum serviço cadastrado.</div>';

  const activePros = (serviceData.professionals || []).filter(p => p.is_active !== false);
  if (caps.appointments && activePros.length) {
    $('#professionalsShowcase').classList.remove('hidden');
    $('#professionalGrid').innerHTML = activePros.map(p => `<article class="professional-card">
      <div class="professional-avatar">${p.image_url ? `<img src="${escapeHtml(assetUrl(p.image_url))}" alt="${escapeHtml(p.name)}" loading="lazy">` : `<span>${initials(p.name)}</span>`}</div>
      <div><h3>${escapeHtml(p.name)}</h3><p>${escapeHtml(p.description || 'Profissional disponível para atendimento.')}</p><small>${p.service_ids.length} ${p.service_ids.length === 1 ? 'serviço' : 'serviços'} disponível(is)</small></div>
    </article>`).join('');
  }
}

function bookingStep(step) {
  $$('[data-booking-step]').forEach(el => el.classList.toggle('hidden', Number(el.dataset.bookingStep) !== step));
  const markers = $$('.booking-progress span');
  markers.forEach((marker, index) => marker.classList.toggle('active', index < step));
}

function dateInputBounds(input) {
  const now = new Date();
  const min = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const max = new Date(min); max.setDate(max.getDate() + 180);
  const format = value => `${value.getFullYear()}-${String(value.getMonth()+1).padStart(2,'0')}-${String(value.getDate()).padStart(2,'0')}`;
  input.min = format(min);
  input.max = format(max);
}

window.openAppointment = function openAppointment(serviceId) {
  const s = serviceData.services.find(x => x.id === serviceId);
  if (!s) return;
  const form = $('#appointmentForm');
  form.reset();
  renderPaymentSelects();
  form.service_id.value = serviceId;
  form.starts_at.value = '';
  $('#appointmentService').innerHTML = `<div><span class="section-kicker">Serviço escolhido</span><strong>${escapeHtml(s.name)}</strong><small>${s.duration_minutes} min · ${Number(s.price) > 0 ? money(s.price) : 'Preço sob consulta'}</small></div>`;
  const pros = serviceData.professionals.filter(p => p.service_ids.includes(serviceId));
  form.professional_id.innerHTML = '<option value="">Selecione</option>' + pros.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('');
  $('#appointmentProfessionals').innerHTML = pros.length ? pros.map(p => `<button type="button" class="booking-pro-card" data-professional-id="${p.id}">
      <span class="booking-pro-avatar">${p.image_url ? `<img src="${escapeHtml(assetUrl(p.image_url))}" alt="">` : initials(p.name)}</span>
      <span><b>${escapeHtml(p.name)}</b><small>${escapeHtml(p.description || 'Disponível para este serviço')}</small></span>
    </button>`).join('') : '<div class="notice">Nenhum profissional disponível para este serviço.</div>';
  $('#appointmentProfessionals').querySelectorAll('[data-professional-id]').forEach(btn => btn.onclick = () => {
    form.professional_id.value = btn.dataset.professionalId;
    $('#appointmentProfessionals').querySelectorAll('.booking-pro-card').forEach(x => x.classList.toggle('selected', x === btn));
    refreshSlots();
  });
  $('#appointmentSlots').innerHTML = '<span class="muted">Escolha profissional e data para ver os horários.</span>';
  dateInputBounds(form.date);
  bookingStep(1);
  openModal('appointmentModal');
};

async function refreshSlots() {
  const f = $('#appointmentForm');
  f.starts_at.value = '';
  if (!f.professional_id.value || !f.date.value) {
    $('#appointmentSlots').innerHTML = '<span class="muted">Escolha profissional e data para ver os horários.</span>';
    return;
  }
  $('#appointmentSlots').innerHTML = '<span class="muted">Buscando horários...</span>';
  try {
    const offset = -new Date().getTimezoneOffset();
    const d = await api(`/api/public/stores/${encodeURIComponent(slug)}/availability?service_id=${f.service_id.value}&professional_id=${f.professional_id.value}&date=${f.date.value}&utc_offset_minutes=${offset}&slot_interval_minutes=15`);
    $('#appointmentSlots').innerHTML = d.slots.length ? d.slots.map(slot => `<button type="button" class="slot-chip" data-slot="${escapeHtml(slot.starts_at)}">${new Date(slot.starts_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</button>`).join('') : '<div class="notice">Não há horários disponíveis nesta data. Tente outro dia.</div>';
    $('#appointmentSlots').querySelectorAll('[data-slot]').forEach(btn => btn.onclick = () => {
      f.starts_at.value = btn.dataset.slot;
      $('#appointmentSlots').querySelectorAll('.slot-chip').forEach(x => x.classList.toggle('selected', x === btn));
    });
  } catch (e) { showToast(e.message, 'error'); }
}
$('#appointmentForm').professional_id.onchange = refreshSlots;
$('#appointmentForm').date.onchange = refreshSlots;

$('#bookingNextBtn').onclick = () => {
  const f = $('#appointmentForm');
  if (!f.professional_id.value) return showToast('Escolha um profissional.', 'error');
  if (!f.date.value) return showToast('Escolha uma data.', 'error');
  if (!f.starts_at.value) return showToast('Escolha um horário disponível.', 'error');
  const service = serviceData.services.find(x => x.id === Number(f.service_id.value));
  const professional = serviceData.professionals.find(x => x.id === Number(f.professional_id.value));
  const when = new Date(f.starts_at.value);
  $('#bookingChosenSummary').innerHTML = `<span class="section-kicker">Confira sua escolha</span><strong>${escapeHtml(service.name)}</strong><span>${escapeHtml(professional.name)} · ${when.toLocaleDateString('pt-BR')} às ${when.toLocaleTimeString('pt-BR', {hour:'2-digit',minute:'2-digit'})}</span>`;
  bookingStep(2);
};
$('#bookingBackBtn').onclick = () => bookingStep(1);

$('#appointmentForm').onsubmit = async e => {
  e.preventDefault(); const f = e.currentTarget;
  if (!f.starts_at.value) return showToast('Escolha um horário.', 'error');
  try {
    const result = await api(`/api/public/stores/${encodeURIComponent(slug)}/appointments`, { method: 'POST', body: JSON.stringify({ customer: { name: f.name.value, email: f.email.value || null, phone: f.phone.value || null }, service_id: Number(f.service_id.value), professional_id: Number(f.professional_id.value), starts_at: f.starts_at.value, payment_method: f.payment_method?.value || null, payment_document: f.payment_document?.value || null, notes: f.notes.value || null }) });
    closeModal('appointmentModal');
    const start = new Date(result.starts_at);
    $('#appointmentSuccessText').textContent = `${result.service.name} com ${result.professional.name}, ${start.toLocaleDateString('pt-BR')} às ${start.toLocaleTimeString('pt-BR', {hour:'2-digit',minute:'2-digit'})}.`;
    $('#appointmentProtocol').innerHTML = `<small>Protocolo de acompanhamento</small><strong>${escapeHtml(result.public_token)}</strong>`;
    $('#appointmentPaymentBox').innerHTML = result.payment ? paymentResultHtml(result.payment) : '<div class="notice">Pagamento será combinado diretamente com a empresa.</div>';
    watchOnlinePayment(result.payment, '#appointmentPaymentBox');
    $('#appointmentTrackLink').href = `acompanhar.html?slug=${encodeURIComponent(slug)}&tipo=agendamento&token=${encodeURIComponent(result.public_token)}`;
    const appointmentAccountLink = $('#appointmentAccountLink');
    if (appointmentAccountLink) appointmentAccountLink.href = `cliente.html?slug=${encodeURIComponent(slug)}&modo=cadastro&tipo=agendamento&token=${encodeURIComponent(result.public_token)}`;
    formResetAppointment(f);
    openModal('appointmentSuccessModal');
  } catch (err) { showToast(err.message, 'error'); }
};

function formResetAppointment(form) {
  form.reset();
  form.starts_at.value = '';
  $('#appointmentSlots').innerHTML = '<span class="muted">Escolha profissional e data para ver os horários.</span>';
}

window.openQuote = function openQuote(serviceId) {
  const f = $('#quoteForm'); f.service_id.value = serviceId; const s = serviceData.services.find(x => x.id === serviceId); f.title.value = `Orçamento para ${s.name}`; openModal('quoteModal');
};
$('#quoteForm').onsubmit = async e => {
  e.preventDefault(); const f = e.currentTarget;
  try {
    const result = await api(`/api/public/stores/${encodeURIComponent(slug)}/quotes`, { method: 'POST', body: JSON.stringify({ customer: { name: f.name.value, email: f.email.value || null, phone: f.phone.value || null }, service_id: f.service_id.value ? Number(f.service_id.value) : null, title: f.title.value, description: f.description.value, preferred_contact: f.preferred_contact.value, service_address: f.service_address.value || null, service_city: f.service_city.value || null, service_state: null, service_zip_code: null, attachments: [] }) });
    closeModal('quoteModal'); f.reset(); showToast(`Orçamento enviado. Protocolo: ${result.public_token}`);
  } catch (err) { showToast(err.message, 'error'); }
};

$('#checkoutBtn').onclick = () => {
  if (!cart.length) return showToast('Adicione um produto ao carrinho.', 'error');
  closeCartDrawer();
  if (selectedCouponCode && $('#checkoutCouponCode') && !$('#checkoutCouponCode').value) $('#checkoutCouponCode').value = selectedCouponCode;
  validatedCoupon = null;
  renderCheckoutSummary();
  openModal('checkoutModal');
};

$('#applyCheckoutCouponBtn')?.addEventListener('click', () => validateCheckoutCoupon().catch(() => {}));
$('#checkoutCouponCode')?.addEventListener('input', () => {
  validatedCoupon = null;
  const hint = $('#checkoutCouponHint');
  hint?.classList.add('hidden');
  renderCheckoutSummary();
});

$('#checkoutForm').fulfillment_method.onchange = (event) => {
  const delivery = event.target.value === 'ENTREGA';
  $('#deliveryFields').classList.toggle('hidden', !delivery);
  $('#checkoutForm').delivery_address.required = delivery;
};

$('#checkoutForm').onsubmit = async e => {
  e.preventDefault(); const f = e.currentTarget;
  try {
    const couponCode = f.coupon_code.value.trim();
    if (couponCode) await validateCheckoutCoupon(false);
    const result = await api(`/api/public/stores/${encodeURIComponent(slug)}/orders`, { method: 'POST', body: JSON.stringify({
      customer: { name: f.name.value, email: f.email.value || null, phone: f.phone.value || null },
      items: cart.map(({ product_id, variant_id, selected_option_item_ids, quantity }) => ({ product_id, variant_id, selected_option_item_ids: selected_option_item_ids || [], quantity })),
      payment_method: f.payment_method.value, payment_document: f.payment_document?.value || null, fulfillment_method: f.fulfillment_method.value, coupon_code: f.coupon_code.value || null,
      notes: f.notes.value || null, delivery_address: f.delivery_address.value || null, delivery_city: f.delivery_city.value || null, delivery_state: f.delivery_state.value || null, delivery_zip_code: f.delivery_zip_code.value || null,
    }) });
    cart = []; saveCart(); selectedCouponCode = null; validatedCoupon = null; closeModal('checkoutModal'); f.reset(); $('#checkoutCouponHint')?.classList.add('hidden'); $('#deliveryFields').classList.add('hidden');
    const discountText = Number(result.discount_amount) > 0 ? ` Desconto: ${money(result.discount_amount)}.` : '';
    showToast(`Pedido ${result.order_number} criado. Total: ${money(result.total)}.${discountText}`);
    $('#orderSuccessTitle').textContent = `Pedido ${result.order_number} criado!`;
    $('#orderSuccessText').textContent = `Total ${money(result.total)}. Agora você pode acompanhar o andamento em tempo real.`;
    $('#orderSuccessProtocol').innerHTML = `<small>Protocolo de acompanhamento</small><strong>${escapeHtml(result.public_token)}</strong>`;
    $('#orderPaymentBox').innerHTML = result.payment ? paymentResultHtml(result.payment) : '<div class="notice">Pagamento será combinado diretamente com a empresa.</div>';
    watchOnlinePayment(result.payment, '#orderPaymentBox');
    $('#orderTrackLink').href = `acompanhar.html?slug=${encodeURIComponent(slug)}&tipo=pedido&token=${encodeURIComponent(result.public_token)}`;
    $('#orderAccountLink').href = `cliente.html?slug=${encodeURIComponent(slug)}&modo=cadastro&tipo=pedido&token=${encodeURIComponent(result.public_token)}`;
    openModal('orderSuccessModal');
  } catch (err) { showToast(err.message, 'error'); }
};


async function loadResources() {
  resourcesData = await api(`/api/public/stores/${encodeURIComponent(slug)}/resources`);
  const rows = resourcesData.resources || [];
  $('#resourceGrid').innerHTML = rows.length ? rows.map(item => `<article class="service-card service-card-v2">
    <div class="service-media">${item.image_url ? `<img src="${escapeHtml(assetUrl(item.image_url))}" alt="${escapeHtml(item.name)}" loading="lazy">` : `<span>${initials(item.name)}</span>`}</div>
    <div class="card-body"><div class="service-meta"><span class="badge">${escapeHtml(item.resource_type)}</span><span>Até ${item.capacity} pessoa(s)</span></div><h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.description || 'Disponível para reserva.')}</p><div class="service-footer"><span class="price">${Number(item.price_per_day) > 0 ? `${money(item.price_per_day)} / dia` : 'Consultar'}</span><button class="btn primary small" onclick="openReservation(${item.id})">Reservar</button></div></div>
  </article>`).join('') : '<div class="empty empty-wide">Nenhum recurso disponível para reserva.</div>';
}

window.openReservation = function openReservation(id) {
  const item = resourcesData?.resources?.find(x => x.id === id);
  if (!item) return;
  const f = $('#reservationForm'); f.reset(); f.resource_id.value = id; f.guests.value = 1; renderPaymentSelects();
  $('#reservationTitle').textContent = `Reservar ${item.name}`;
  openModal('reservationModal');
};

$('#reservationForm').onsubmit = async (event) => {
  event.preventDefault(); const f = event.currentTarget;
  try {
    const out = await api(`/api/public/stores/${encodeURIComponent(slug)}/reservations`, { method: 'POST', body: JSON.stringify({
      customer: { name: f.name.value, email: f.email.value || null, phone: f.phone.value || null },
      resource_id: Number(f.resource_id.value), starts_at: new Date(f.starts_at.value).toISOString(), ends_at: new Date(f.ends_at.value).toISOString(), guests: Number(f.guests.value), payment_method: f.payment_method?.value || null, payment_document: f.payment_document?.value || null, notes: f.notes.value || null,
    })});
    closeModal('reservationModal'); f.reset();
    showToast(`Reserva criada. Protocolo: ${out.public_token}. Total estimado: ${money(out.total)}`);
    if (out.payment) showPaymentModal(out.payment, `Pagamento da reserva`);
  } catch (err) { showToast(err.message, 'error'); }
};

async function loadRentalItems() {
  rentalItemsData = await api(`/api/public/stores/${encodeURIComponent(slug)}/rental-items`);
  const rows = rentalItemsData.items || [];
  $('#rentalGrid').innerHTML = rows.length ? rows.map(item => `<article class="service-card service-card-v2">
    <div class="service-media">${item.image_url ? `<img src="${escapeHtml(assetUrl(item.image_url))}" alt="${escapeHtml(item.name)}" loading="lazy">` : `<span>${initials(item.name)}</span>`}</div>
    <div class="card-body"><div class="service-meta"><span class="badge">${escapeHtml(item.sku || 'Locação')}</span><span>${item.quantity_total} unidade(s)</span></div><h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.description || 'Item disponível para locação.')}</p><div class="service-footer"><span class="price">${money(item.daily_rate)} / dia</span><button class="btn primary small" onclick="openRental(${item.id})">Alugar</button></div></div>
  </article>`).join('') : '<div class="empty empty-wide">Nenhum item disponível para locação.</div>';
}

window.openRental = function openRental(id) {
  const item = rentalItemsData?.items?.find(x => x.id === id);
  if (!item) return;
  const f = $('#rentalForm'); f.reset(); f.rental_item_id.value = id; f.quantity.value = 1; renderPaymentSelects();
  $('#rentalTitle').textContent = `Alugar ${item.name}`;
  $('#rentalAvailability').textContent = `Diária: ${money(item.daily_rate)} · Caução por unidade: ${money(item.deposit_amount)}`;
  openModal('rentalModal');
};

async function refreshRentalAvailability() {
  const f = $('#rentalForm');
  if (!f.rental_item_id.value || !f.starts_at.value || !f.ends_at.value) return;
  try {
    const query = new URLSearchParams({ item_id: f.rental_item_id.value, starts_at: new Date(f.starts_at.value).toISOString(), ends_at: new Date(f.ends_at.value).toISOString() });
    const out = await api(`/api/public/stores/${encodeURIComponent(slug)}/rentals/availability?${query}`);
    $('#rentalAvailability').textContent = `${out.available_quantity} unidade(s) disponível(is) · ${out.rental_days} dia(s) · diária ${money(out.daily_rate)} · caução ${money(out.deposit_amount)}`;
  } catch (err) { $('#rentalAvailability').textContent = err.message; }
}
$('#rentalForm').starts_at.onchange = refreshRentalAvailability;
$('#rentalForm').ends_at.onchange = refreshRentalAvailability;
$('#rentalForm').quantity.onchange = refreshRentalAvailability;

$('#rentalForm').onsubmit = async (event) => {
  event.preventDefault(); const f = event.currentTarget;
  try {
    const out = await api(`/api/public/stores/${encodeURIComponent(slug)}/rentals`, { method: 'POST', body: JSON.stringify({
      customer: { name: f.name.value, email: f.email.value || null, phone: f.phone.value || null },
      rental_item_id: Number(f.rental_item_id.value), starts_at: new Date(f.starts_at.value).toISOString(), ends_at: new Date(f.ends_at.value).toISOString(), quantity: Number(f.quantity.value), payment_method: f.payment_method?.value || null, payment_document: f.payment_document?.value || null, notes: f.notes.value || null,
    })});
    closeModal('rentalModal'); f.reset();
    showToast(`Locação criada. Protocolo: ${out.public_token}. Total estimado: ${money(out.total)}`);
    if (out.payment) showPaymentModal(out.payment, `Pagamento da locação`);
  } catch (err) { showToast(err.message, 'error'); }
};

function renderContact() {
  const bits = [store.phone, store.email, [store.address, store.city, store.state].filter(Boolean).join(', ')].filter(Boolean);
  $('#contactText').textContent = bits.length ? bits.join(' · ') : 'Use os canais disponíveis para falar com a empresa.';
  const actions = [];
  if (store.whatsapp) { const number = store.whatsapp.replace(/\D/g, ''); actions.push(`<a class="btn primary" target="_blank" rel="noopener" href="https://wa.me/${number}">Abrir WhatsApp</a>`); }
  if (store.email) actions.push(`<a class="btn ghost" href="mailto:${escapeHtml(store.email)}">Enviar e-mail</a>`);
  $('#contactActions').innerHTML = actions.join('');
}

function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
$$('[data-close]').forEach(b => b.onclick = () => closeModal(b.dataset.close));
$$('.modal-backdrop').forEach(m => m.addEventListener('click', e => { if (e.target === m) closeModal(m.id); }));
init();
