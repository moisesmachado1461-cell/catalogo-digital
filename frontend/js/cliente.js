const customerQs = new URLSearchParams(location.search);
const customerSlug = customerQs.get('slug') || customerQs.get('loja') || '';
const customerTrackingToken = customerQs.get('token') || '';
const customerTrackingType = String(customerQs.get('tipo') || customerQs.get('type') || '').toUpperCase();
const customerTokenKey = `catalogo_customer_token_${customerSlug || 'default'}`;
let customerStore = null;
let customerAccount = null;
let customerOrders = [];
let customerAppointments = [];

const cq = selector => document.querySelector(selector);

function customerInitials(value = '') {
  return String(value).trim().split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0]).join('').toUpperCase() || 'CD';
}

function customerToken() {
  return sessionStorage.getItem(customerTokenKey) || '';
}

function setCustomerToken(value) {
  if (value) sessionStorage.setItem(customerTokenKey, value);
  else sessionStorage.removeItem(customerTokenKey);
}

async function customerRequest(path, options = {}, auth = true) {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const token = customerToken();
  if (auth && token) headers.set('Authorization', `Bearer ${token}`);
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers, cache: 'no-store' });
  } catch (_error) {
    throw new Error('Não foi possível conectar à API. Tente novamente.');
  }
  const text = await response.text();
  let data = null;
  if (text) { try { data = JSON.parse(text); } catch { data = text; } }
  if (!response.ok) {
    if (response.status === 401 && auth) setCustomerToken('');
    const message = data?.detail || data?.message || `Erro HTTP ${response.status}`;
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
  }
  return data;
}

function customerApplyTheme(store) {
  const primary = store?.primary_color || '#6d5dfc';
  const secondary = store?.secondary_color || '#4f46e5';
  document.documentElement.style.setProperty('--brand', primary);
  document.documentElement.style.setProperty('--brand2', secondary);
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', primary);
  const logo = store?.logo_url ? `<img src="${escapeHtml(assetUrl(store.logo_url))}" alt="Logo de ${escapeHtml(store.name)}">` : escapeHtml(customerInitials(store?.name));
  cq('#customerBrandMark').innerHTML = logo;
  cq('#customerStoreBadge').innerHTML = logo;
  cq('#customerMobileBrandMark').innerHTML = logo;
  cq('#customerBrandName').textContent = store?.name || 'Catálogo Digital';
  cq('#customerStoreTitle').textContent = store?.name || 'Sua loja';
  cq('#customerMobileBrandName').textContent = store?.name || 'Sua loja';
  const storeHref = `loja.html?slug=${encodeURIComponent(customerSlug)}`;
  cq('#customerBackStore').href = storeHref;
  cq('#customerBackStoreAuth').href = storeHref;
  cq('#customerBackStoreMobile').href = storeHref;
  cq('#customerBrand').href = storeHref;
  document.title = `Minha conta — ${store?.name || 'Catálogo Digital'}`;
}

function normalizeTrackingType(value) {
  const upper = String(value || '').toUpperCase();
  if (['ORDER', 'PEDIDO'].includes(upper)) return 'ORDER';
  if (['APPOINTMENT', 'AGENDAMENTO'].includes(upper)) return 'APPOINTMENT';
  return null;
}

function switchAuthMode(mode) {
  const register = mode === 'register';
  cq('#customerLoginForm').classList.toggle('hidden', register);
  cq('#customerRegisterForm').classList.toggle('hidden', !register);
  cq('#customerLoginTab').classList.toggle('active', !register);
  cq('#customerRegisterTab').classList.toggle('active', register);
  cq('#customerLoginTab').setAttribute('aria-selected', register ? 'false' : 'true');
  cq('#customerRegisterTab').setAttribute('aria-selected', register ? 'true' : 'false');
  const heading = cq('.customer-auth-heading h2');
  const copy = cq('.customer-auth-heading p');
  if (heading) heading.textContent = register ? 'Crie sua conta' : 'Acesse sua conta';
  if (copy) copy.textContent = register
    ? 'Cadastre-se para reunir pedidos e agendamentos em um só lugar.'
    : 'Entre para acompanhar seus pedidos, agendamentos e histórico.';
}

cq('#customerLoginTab').onclick = () => switchAuthMode('login');
cq('#customerRegisterTab').onclick = () => switchAuthMode('register');

function orderStatusLabel(status, fulfillment) {
  const map = {PENDENTE:'Recebido',CONFIRMADO:'Confirmado',EM_PREPARACAO:'Em preparação',PRONTO:fulfillment === 'RETIRADA' ? 'Pronto para retirada' : 'Pronto',SAIU_PARA_ENTREGA:'Saiu para entrega',ENTREGUE:fulfillment === 'RETIRADA' ? 'Retirado' : 'Entregue',CANCELADO:'Cancelado'};
  return map[status] || status;
}

function appointmentStatusLabel(status) {
  return ({PENDENTE:'Pendente',CONFIRMADO:'Confirmado',CONCLUIDO:'Concluído',CANCELADO:'Cancelado',NAO_COMPARECEU:'Não compareceu'})[status] || status;
}

function statusClass(status) {
  if (['ENTREGUE','CONCLUIDO','CONFIRMADO'].includes(status)) return 'is-success';
  if (['CANCELADO','NAO_COMPARECEU'].includes(status)) return 'is-danger';
  return 'is-warning';
}

function trackingHref(type, token) {
  return `acompanhar.html?slug=${encodeURIComponent(customerSlug)}&tipo=${type === 'ORDER' ? 'pedido' : 'agendamento'}&token=${encodeURIComponent(token)}`;
}

function renderCustomerPortal() {
  const name = customerAccount?.name || 'Cliente';
  cq('#customerAuthView').classList.add('hidden');
  cq('#customerPortalView').classList.remove('hidden');
  document.body.classList.remove('customer-auth-active');
  cq('#customerGreeting').textContent = `Olá, ${name.split(' ')[0]}!`;
  cq('#customerPortalSubtitle').textContent = `Acompanhe sua atividade em ${customerAccount?.store?.name || customerStore?.name || 'sua loja'}.`;
  const pendingOrders = customerOrders.filter(row => !['ENTREGUE','CANCELADO'].includes(row.status)).length;
  const upcomingAppointments = customerAppointments.filter(row => ['PENDENTE','CONFIRMADO'].includes(row.status)).length;
  cq('#customerSummary').innerHTML = `
    <div class="customer-summary-card"><span>Pedidos</span><strong>${customerOrders.length}</strong></div>
    <div class="customer-summary-card"><span>Em andamento</span><strong>${pendingOrders}</strong></div>
    <div class="customer-summary-card"><span>Próximos agendamentos</span><strong>${upcomingAppointments}</strong></div>`;

  cq('#customerOrdersList').innerHTML = customerOrders.length ? customerOrders.map(order => `
    <article class="customer-record">
      <div class="customer-record-head"><div><small>Pedido</small><h3>${escapeHtml(order.order_number)}</h3></div><span class="customer-status ${statusClass(order.status)}">${escapeHtml(orderStatusLabel(order.status, order.fulfillment_method))}</span></div>
      <div class="customer-record-meta"><span>${new Date(order.created_at).toLocaleDateString('pt-BR')}</span><span>${order.items.length} item(ns)</span><span>${money(order.total)}</span></div>
      <div class="customer-record-actions"><a class="btn primary small" href="${trackingHref('ORDER', order.public_token)}">Acompanhar pedido</a></div>
    </article>`).join('') : '<div class="empty">Você ainda não possui pedidos vinculados a esta conta.</div>';

  cq('#customerAppointmentsList').innerHTML = customerAppointments.length ? customerAppointments.map(item => {
    const start = new Date(item.starts_at);
    return `<article class="customer-record">
      <div class="customer-record-head"><div><small>Agendamento</small><h3>${escapeHtml(item.service?.name || 'Serviço')}</h3></div><span class="customer-status ${statusClass(item.status)}">${escapeHtml(appointmentStatusLabel(item.status))}</span></div>
      <div class="customer-record-meta"><span>${start.toLocaleDateString('pt-BR')}</span><span>${start.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}</span><span>${escapeHtml(item.professional?.name || 'Profissional')}</span></div>
      <div class="customer-record-actions"><a class="btn primary small" href="${trackingHref('APPOINTMENT', item.public_token)}">Acompanhar agendamento</a></div>
    </article>`;
  }).join('') : '<div class="empty">Você ainda não possui agendamentos vinculados a esta conta.</div>';
}

async function loadCustomerData() {
  customerAccount = await customerRequest('/api/customer/me');
  customerApplyTheme(customerAccount.store);
  [customerOrders, customerAppointments] = await Promise.all([
    customerRequest('/api/customer/orders'),
    customerRequest('/api/customer/appointments'),
  ]);
  renderCustomerPortal();
}

async function claimFromUrl() {
  const type = normalizeTrackingType(customerTrackingType);
  if (!type || !customerTrackingToken) return;
  try {
    await customerRequest('/api/customer/claim', { method:'POST', body:JSON.stringify({tracking_type:type,tracking_token:customerTrackingToken}) });
  } catch (error) {
    showToast(error.message, 'error');
  }
}

cq('#customerLoginForm').onsubmit = async event => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const result = await customerRequest('/api/customer/login', { method:'POST', body:JSON.stringify({store_slug:customerSlug,email:form.email.value,password:form.password.value}) }, false);
    setCustomerToken(result.access_token);
    await claimFromUrl();
    await loadCustomerData();
  } catch (error) { showToast(error.message, 'error'); }
};

cq('#customerRegisterForm').onsubmit = async event => {
  event.preventDefault();
  const form = event.currentTarget;
  if (form.password.value !== form.password_confirm.value) return showToast('As senhas não são iguais.', 'error');
  try {
    const type = normalizeTrackingType(customerTrackingType);
    const result = await customerRequest('/api/customer/register', { method:'POST', body:JSON.stringify({
      store_slug:customerSlug,
      name:form.name.value,
      email:form.email.value,
      phone:form.phone.value || null,
      password:form.password.value,
      tracking_type:type,
      tracking_token:type ? customerTrackingToken : null,
    }) }, false);
    setCustomerToken(result.access_token);
    await loadCustomerData();
    showToast('Conta criada com sucesso.');
  } catch (error) { showToast(error.message, 'error'); }
};

cq('#customerLogoutBtn').onclick = () => {
  setCustomerToken('');
  customerAccount = null;
  cq('#customerPortalView').classList.add('hidden');
  cq('#customerAuthView').classList.remove('hidden');
  document.body.classList.add('customer-auth-active');
  switchAuthMode('login');
};

for (const toggle of document.querySelectorAll('[data-password-toggle]')) {
  toggle.addEventListener('click', () => {
    const input = toggle.closest('.customer-input-wrap')?.querySelector('input');
    if (!input) return;
    const show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    toggle.textContent = show ? 'Ocultar' : 'Ver';
    toggle.setAttribute('aria-label', show ? 'Ocultar senha' : 'Mostrar senha');
  });
}

for (const button of document.querySelectorAll('[data-customer-tab]')) {
  button.onclick = () => {
    document.querySelectorAll('[data-customer-tab]').forEach(row => row.classList.toggle('active', row === button));
    const orders = button.dataset.customerTab === 'orders';
    cq('#customerOrdersPanel').classList.toggle('hidden', !orders);
    cq('#customerAppointmentsPanel').classList.toggle('hidden', orders);
  };
}

async function startCustomerPortal() {
  if (!customerSlug) {
    cq('#customerStoreTitle').textContent = 'Link incompleto';
    cq('#customerAuthView').innerHTML = '<div class="empty">Abra a área do cliente a partir da página da loja.</div>';
    return;
  }
  try {
    customerStore = await api(`/api/public/stores/${encodeURIComponent(customerSlug)}`);
    customerApplyTheme(customerStore);
  } catch (error) {
    cq('#customerStoreTitle').textContent = 'Loja não encontrada';
    cq('#customerAuthView').innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
    return;
  }
  if (customerTrackingToken && normalizeTrackingType(customerTrackingType)) {
    cq('#customerClaimNotice').textContent = 'Este cadastro será vinculado ao acompanhamento que trouxe você até aqui.';
    cq('#customerClaimNotice').classList.remove('hidden');
  }
  if (String(customerQs.get('modo') || '').toLowerCase() === 'cadastro') switchAuthMode('register');
  if (customerToken()) {
    try {
      await claimFromUrl();
      await loadCustomerData();
    } catch (_error) {
      setCustomerToken('');
    }
  }
}

startCustomerPortal();
