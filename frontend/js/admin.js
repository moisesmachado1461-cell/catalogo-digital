const { query: $, queryAll: $$, initials, nullable, checked, optionSelected, toDateTimeLocal } = window.CatalogoUtils;

let me = null;
let store = null;
let categories = [];
let products = [];
let orders = [];
let inventory = [];
let services = [];
let professionals = [];
let appointments = [];
let quotes = [];
let coupons = [];
let promotions = [];
let resources = [];
let reservations = [];
let rentalItems = [];
let rentals = [];
let payments = [];
let paymentSettings = null;
let subscriptionInfo = null;
let billingOverview = null;
let availableBillingPlans = [];
let pixPollTimer = null;
let privacyRequests = [];
let auditLogs = [];
let reportOverview = null;
let reportSeries = [];
let reportTopItems = null;

const labels = {
  dashboard: 'Dashboard',
  categories: 'Categorias',
  products: 'Produtos',
  orders: 'Pedidos',
  inventory: 'Estoque',
  services: 'Serviços',
  professionals: 'Profissionais',
  appointments: 'Agendamentos',
  quotes: 'Orçamentos',
  coupons: 'Cupons',
  promotions: 'Promoções',
  resources: 'Recursos',
  reservations: 'Reservas',
  rentalItems: 'Itens de locação',
  rentals: 'Locações',
  payments: 'Pagamentos',
  reports: 'Relatórios',
  subscription: 'Meu plano',
  privacy: 'Privacidade e auditoria',
  settings: 'Configurações',
};

const weekdayLabels = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'];

const adminMenuGroups = [
  { title: 'Visão geral', ids: ['dashboard', 'reports'] },
  { title: 'Vendas e catálogo', ids: ['categories', 'products', 'orders', 'inventory', 'coupons', 'promotions'] },
  { title: 'Serviços e agenda', ids: ['services', 'professionals', 'appointments', 'quotes'] },
  { title: 'Reservas e locação', ids: ['resources', 'reservations', 'rentalItems', 'rentals'] },
  { title: 'Financeiro', ids: ['payments', 'subscription'] },
  { title: 'Gestão', ids: ['privacy', 'settings'] },
];

const adminIconPaths = {
  dashboard: '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
  reports: '<path d="M4 19V9"/><path d="M10 19V5"/><path d="M16 19v-7"/><path d="M22 19H2"/>',
  categories: '<path d="M4 4h6v6H4z"/><path d="M14 4h6v6h-6z"/><path d="M4 14h6v6H4z"/><path d="M14 14h6v6h-6z"/>',
  products: '<path d="M6 7h12l1 13H5L6 7Z"/><path d="M9 7a3 3 0 0 1 6 0"/>',
  orders: '<path d="M6 3h12v18H6z"/><path d="M9 8h6M9 12h6M9 16h4"/>',
  inventory: '<path d="m4 7 8-4 8 4-8 4-8-4Z"/><path d="M4 7v10l8 4 8-4V7"/><path d="M12 11v10"/>',
  coupons: '<path d="M4 7a3 3 0 0 0 0 6v4h16v-4a3 3 0 0 0 0-6V3H4v4Z"/><path d="M12 6v2M12 11v2M12 16v2"/>',
  promotions: '<path d="m20 12-8 8-8-8 8-8 8 8Z"/><path d="M9 9h.01M15 15h.01"/><path d="m15 9-6 6"/>',
  services: '<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="8" cy="6" r="2"/><circle cx="16" cy="12" r="2"/><circle cx="10" cy="18" r="2"/>',
  professionals: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  appointments: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/><path d="m9 15 2 2 4-4"/>',
  quotes: '<path d="M5 4h14v16H5z"/><path d="M8 8h8M8 12h8M8 16h5"/>',
  resources: '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M8 8h8v8H8z"/>',
  reservations: '<path d="M5 3v3M19 3v3"/><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 14h.01M12 14h.01M16 14h.01"/>',
  rentalItems: '<path d="M4 8h16v11H4z"/><path d="M8 8V5h8v3"/><path d="M9 13h6"/>',
  rentals: '<path d="M3 12h18"/><path d="m16 7 5 5-5 5"/><path d="m8 17-5-5 5-5"/>',
  payments: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M7 15h4"/>',
  subscription: '<path d="M12 2 5 5v6c0 5 3 9 7 11 4-2 7-6 7-11V5l-7-3Z"/><path d="m9 12 2 2 4-4"/>',
  privacy: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.83 2.83-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21h-4v-.1A1.7 1.7 0 0 0 8.6 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06-2.83-2.83.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H3v-4h.1A1.7 1.7 0 0 0 4.6 8.6a1.7 1.7 0 0 0-.34-1.88l-.06-.06 2.83-2.83.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V3h4v.1A1.7 1.7 0 0 0 15.4 4.6a1.7 1.7 0 0 0 1.88-.34l.06-.06 2.83 2.83-.06.06A1.7 1.7 0 0 0 19.4 9c.4.3.7.6 1 .6h.1v4h-.1c-.4 0-.8.2-1 .6Z"/>',
  default: '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/>',
};

function adminIcon(id) {
  const path = adminIconPaths[id] || adminIconPaths.default;
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${path}</svg>`;
}

function renderAdminIdentity() {
  const userName = me?.name || me?.full_name || 'Administrador';
  const storeName = store?.name || 'Sua loja';
  const planName = subscriptionInfo?.plan?.name || store?.subscription?.plan?.name || 'Gratuito';
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Bom dia' : hour < 18 ? 'Boa tarde' : 'Boa noite';
  const userEl = $('#adminUserName');
  const userAvatar = $('#adminUserAvatar');
  const storeAvatar = $('#sideStoreAvatar');
  const brandName = store?.panel_brand_name || 'Catálogo Digital';
  const brandNameEl = $('#adminBrandName');
  const brandMark = $('#adminBrandMark');
  if (userEl) userEl.textContent = userName;
  if (userAvatar) userAvatar.textContent = initials(userName, 'A');
  if (brandNameEl) brandNameEl.textContent = brandName;
  if (brandMark) brandMark.innerHTML = store?.panel_logo_url
    ? `<img src="${escapeHtml(assetUrl(store.panel_logo_url))}" alt="Logo de ${escapeHtml(brandName)}">`
    : escapeHtml(initials(brandName));
  if (storeAvatar) storeAvatar.innerHTML = store?.logo_url
    ? `<img src="${escapeHtml(assetUrl(store.logo_url))}" alt="Logo de ${escapeHtml(storeName)}">`
    : escapeHtml(initials(storeName));
  const greet = $('#dashboardGreeting');
  if (greet) greet.textContent = `${greeting}, ${userName.split(' ')[0]}!`;
  const greetCopy = $('#dashboardGreetingCopy');
  if (greetCopy) greetCopy.textContent = `Aqui está um resumo de ${storeName}. Veja o que precisa de atenção e continue sua operação.`;
  const badge = $('#dashboardPlanBadge');
  if (badge) badge.textContent = `Plano ${planName}`;
  const today = $('#dashboardToday');
  if (today) today.textContent = new Intl.DateTimeFormat('pt-BR', { weekday: 'long', day: '2-digit', month: 'long' }).format(new Date());
}

function renderDashboardAttention() {
  const root = $('#dashboardAttention');
  if (!root) return;
  const alerts = [];
  const pendingOrders = orders.filter(item => ['NOVO', 'PENDENTE', 'CONFIRMADO'].includes(String(item.status || '').toUpperCase())).length;
  const pendingAppointments = appointments.filter(item => ['PENDENTE', 'CONFIRMADO'].includes(String(item.status || '').toUpperCase())).length;
  const lowStock = inventory.filter(item => Number(item.quantity || 0) <= Number(item.min_quantity || item.minimum_quantity || 0)).length;
  const pendingPayments = payments.filter(item => String(item.status || '').toUpperCase() === 'PENDENTE').length;
  if (store?.capabilities?.catalog) alerts.push({ level: pendingOrders ? 'warning' : '', title: `${pendingOrders} pedido${pendingOrders === 1 ? '' : 's'} em andamento`, note: pendingOrders ? 'Acompanhe e atualize os status.' : 'Nenhum pedido aguardando ação.' });
  if (store?.capabilities?.appointments) alerts.push({ level: pendingAppointments ? 'warning' : '', title: `${pendingAppointments} agendamento${pendingAppointments === 1 ? '' : 's'} ativo${pendingAppointments === 1 ? '' : 's'}`, note: pendingAppointments ? 'Revise sua agenda de atendimento.' : 'Agenda sem pendências.' });
  if (store?.capabilities?.catalog) alerts.push({ level: lowStock ? 'danger' : '', title: `${lowStock} item${lowStock === 1 ? '' : 's'} com estoque baixo`, note: lowStock ? 'Considere repor o estoque.' : 'Estoque dentro dos limites.' });
  if (store?.capabilities?.payments && alerts.length < 3) alerts.push({ level: pendingPayments ? 'warning' : '', title: `${pendingPayments} pagamento${pendingPayments === 1 ? '' : 's'} pendente${pendingPayments === 1 ? '' : 's'}`, note: pendingPayments ? 'Há pagamentos aguardando confirmação.' : 'Financeiro em dia.' });
  if (!alerts.length) alerts.push({ level: '', title: 'Operação em dia', note: 'Nenhuma pendência importante detectada.' });
  root.innerHTML = alerts.slice(0, 3).map(item => `<div class="attention-item ${item.level}"><span class="attention-dot"></span><div class="attention-copy"><b>${escapeHtml(item.title)}</b><small>${escapeHtml(item.note)}</small></div></div>`).join('');
}

function couponValidityLabel(coupon) {
  if (!coupon.starts_at && !coupon.ends_at) return 'Sem prazo';
  const start = coupon.starts_at ? new Date(coupon.starts_at).toLocaleDateString('pt-BR') : 'agora';
  const end = coupon.ends_at ? new Date(coupon.ends_at).toLocaleDateString('pt-BR') : 'sem fim';
  return `${start} → ${end}`;
}


function imageUploadField(name, label, kind, current = '', hint = 'JPG, PNG ou WebP · máximo 8 MB') {
  const value = current || '';
  return `<div class="field full image-upload-field">
    <label>${escapeHtml(label)}</label>
    <div class="image-upload-box">
      <div class="image-upload-preview" data-preview-for="${name}">${value ? `<img src="${escapeHtml(assetUrl(value))}" alt="Prévia">` : '<span>Sem imagem</span>'}</div>
      <div class="upload-controls">
        <input class="input" name="${name}" value="${escapeHtml(value)}" placeholder="URL da imagem ou envie um arquivo">
        <label class="btn ghost upload-button">Enviar imagem<input type="file" accept="image/jpeg,image/png,image/webp" data-upload-target="${name}" data-upload-kind="${kind}" hidden></label>
        <small>${escapeHtml(hint)}</small>
      </div>
    </div>
  </div>`;
}

function refreshImagePreview(form, fieldName) {
  const preview = form.querySelector(`[data-preview-for="${fieldName}"]`);
  const input = form.elements[fieldName];
  if (!preview || !input) return;
  const url = String(input.value || '').trim();
  preview.innerHTML = url ? `<img src="${escapeHtml(assetUrl(url))}" alt="Prévia" onerror="this.parentElement.innerHTML='<span>Imagem inválida</span>'">` : '<span>Sem imagem</span>';
}

function wireImageUploads(form, onChange = null) {
  if (!form) return;
  form.querySelectorAll('[data-upload-target]').forEach((fileInput) => {
    const fieldName = fileInput.dataset.uploadTarget;
    const urlInput = form.elements[fieldName];
    const button = fileInput.closest('.upload-button');
    if (urlInput) {
      urlInput.addEventListener('input', () => {
        refreshImagePreview(form, fieldName);
        onChange?.();
      });
    }
    fileInput.addEventListener('change', async () => {
      const file = fileInput.files?.[0];
      if (!file) return;
      const oldText = button?.childNodes?.[0]?.textContent || 'Enviar imagem';
      if (button) {
        button.classList.add('is-loading');
        button.childNodes[0].textContent = 'Enviando...';
      }
      try {
        const result = await uploadImage(file, fileInput.dataset.uploadKind);
        if (urlInput) urlInput.value = result.url;
        refreshImagePreview(form, fieldName);
        onChange?.();
        showToast('Imagem enviada e otimizada.');
      } catch (error) {
        showToast(error.message, 'error');
      } finally {
        if (button) {
          button.classList.remove('is-loading');
          button.childNodes[0].textContent = oldText;
        }
        fileInput.value = '';
      }
    });
  });
}

function categoryName(id) {
  return categories.find((item) => item.id === id)?.name || 'Sem categoria';
}

function openModal(title, eyebrow, html) {
  $('#modalTitle').textContent = title;
  $('#modalEyebrow').textContent = eyebrow || 'Gerenciar';
  $('#modalContent').innerHTML = html;
  $('#adminModal').classList.add('open');
  $('#adminModal').setAttribute('aria-hidden', 'false');
}

function closeModal() {
  if (pixPollTimer) { clearInterval(pixPollTimer); pixPollTimer = null; }
  $('#adminModal').classList.remove('open');
  $('#adminModal').setAttribute('aria-hidden', 'true');
  $('#modalContent').innerHTML = '';
}

$('#modalCloseBtn').onclick = closeModal;
$('#adminModal').addEventListener('click', (event) => {
  if (event.target === $('#adminModal')) closeModal();
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    closeModal();
    setAdminSidebarOpen(false);
  }
});

$('#loginForm').onsubmit = async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const out = await api('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: form.email.value, password: form.password.value }),
    });
    sessionStorage.setItem('catalogo_token', out.access_token);
    await startAdmin();
  } catch (error) {
    showToast(error.message, 'error');
  }
};

$('#logoutBtn').onclick = () => {
  clearAuthToken();
  location.reload();
};

$('#refreshBtn').onclick = async () => {
  await loadAll();
  showToast('Painel atualizado.');
};

$('#adminSidebarToggle').onclick = () => {
  const sidebar = $('#adminSidebar');
  setAdminSidebarOpen(!sidebar?.classList.contains('mobile-open'));
};

$('#adminSidebarBackdrop').onclick = () => setAdminSidebarOpen(false);

function setAdminSidebarCollapsed(collapsed, persist = true) {
  const shell = $('#adminView');
  const button = $('#adminSidebarCollapse');
  if (!shell || !button) return;
  shell.classList.toggle('sidebar-collapsed', collapsed);
  const glyph = button.querySelector('.sidebar-collapse-glyph');
  if (glyph) glyph.textContent = collapsed ? '›' : '‹';
  button.title = collapsed ? 'Expandir menu' : 'Recolher menu';
  button.setAttribute('aria-label', button.title);
  button.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
  if (persist) localStorage.setItem('catalogo_admin_sidebar_collapsed', collapsed ? '1' : '0');
}

$('#adminSidebarCollapse')?.addEventListener('click', () => {
  if (window.matchMedia('(max-width: 980px)').matches) return;
  setAdminSidebarCollapsed(!$('#adminView')?.classList.contains('sidebar-collapsed'));
});

async function startAdmin() {
  try {
    me = await api('/api/auth/me');
    if (me.role === 'SUPER_ADMINISTRADOR') {
      location.href = 'super-admin.html';
      return;
    }

    store = await api('/api/admin/store');
    applyStoreTheme();
    $('#loginView').classList.add('hidden');
    $('#adminView').classList.remove('hidden');
    setAdminSidebarCollapsed(localStorage.getItem('catalogo_admin_sidebar_collapsed') === '1' && !window.matchMedia('(max-width: 980px)').matches, false);
    $('#sideStoreName').textContent = store.name;
    $('#sideStoreModel').textContent = store.business_model?.name || 'Negócio';
    $('#openStoreBtn').href = `loja.html?slug=${encodeURIComponent(store.slug)}`;
    buildMenu();
    renderAdminIdentity();
    await loadAll();
    renderAdminIdentity();
    renderSettings();
  } catch (error) {
    clearAuthToken();
    $('#loginView').classList.remove('hidden');
    $('#adminView').classList.add('hidden');
    if (error.message !== 'Not authenticated') showToast(error.message, 'error');
  }
}

function applyStoreTheme() {
  document.documentElement.style.setProperty('--brand', store?.primary_color || '#7C3AED');
  document.documentElement.style.setProperty('--brand2', store?.secondary_color || '#4F46E5');
  $('meta[name="theme-color"]')?.setAttribute('content', store?.primary_color || '#7C3AED');
}

function setAdminSidebarOpen(open) {
  const sidebar = $('#adminSidebar');
  const backdrop = $('#adminSidebarBackdrop');
  const toggle = $('#adminSidebarToggle');
  if (!sidebar || !backdrop || !toggle) return;
  sidebar.classList.toggle('mobile-open', open);
  backdrop.classList.toggle('open', open);
  toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
  document.body.classList.toggle('admin-sidebar-open', open);
}

function closeAdminSidebarOnMobile() {
  if (window.matchMedia('(max-width: 980px)').matches) setAdminSidebarOpen(false);
}

function buildMenu() {
  const caps = store.capabilities || {};
  const planFeatures = store.subscription?.features || {};
  const items = ['dashboard'];
  if (caps.catalog || caps.services) items.push('categories');
  if (caps.catalog) items.push('products', 'orders', 'inventory');
  if (caps.coupons && planFeatures.coupons) items.push('coupons');
  if (caps.promotions && planFeatures.promotions) items.push('promotions');
  if (caps.services) items.push('services');
  if (caps.appointments) items.push('professionals', 'appointments');
  if (caps.quotes) items.push('quotes');
  if (caps.reservations) items.push('resources', 'reservations');
  if (caps.rentals) items.push('rentalItems', 'rentals');
  if (caps.payments) items.push('payments');
  if (planFeatures.reports) items.push('reports');
  items.push('subscription', 'privacy', 'settings');

  $('#sideMenu').innerHTML = adminMenuGroups
    .map(group => {
      const groupItems = group.ids.filter(id => items.includes(id));
      if (!groupItems.length) return '';
      return `<div class="side-menu-group"><div class="side-menu-label">${escapeHtml(group.title)}</div>${groupItems.map(id => `<button class="side-btn ${id === 'dashboard' ? 'active' : ''}" data-section="${id}"><span class="side-icon">${adminIcon(id)}</span><span class="side-label">${labels[id]}</span></button>`).join('')}</div>`;
    })
    .join('');

  $$('[data-section]').forEach((button) => {
    button.onclick = () => switchSection(button.dataset.section);
  });
}

window.switchSection = function switchSection(id) {
  $$('.admin-section').forEach((section) => section.classList.remove('active'));
  const target = $(`#${id}`);
  if (!target) return;
  target.classList.add('active');
  $$('[data-section]').forEach((button) => button.classList.toggle('active', button.dataset.section === id));
  $('#adminTitle').textContent = labels[id] || id;
  const breadcrumb = $('#adminBreadcrumb');
  if (breadcrumb) breadcrumb.textContent = id === 'dashboard' ? 'Painel administrativo' : `Painel / ${labels[id] || id}`;
  const mobileSection = $('#adminMobileSection');
  if (mobileSection) mobileSection.textContent = labels[id] || id;
  closeAdminSidebarOnMobile();
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

async function loadAll() {
  const caps = store.capabilities || {};
  const planFeatures = store.subscription?.features || {};
  const jobs = [];

  if (caps.catalog || caps.services) jobs.push(loadCategories());
  if (caps.catalog) jobs.push(loadProducts(), loadOrders(), loadInventory());
  if (caps.coupons && planFeatures.coupons) jobs.push(loadCoupons());
  if (caps.promotions && planFeatures.promotions) jobs.push(loadPromotions());
  if (caps.services) jobs.push(loadServices());
  if (caps.appointments) jobs.push(loadProfessionals(), loadAppointments());
  if (caps.quotes) jobs.push(loadQuotes());
  if (caps.reservations) jobs.push(loadResources(), loadReservations());
  if (caps.rentals) jobs.push(loadRentalItems(), loadRentals());
  if (caps.payments) jobs.push(loadPayments(), loadPaymentSettings());
  if (planFeatures.reports) jobs.push(loadReports(30));
  jobs.push(loadSubscription(), loadPrivacy());

  await Promise.allSettled(jobs);
  renderStats();
}

function renderStats() {
  const caps = store.capabilities || {};
  const planFeatures = subscriptionInfo?.features || store.subscription?.features || {};
  const rows = [];

  if (caps.catalog) {
    rows.push(['Produtos ativos', products.filter((item) => item.is_active).length]);
    rows.push(['Pedidos', orders.length]);
    rows.push(['Itens em estoque', inventory.reduce((sum, item) => sum + Number(item.quantity || 0), 0)]);
  }
  if (caps.services) rows.push(['Serviços ativos', services.filter((item) => item.is_active).length]);
  if (caps.appointments) rows.push(['Agendamentos', appointments.length]);
  if (caps.quotes) rows.push(['Orçamentos', quotes.length]);
  if (caps.coupons && planFeatures.coupons) rows.push(['Cupons ativos', coupons.filter(item => item.is_active).length]);
  if (caps.promotions && planFeatures.promotions) rows.push(['Promoções ativas', promotions.filter(item => item.is_active).length]);
  if (caps.reservations) rows.push(['Reservas', reservations.length]);
  if (caps.rentals) rows.push(['Locações', rentals.length]);
  if (caps.payments) rows.push(['Pagamentos pendentes', payments.filter(item => item.status === 'PENDENTE').length]);

  const metricIds = {
    'Produtos ativos':'products','Pedidos':'orders','Itens em estoque':'inventory','Serviços ativos':'services',
    'Agendamentos':'appointments','Orçamentos':'quotes','Cupons ativos':'coupons','Promoções ativas':'promotions',
    'Reservas':'reservations','Locações':'rentals','Pagamentos pendentes':'payments'
  };
  $('#stats').innerHTML = rows.length
    ? rows.slice(0, 4).map(([label, value]) => { const metricId = metricIds[label] || 'dashboard'; return `<div class="stat-card metric-card metric-${metricId}"><span class="metric-icon">${adminIcon(metricId)}</span><span>${escapeHtml(label)}</span><strong>${value}</strong><span class="metric-note">Atualizado agora</span></div>`; }).join('')
    : '<div class="empty">Nenhuma métrica disponível ainda.</div>';

  renderDashboardAttention();
  renderAdminIdentity();

  $('#summaryContent').innerHTML = `
    <p>Você está administrando <b>${escapeHtml(store.name)}</b>.</p>
    <p>Modelo: <b>${escapeHtml(store.business_model?.name || 'Não definido')}</b> · Segmento: <b>${escapeHtml(store.business_category?.name || 'Não definido')}</b>.</p>
    <p>Plano atual: <b>${escapeHtml(subscriptionInfo?.plan?.name || store.subscription?.plan?.name || 'Gratuito')}</b>.</p>
    <p>O painel exibe apenas os módulos habilitados para esta empresa. Todas as operações administrativas continuam isoladas pelo <code>store_id</code> do usuário autenticado.</p>
  `;
}


function reportMetric(label, value, note = '') {
  return `<div class="stat-card report-stat"><span>${escapeHtml(label)}</span><strong>${value}</strong>${note ? `<small>${escapeHtml(note)}</small>` : ''}</div>`;
}

function renderDashboardReportPreview() {
  const root = $('#dashboardReportPreview');
  const content = $('#dashboardReportContent');
  if (!root || !content) return;
  if (!reportOverview || !(subscriptionInfo?.features?.reports || store?.subscription?.features?.reports)) {
    root.classList.add('hidden');
    return;
  }
  root.classList.remove('hidden');
  const o = reportOverview;
  const rows = [];
  if (store.capabilities?.catalog) rows.push(['Receita em pedidos', money(o.orders?.revenue), `${o.orders?.active_count || 0} pedidos válidos`]);
  if (store.capabilities?.appointments) rows.push(['Agendamentos', o.appointments?.count || 0, `${o.appointments?.completed || 0} concluídos`]);
  if (store.capabilities?.payments) rows.push(['Pagamentos confirmados', money(o.payments?.paid_total), `${o.payments?.paid_count || 0} pagamentos`]);
  rows.push(['Novos clientes', o.customers?.new || 0, 'no período']);
  content.innerHTML = `<div class="stats compact-report-stats">${rows.slice(0,4).map(([l,v,n])=>reportMetric(l,v,n)).join('')}</div>`;
}

window.loadReports = async function loadReports(forcedPeriod = null) {
  const select = $('#reportPeriod');
  const period = Number(forcedPeriod || select?.value || 30);
  if (select && forcedPeriod) select.value = String(forcedPeriod);
  try {
    const [overview, series, top] = await Promise.all([
      api(`/api/admin/reports/overview?period=${period}`),
      api(`/api/admin/reports/timeseries?period=${period}`),
      api(`/api/admin/reports/top-items?period=${period}&limit=8`),
    ]);
    reportOverview = overview;
    reportSeries = series;
    reportTopItems = top;
    renderReports();
    renderDashboardReportPreview();
  } catch (error) {
    if (forcedPeriod) return;
    showToast(error.message, 'error');
  }
};

function renderReports() {
  if (!reportOverview) return;
  const o = reportOverview;
  const metrics = [];
  if (store.capabilities?.catalog) {
    metrics.push(['Receita em pedidos', money(o.orders.revenue), `Ticket médio ${money(o.orders.average_ticket)}`]);
    metrics.push(['Pedidos', o.orders.count, `${o.orders.pending} pendentes`]);
  }
  if (store.capabilities?.appointments) metrics.push(['Agendamentos', o.appointments.count, `${o.appointments.completed} concluídos`]);
  if (store.capabilities?.quotes) metrics.push(['Orçamentos', o.quotes.count, `${o.quotes.approved} aprovados/concluídos`]);
  if (store.capabilities?.reservations) metrics.push(['Reservas', o.reservations.count, `Valor ${money(o.reservations.revenue)}`]);
  if (store.capabilities?.rentals) metrics.push(['Locações', o.rentals.count, `Valor ${money(o.rentals.revenue)}`]);
  if (store.capabilities?.payments) metrics.push(['Recebido', money(o.payments.paid_total), `${o.payments.paid_count} pagamentos`]);
  metrics.push(['Novos clientes', o.customers.new, `${o.period_days} dias`]);
  if (store.capabilities?.catalog) metrics.push(['Estoque baixo', o.inventory.low_stock_count, 'itens no mínimo ou abaixo']);
  $('#reportStats').innerHTML = metrics.slice(0,8).map(([l,v,n])=>reportMetric(l,v,n)).join('');

  const visibleSeries = reportSeries.length > 60 ? reportSeries.filter((_,i)=> i % Math.ceil(reportSeries.length/60)===0 || i===reportSeries.length-1) : reportSeries;
  const maxRevenue = Math.max(1, ...visibleSeries.map(r => Number(r.order_revenue || r.paid_total || 0)));
  const maxActivity = Math.max(1, ...visibleSeries.map(r => Number(r.orders || 0) + Number(r.appointments || 0)));
  $('#reportChart').innerHTML = visibleSeries.length ? `<div class="report-chart">${visibleSeries.map(row => {
    const revenue = Number(row.order_revenue || 0);
    const activity = Number(row.orders || 0) + Number(row.appointments || 0);
    const revenueHeight = Math.max(revenue ? 6 : 1, Math.round((revenue/maxRevenue)*100));
    const activityHeight = Math.max(activity ? 6 : 1, Math.round((activity/maxActivity)*100));
    const label = new Date(`${row.date}T12:00:00`).toLocaleDateString('pt-BR',{day:'2-digit',month:'2-digit'});
    return `<div class="chart-day" title="${label} · ${row.orders} pedidos · ${row.appointments} agendamentos · ${money(revenue)}">
      <div class="chart-bars"><i class="bar revenue" style="height:${revenueHeight}%"></i><i class="bar activity" style="height:${activityHeight}%"></i></div>
      <small>${label}</small></div>`;
  }).join('')}</div><div class="chart-legend"><span><i class="legend-dot revenue"></i> Receita de pedidos</span><span><i class="legend-dot activity"></i> Pedidos + agendamentos</span></div>` : '<div class="empty">Sem dados no período.</div>';

  const products = reportTopItems?.products || [];
  const servicesTop = reportTopItems?.services || [];
  $('#reportTopItems').innerHTML = `<div class="top-report-columns">
    <div><h4>Produtos</h4>${products.length ? `<ol class="rank-list">${products.map(p=>`<li><span>${escapeHtml(p.name)}</span><b>${p.quantity} un. · ${money(p.revenue)}</b></li>`).join('')}</ol>` : '<div class="empty small-empty">Sem vendas.</div>'}</div>
    <div><h4>Serviços</h4>${servicesTop.length ? `<ol class="rank-list">${servicesTop.map(p=>`<li><span>${escapeHtml(p.name)}</span><b>${p.count} agend.</b></li>`).join('')}</ol>` : '<div class="empty small-empty">Sem agendamentos.</div>'}</div>
  </div>`;

  const exports = [];
  if (store.capabilities?.catalog) exports.push(['Pedidos','orders']);
  exports.push(['Clientes','customers']);
  if (store.capabilities?.appointments) exports.push(['Agendamentos','appointments']);
  if (store.capabilities?.quotes) exports.push(['Orçamentos','quotes']);
  if (store.capabilities?.reservations) exports.push(['Reservas','reservations']);
  if (store.capabilities?.rentals) exports.push(['Locações','rentals']);
  if (store.capabilities?.payments) exports.push(['Pagamentos','payments']);
  $('#reportExports').innerHTML = exports.map(([label,type])=>`<button class="btn ghost report-export-btn" type="button" onclick="downloadReportCsv('${type}')">Baixar ${escapeHtml(label)} (.csv)</button>`).join('');
}

window.downloadReportCsv = async function downloadReportCsv(type) {
  const period = Number($('#reportPeriod')?.value || 30);
  const token = getAuthToken();
  try {
    const response = await fetch(`${API_BASE}/api/admin/reports/export.csv?type=${encodeURIComponent(type)}&period=${period}`, {
      headers: token ? {Authorization:`Bearer ${token}`} : {},
    });
    if (!response.ok) {
      let message = `Erro HTTP ${response.status}`;
      try { const data = await response.json(); message = data.detail || message; } catch {}
      throw new Error(message);
    }
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match?.[1] || `${type}.csv`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    showToast('Relatório exportado.');
  } catch (error) { showToast(error.message, 'error'); }
};

window.loadSubscription = async function loadSubscription() {
  const [overview, plans] = await Promise.all([
    api('/api/admin/billing/overview'),
    api('/api/admin/billing/available-plans'),
  ]);
  billingOverview = overview;
  availableBillingPlans = plans || [];
  subscriptionInfo = billingOverview?.subscription || null;
  renderSubscription();
  renderDashboardReportPreview();
};

function usageCard(label, key) {
  const used = Number(subscriptionInfo?.usage?.[key] || 0);
  const raw = subscriptionInfo?.limits?.[key];
  const unlimited = raw === undefined || raw === null || Number(raw) < 0;
  const limit = unlimited ? null : Number(raw);
  const percent = unlimited || !limit ? 0 : Math.min(100, Math.round((used / limit) * 100));
  return `<div class="usage-card"><div class="usage-head"><span>${escapeHtml(label)}</span><b>${used} / ${unlimited ? '∞' : limit}</b></div><div class="usage-bar"><i style="width:${percent}%"></i></div></div>`;
}

function formatBillingDate(value, fallback = '—') {
  if (!value) return fallback;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return fallback;
  return date.toLocaleDateString('pt-BR');
}

function billingStatusLabel(value) {
  return ({
    ACTIVE:'Ativa', TRIAL:'Período de teste', PAST_DUE:'Pagamento em atraso', EXPIRED:'Expirada', CANCELED:'Cancelada',
    PENDING:'Pendente', PAID:'Pago', FAILED:'Falhou'
  })[String(value || '').toUpperCase()] || String(value || '—');
}

function billingStatusClass(value) {
  const status = String(value || '').toUpperCase();
  if (['ACTIVE','PAID'].includes(status)) return 'CONFIRMADO';
  if (['PAST_DUE','FAILED'].includes(status)) return 'PENDENTE';
  if (['CANCELED','EXPIRED'].includes(status)) return 'CANCELADO';
  return 'PENDENTE';
}

function billingProviderLabel(value) {
  const code = String(value || 'MANUAL').toUpperCase();
  const provider = billingOverview?.providers?.find(item => item.code === code);
  return provider?.display_name || ({MANUAL:'Controle manual'})[code] || code.replaceAll('_',' ');
}

function billingCycleLabel(value) {
  return String(value || 'MONTHLY').toUpperCase() === 'YEARLY' ? 'Anual' : 'Mensal';
}

const billingFeatureLabels = {
  coupons: 'Cupons',
  promotions: 'Promoções',
  custom_branding: 'Personalização visual',
  reports: 'Relatórios',
  priority_support: 'Suporte prioritário',
  custom_domain: 'Domínio personalizado',
  online_payments: 'Pagamentos online',
};

function subscriptionHeroHtml({ plan, sub, cycle, price, paymentMethod }) {
  return `<div class="billing-admin-hero">
    <div class="billing-plan-card">
      <div class="billing-plan-top"><span class="eyebrow">PLANO ATUAL</span><span class="status ${billingStatusClass(sub?.status || 'ACTIVE')}">${escapeHtml(billingStatusLabel(sub?.status || 'ACTIVE'))}</span></div>
      <h3>${escapeHtml(plan.name)}</h3>
      <div class="plan-price">${money(price)}<small>/${cycle === 'YEARLY' ? 'ano' : 'mês'}</small></div>
      <p>${escapeHtml(plan.description || 'Plano da sua loja no Catálogo Digital.')}</p>
      <div class="billing-meta-grid">
        <div><span>Ciclo</span><b>${escapeHtml(billingCycleLabel(cycle))}</b></div>
        <div><span>Próxima cobrança</span><b>${formatBillingDate(sub?.next_billing_at || sub?.current_period_end)}</b></div>
        <div><span>Cobrança</span><b>${escapeHtml(billingProviderLabel(sub?.provider))}</b></div>
        <div><span>Forma de pagamento</span><b>${escapeHtml(paymentMethod)}</b></div>
      </div>
    </div>
    <div class="plan-usage billing-usage-card">
      <div class="billing-card-title"><div><span class="eyebrow">CAPACIDADE</span><h3>Uso do plano</h3></div><small>Atualizado agora</small></div>
      ${usageCard('Produtos','products')}
      ${usageCard('Serviços','services')}
      ${usageCard('Profissionais','professionals')}
    </div>
  </div>`;
}

function subscriptionFeaturesHtml(features, pixReady) {
  const chips = Object.entries(billingFeatureLabels)
    .map(([key, label]) => `<span class="feature-chip ${features[key] ? 'enabled' : 'disabled'}">${features[key] ? '✓' : '—'} ${escapeHtml(label)}</span>`)
    .join('');
  const help = pixReady
    ? 'A confirmação do Mercado Pago ativa o plano automaticamente.'
    : 'O Pix aparecerá assim que as credenciais do Mercado Pago forem configuradas com segurança.';

  return `<div class="panel-soft billing-feature-panel">
      <div class="billing-card-title"><div><span class="eyebrow">RECURSOS</span><h3>O que está incluído</h3></div></div>
      <div class="feature-chips">${chips}</div>
      <p class="section-copy billing-help-copy">Você pode escolher outro plano, aplicar cupom e pagar por Pix. ${help}</p>
    </div>`;
}

function subscriptionSummaryHtml(sub, invoices, policy) {
  return `<div class="panel-soft billing-summary-panel">
      <div class="billing-card-title"><div><span class="eyebrow">COBRANÇA</span><h3>Resumo financeiro</h3></div></div>
      <div class="billing-summary-list">
        <div><span>Período atual</span><b>${formatBillingDate(sub?.current_period_start)} → ${formatBillingDate(sub?.current_period_end)}</b></div>
        <div><span>Tolerância após vencimento</span><b>${Number(policy.grace_days ?? 0)} dias</b></div>
        <div><span>Faturas recentes</span><b>${invoices.length}</b></div>
        <div><span>Renovação automática</span><b>${sub?.auto_renew ? 'Ativada' : 'Ainda não ativada'}</b></div>
      </div>
    </div>`;
}

function planChoiceCardHtml(candidate, currentPlan, sub, cycle, invoices, pixReady) {
  const isCurrent = Number(candidate.id) === Number(currentPlan.id);
  const featureCount = Object.values(candidate.features || {}).filter(Boolean).length;
  const hasPendingRenewal = isCurrent && invoices.some(invoice => invoice.invoice_type === 'RENEWAL' && ['PENDING','FAILED'].includes(String(invoice.status || '').toUpperCase()));
  const isTrialCurrent = isCurrent && String(sub?.status || '').toUpperCase() === 'TRIAL';
  const canChangeCurrentCycle = isCurrent && candidate.yearly_price != null && cycle !== 'YEARLY';
  const buttonEnabled = pixReady && (!isCurrent || canChangeCurrentCycle || hasPendingRenewal || isTrialCurrent);
  const buttonLabel = !pixReady
    ? 'Pix em configuração'
    : hasPendingRenewal
      ? 'Pagar renovação com Pix'
      : isTrialCurrent
        ? 'Garantir plano com Pix'
        : isCurrent
          ? (canChangeCurrentCycle ? 'Mudar ciclo com Pix' : 'Plano atual')
          : 'Pagar com Pix';

  return `<article class="billing-choice-card ${isCurrent ? 'is-current' : ''} ${candidate.is_featured ? 'is-featured' : ''}">
        ${candidate.badge ? `<span class="billing-plan-badge">${escapeHtml(candidate.badge)}</span>` : ''}
        <div class="billing-choice-head"><div><b>${escapeHtml(candidate.name)}</b><small>${escapeHtml(candidate.description || 'Plano Catálogo Digital')}</small></div>${isCurrent ? '<span class="status CONFIRMADO">Atual</span>' : ''}</div>
        <div class="billing-choice-price"><strong>${money(candidate.monthly_price)}</strong><span>/mês</span></div>
        <div class="billing-choice-meta"><span>${featureCount} recurso(s)</span><span>${Number(candidate.trial_days || 0)} dia(s) grátis</span><span>${candidate.yearly_price != null ? `${money(candidate.yearly_price)}/ano` : 'Mensal'}</span></div>
        <button class="btn ${isCurrent ? 'ghost' : 'primary'} small" type="button" ${buttonEnabled ? `onclick="openPlanCheckout(${candidate.id})"` : 'disabled'}>${buttonLabel}</button>
      </article>`;
}

function subscriptionPlansHtml(plan, sub, cycle, invoices, pixReady) {
  const cards = availableBillingPlans
    .map(candidate => planChoiceCardHtml(candidate, plan, sub, cycle, invoices, pixReady))
    .join('');

  return `<div class="panel-soft billing-plan-marketplace">
    <div class="billing-card-title"><div><span class="eyebrow">PLANOS</span><h3>Escolha o plano ideal</h3></div><small>Cupons promocionais podem ser aplicados antes de confirmar</small></div>
    <div class="billing-plan-choice-grid">${cards || '<div class="empty">Nenhum plano disponível.</div>'}</div>
  </div>`;
}

function subscriptionHistoryHtml(invoices, plan) {
  const rows = invoices.map(invoice => `<tr>
      <td><b>#${invoice.id}</b><br><small>${escapeHtml(invoice.invoice_type === 'PLAN_CHANGE' ? 'Troca de plano' : 'Renovação')}</small></td>
      <td>${escapeHtml(invoice.plan_name || plan.name)}</td>
      <td>${formatBillingDate(invoice.due_at || invoice.created_at)}</td>
      <td><b>${money(invoice.amount)}</b>${Number(invoice.discount_amount || 0) > 0 ? `<br><small>desconto ${money(invoice.discount_amount)}${invoice.coupon_code ? ` · ${escapeHtml(invoice.coupon_code)}` : ''}</small>` : ''}</td>
      <td>${escapeHtml(invoice.payment_method || billingProviderLabel(invoice.provider))}</td>
      <td><span class="status ${billingStatusClass(invoice.status)}">${escapeHtml(billingStatusLabel(invoice.status))}</span></td>
    </tr>`).join('');

  return `<div class="panel-soft billing-history-panel">
    <div class="billing-card-title"><div><span class="eyebrow">HISTÓRICO</span><h3>Cobranças da assinatura</h3></div><small>Últimas ${Math.min(invoices.length,20)} faturas</small></div>
    <div class="table-wrap">${invoices.length ? `<table class="table billing-table"><thead><tr><th>Fatura</th><th>Plano</th><th>Vencimento</th><th>Valor</th><th>Pagamento</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table>` : '<div class="empty small-empty">Ainda não há cobranças registradas para esta assinatura.</div>'}</div>
  </div>`;
}

function renderSubscription() {
  const root = $('#subscriptionContent');
  if (!root || !subscriptionInfo) return;

  const plan = subscriptionInfo.plan;
  if (!plan) {
    root.innerHTML = '<div class="empty">Nenhum plano configurado para esta loja.</div>';
    return;
  }

  const sub = subscriptionInfo.subscription;
  const features = subscriptionInfo.features || {};
  const invoices = billingOverview?.recent_invoices || [];
  const policy = billingOverview?.billing_policy || {};
  const cycle = sub?.billing_cycle || 'MONTHLY';
  const price = cycle === 'YEARLY' ? plan.yearly_price : plan.monthly_price;
  const latestInvoice = invoices[0] || null;
  const automaticProvider = (billingOverview?.providers || []).find(item => item.code === sub?.provider && item.configured);
  const paymentMethod = latestInvoice?.payment_method || (automaticProvider ? automaticProvider.display_name : 'Ainda não configurada');
  const pixProvider = (billingOverview?.providers || []).find(item => item.code === 'MERCADO_PAGO');
  const pixReady = Boolean(pixProvider?.available_for_checkout);

  root.innerHTML = [
    subscriptionHeroHtml({ plan, sub, cycle, price, paymentMethod }),
    `<div class="billing-two-columns">${subscriptionFeaturesHtml(features, pixReady)}${subscriptionSummaryHtml(sub, invoices, policy)}</div>`,
    subscriptionPlansHtml(plan, sub, cycle, invoices, pixReady),
    subscriptionHistoryHtml(invoices, plan),
  ].join('');
}

function billingCheckoutPreview(plan, cycle, preview = null) {
  const subtotal = preview?.subtotal_amount ?? (cycle === 'YEARLY' ? plan.yearly_price : plan.monthly_price);
  const discount = Number(preview?.discount_amount || 0);
  const total = preview?.amount ?? subtotal;
  return `<div class="billing-checkout-preview">
    <div><span>Plano</span><b>${escapeHtml(plan.name)}</b></div>
    <div><span>Valor do ciclo</span><b>${money(subtotal)}</b></div>
    <div><span>Desconto</span><b>${discount > 0 ? `- ${money(discount)}` : money(0)}</b></div>
    <div class="billing-checkout-total"><span>Total</span><strong>${money(total)}</strong></div>
    ${preview?.coupon ? `<div class="billing-coupon-applied">✓ Cupom ${escapeHtml(preview.coupon.code)} aplicado${preview.coupon.duration === 'RECURRING' ? ' às cobranças recorrentes enquanto estiver válido' : ' nesta cobrança'}</div>` : ''}
  </div>`;
}

function pixStatusLabel(status) {
  const value = String(status || 'PENDING').toUpperCase();
  return ({PENDING:'Aguardando pagamento',PAID:'Pagamento confirmado',FAILED:'Pagamento recusado',CANCELED:'Pagamento cancelado'})[value] || value;
}

function renderPixCheckout(invoice) {
  if (!invoice) return;
  const paid = String(invoice.status || '').toUpperCase() === 'PAID';
  const failed = ['FAILED','CANCELED'].includes(String(invoice.status || '').toUpperCase());
  const qrImage = invoice.pix_qr_code_base64 ? `<img class="billing-pix-qr" src="data:image/png;base64,${escapeHtml(invoice.pix_qr_code_base64)}" alt="QR Code Pix">` : '';
  openModal(paid ? 'Pagamento confirmado' : 'Pague com Pix', 'Assinatura', `<div class="billing-pix-shell ${paid ? 'is-paid' : failed ? 'is-failed' : ''}">
    <div class="billing-pix-status"><span class="billing-pix-status-icon">${paid ? '✓' : failed ? '!' : 'PIX'}</span><div><span class="eyebrow">${paid ? 'TUDO CERTO' : 'PAGAMENTO SEGURO'}</span><h3>${escapeHtml(pixStatusLabel(invoice.status))}</h3><p>${paid ? 'Seu plano foi atualizado automaticamente.' : failed ? 'Você pode fechar e gerar um novo Pix.' : 'Abra seu banco, escaneie o QR Code ou use o código Copia e Cola.'}</p></div></div>
    ${!paid && !failed ? `<div class="billing-pix-content">${qrImage}<div class="billing-pix-payment-data"><div class="billing-pix-value"><span>Valor</span><strong>${money(invoice.amount)}</strong></div>${invoice.pix_qr_code ? `<label>Código Pix Copia e Cola</label><div class="billing-pix-copy"><textarea class="textarea" id="pixCopyCode" readonly>${escapeHtml(invoice.pix_qr_code)}</textarea><button class="btn primary" type="button" id="copyPixCodeBtn">Copiar Pix</button></div>` : '<div class="notice">QR Code em processamento. Aguarde alguns segundos.</div>'}<small>A confirmação é automática. Esta tela verifica o pagamento enquanto estiver aberta.</small></div></div>` : ''}
    ${paid ? '<div class="billing-pix-success-card"><b>Assinatura liberada</b><span>Você já pode continuar usando os recursos do plano.</span></div>' : ''}
    <div class="form-actions"><button class="btn ${paid ? 'primary' : 'ghost'}" type="button" onclick="closeModal()">${paid ? 'Continuar' : 'Fechar'}</button></div>
  </div>`);
  const copyBtn = $('#copyPixCodeBtn');
  if (copyBtn) copyBtn.onclick = async () => {
    try { await navigator.clipboard.writeText(invoice.pix_qr_code || ''); showToast('Código Pix copiado.'); }
    catch (_) { const field=$('#pixCopyCode'); field?.select(); document.execCommand('copy'); showToast('Código Pix copiado.'); }
  };
}

function startPixPolling(invoiceId) {
  if (pixPollTimer) clearInterval(pixPollTimer);
  pixPollTimer = setInterval(async () => {
    if (!$('#adminModal')?.classList.contains('open')) { clearInterval(pixPollTimer); pixPollTimer = null; return; }
    try {
      const result = await api(`/api/admin/billing/pix/invoices/${invoiceId}`);
      const invoice = result?.invoice;
      if (!invoice) return;
      const status = String(invoice.status || '').toUpperCase();
      if (status === 'PAID' || status === 'FAILED' || status === 'CANCELED') {
        clearInterval(pixPollTimer); pixPollTimer = null;
        renderPixCheckout(invoice);
        await loadSubscription();
        if (status === 'PAID') showToast('Pix confirmado e plano atualizado.');
      }
    } catch (_) { /* mantém a tela; o webhook continua independente */ }
  }, 5000);
}

window.openPlanCheckout = function openPlanCheckout(planId) {
  const plan = availableBillingPlans.find(item => Number(item.id) === Number(planId));
  if (!plan) return showToast('Plano não encontrado.', 'error');
  const pixReady = Boolean((billingOverview?.providers || []).find(item => item.code === 'MERCADO_PAGO')?.available_for_checkout);
  if (!pixReady) return showToast('O Pix do Mercado Pago ainda está sendo configurado.', 'error');
  openModal('Pagar plano com Pix', 'Assinatura', `<form id="planCheckoutForm" class="form-grid modal-form">
    <div class="field full"><div class="billing-checkout-plan-title"><span class="eyebrow">${escapeHtml(plan.badge || plan.code || 'PLANO')}</span><h3>${escapeHtml(plan.name)}</h3><p>${escapeHtml(plan.description || 'Plano Catálogo Digital')}</p></div></div>
    <div class="field"><label>Ciclo de cobrança</label><select class="select" name="billing_cycle"><option value="MONTHLY">Mensal — ${money(plan.monthly_price)}</option>${plan.yearly_price != null ? `<option value="YEARLY">Anual — ${money(plan.yearly_price)}</option>` : ''}</select></div>
    <div class="field"><label>Cupom de desconto</label><div class="billing-coupon-input"><input class="input" name="coupon_code" maxlength="40" placeholder="Ex.: PROFISSIONAL20"><button class="btn ghost small" type="button" id="applyBillingCouponBtn">Aplicar</button></div></div>
    <div class="field"><label>E-mail do pagador</label><input class="input" name="payer_email" type="email" required value="${escapeHtml(me?.email || '')}" autocomplete="email"></div>
    <div class="field"><label>CPF ou CNPJ do pagador</label><input class="input" name="payer_document" inputmode="numeric" maxlength="18" required placeholder="Somente números"></div>
    <div id="billingCheckoutPreview" class="field full">${billingCheckoutPreview(plan, 'MONTHLY')}</div>
    <div class="field full notice">O Mercado Pago gera um QR Code e um Pix Copia e Cola. Assim que o pagamento for aprovado, o plano é ativado automaticamente.</div>
    <div class="field full form-actions"><button type="button" class="btn ghost" onclick="closeModal()">Cancelar</button><button class="btn primary" type="submit">Gerar Pix agora</button></div>
  </form>`);
  const form = $('#planCheckoutForm');
  let appliedPreview = null;
  const updateBase = () => { appliedPreview = null; $('#billingCheckoutPreview').innerHTML = billingCheckoutPreview(plan, form.billing_cycle.value); };
  form.billing_cycle.onchange = updateBase;
  $('#applyBillingCouponBtn').onclick = async () => {
    const code = form.coupon_code.value.trim();
    if (!code) return showToast('Digite o código do cupom.', 'error');
    try {
      appliedPreview = await api('/api/admin/billing/validate-coupon', {method:'POST', body:JSON.stringify({plan_id:plan.id,billing_cycle:form.billing_cycle.value,coupon_code:code})});
      $('#billingCheckoutPreview').innerHTML = billingCheckoutPreview(plan, form.billing_cycle.value, appliedPreview);
      showToast('Cupom aplicado.');
    } catch (error) { appliedPreview = null; $('#billingCheckoutPreview').innerHTML = billingCheckoutPreview(plan, form.billing_cycle.value); showToast(error.message, 'error'); }
  };
  form.onsubmit = async event => {
    event.preventDefault();
    const submit = form.querySelector('[type="submit"]');
    if (submit) { submit.disabled = true; submit.textContent = 'Gerando Pix...'; }
    try {
      const result = await api('/api/admin/billing/pix/checkout', {method:'POST', body:JSON.stringify({
        plan_id:plan.id,
        billing_cycle:form.billing_cycle.value,
        coupon_code:form.coupon_code.value.trim() || null,
        payer_email:form.payer_email.value.trim(),
        payer_document:form.payer_document.value.replace(/\D/g,''),
      })});
      renderPixCheckout(result.invoice);
      if (String(result.invoice?.status || '').toUpperCase() === 'PENDING') startPixPolling(result.invoice.id);
      else await loadSubscription();
    } catch (error) { showToast(error.message, 'error'); if (submit) { submit.disabled = false; submit.textContent = 'Gerar Pix agora'; } }
  };
};

window.loadCategories = async function loadCategories() {
  categories = await api('/api/admin/categories');
  renderCategories();
};

function renderCategories() {
  $('#categoriesTable').innerHTML = categories.length
    ? `<table class="table"><thead><tr><th>Categoria</th><th>Ordem</th><th>Status</th><th>Ações</th></tr></thead><tbody>${categories.map((category) => `
      <tr>
        <td><b>${escapeHtml(category.name)}</b><br><small>${escapeHtml(category.description || category.slug || '')}</small></td>
        <td>${category.sort_order ?? 0}</td>
        <td><span class="status ${category.is_active ? 'CONFIRMADO' : 'CANCELADO'}">${category.is_active ? 'Ativa' : 'Inativa'}</span></td>
        <td><div class="row-actions">
          <button class="btn ghost small" onclick="openCategoryModal(${category.id})">Editar</button>
          <button class="btn ${category.is_active ? 'danger' : 'ghost'} small" onclick="toggleCategory(${category.id})">${category.is_active ? 'Desativar' : 'Ativar'}</button>
        </div></td>
      </tr>`).join('')}</tbody></table>`
    : '<div class="empty">Nenhuma categoria cadastrada.</div>';
}

window.openCategoryModal = function openCategoryModal(id = null) {
  const item = id ? categories.find((category) => category.id === id) : null;
  openModal(item ? 'Editar categoria' : 'Nova categoria', 'Categorias', `
    <form id="categoryForm" class="form-grid modal-form">
      <div class="field full"><label>Nome</label><input class="input" name="name" required value="${escapeHtml(item?.name || '')}"></div>
      <div class="field"><label>Ordem</label><input class="input" name="sort_order" type="number" value="${item?.sort_order ?? 0}"></div>
      <div class="field"><label>Status</label><select class="select" name="is_active"><option value="true" ${optionSelected(item?.is_active ?? true, true)}>Ativa</option><option value="false" ${optionSelected(item?.is_active, false)}>Inativa</option></select></div>
      <div class="field full"><label>Descrição</label><textarea class="textarea" name="description" rows="3">${escapeHtml(item?.description || '')}</textarea></div>
      ${imageUploadField('image_url', 'Imagem da categoria', 'category', item?.image_url || '')}
      <div class="field full form-actions"><button type="button" class="btn ghost" onclick="closeModal()">Cancelar</button><button class="btn primary" type="submit">${item ? 'Salvar alterações' : 'Criar categoria'}</button></div>
    </form>`);

  wireImageUploads($('#categoryForm'));

  $('#categoryForm').onsubmit = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = {
      name: form.name.value,
      description: nullable(form.description.value),
      image_url: nullable(form.image_url.value),
      sort_order: Number(form.sort_order.value || 0),
    };
    if (item) payload.is_active = form.is_active.value === 'true';

    try {
      await api(item ? `/api/admin/categories/${item.id}` : '/api/admin/categories', {
        method: item ? 'PUT' : 'POST',
        body: JSON.stringify(payload),
      });
      closeModal();
      showToast(item ? 'Categoria atualizada.' : 'Categoria criada.');
      await loadCategories();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };
};

window.toggleCategory = async function toggleCategory(id) {
  const item = categories.find((category) => category.id === id);
  if (!item) return;
  try {
    if (item.is_active) {
      await api(`/api/admin/categories/${id}`, { method: 'DELETE' });
    } else {
      await api(`/api/admin/categories/${id}`, { method: 'PUT', body: JSON.stringify({ is_active: true }) });
    }
    await loadCategories();
    showToast(item.is_active ? 'Categoria desativada.' : 'Categoria ativada.');
  } catch (error) {
    showToast(error.message, 'error');
  }
};

window.loadProducts = async function loadProducts() {
  products = await api('/api/admin/products');
  renderProducts();
  renderStats();
};

function renderProducts() {
  const term = ($('#productSearch')?.value || '').trim().toLowerCase();
  const visible = products.filter((product) => !term || [product.name, product.sku, product.description].some((value) => String(value || '').toLowerCase().includes(term)));

  $('#productsTable').innerHTML = visible.length
    ? `<table class="table"><thead><tr><th>Produto</th><th>Categoria</th><th>Preço</th><th>Estoque</th><th>Status</th><th>Ações</th></tr></thead><tbody>${visible.map((product) => `
      <tr>
        <td><b>${escapeHtml(product.name)}</b><br><small>${escapeHtml(product.sku || product.description || 'Sem SKU')}</small></td>
        <td>${escapeHtml(categoryName(product.category_id))}</td>
        <td>${money(product.price)}${product.compare_at_price ? `<br><small class="strike">${money(product.compare_at_price)}</small>` : ''}</td>
        <td>${product.track_inventory ? (product.inventory?.quantity ?? 'Variantes') : 'Não controla'}</td>
        <td><span class="status ${product.is_active ? 'CONFIRMADO' : 'CANCELADO'}">${product.is_active ? 'Ativo' : 'Inativo'}</span></td>
        <td><div class="row-actions product-action-grid">
          <button class="btn ghost small product-action" onclick="openProductModal(${product.id})"><span>${adminIcon('settings')}</span>Editar</button>
          <button class="btn ghost small product-action" onclick="openCouponModal(null, ${product.id})"><span>${adminIcon('coupons')}</span>Cupom</button>
          <button class="btn ghost small product-action" onclick="openProductExtrasModal(${product.id})"><span>${adminIcon('products')}</span>Variações</button>
          ${product.inventory ? `<button class="btn ghost small product-action" onclick="openInventoryModal(${product.inventory.id})"><span>${adminIcon('inventory')}</span>Estoque</button>` : ''}
          <button class="btn small product-action product-action-status ${product.is_active ? 'is-deactivate' : 'is-activate'}" onclick="toggleProduct(${product.id})"><span>${adminIcon(product.is_active ? 'privacy' : 'dashboard')}</span>${product.is_active ? 'Desativar' : 'Ativar'}</button>
        </div></td>
      </tr>`).join('')}</tbody></table>`
    : '<div class="empty">Nenhum produto encontrado.</div>';
}

$('#productSearch').addEventListener('input', renderProducts);

window.openProductModal = function openProductModal(id = null) {
  const item = id ? products.find((product) => product.id === id) : null;
  const categoryOptions = ['<option value="">Sem categoria</option>', ...categories.filter((category) => category.is_active || category.id === item?.category_id).map((category) => `<option value="${category.id}" ${optionSelected(category.id, item?.category_id)}>${escapeHtml(category.name)}</option>`)].join('');

  openModal(item ? 'Editar produto' : 'Novo produto', 'Catálogo', `
    <form id="productForm" class="form-grid modal-form">
      <div class="field full"><label>Nome</label><input class="input" name="name" required value="${escapeHtml(item?.name || '')}"></div>
      <div class="field"><label>Categoria</label><select class="select" name="category_id">${categoryOptions}</select></div>
      <div class="field"><label>SKU</label><input class="input" name="sku" value="${escapeHtml(item?.sku || '')}"></div>
      <div class="field"><label>Preço</label><input class="input" name="price" type="number" min="0" step="0.01" required value="${item?.price ?? ''}"></div>
      <div class="field"><label>Preço anterior (opcional)</label><input class="input" name="compare_at_price" type="number" min="0" step="0.01" value="${item?.compare_at_price ?? ''}"></div>
      <div class="field full"><label>Descrição</label><textarea class="textarea" name="description" rows="3">${escapeHtml(item?.description || '')}</textarea></div>
      ${imageUploadField('image_url', 'Imagem do produto', 'product', item?.image_url || '')}
      <div class="field checkbox-field"><label><input type="checkbox" name="track_inventory" ${checked(item?.track_inventory ?? true)}> Controlar estoque</label></div>
      ${item ? `<div class="field checkbox-field"><label><input type="checkbox" name="is_active" ${checked(item.is_active)}> Produto ativo</label></div>` : '<div></div>'}
      ${!item ? `<div class="field"><label>Estoque inicial</label><input class="input" name="initial_stock" type="number" min="0" value="0"></div><div class="field"><label>Estoque mínimo</label><input class="input" name="min_stock" type="number" min="0" value="0"></div>` : ''}
      <div class="field full form-actions"><button type="button" class="btn ghost" onclick="closeModal()">Cancelar</button><button class="btn primary" type="submit">${item ? 'Salvar alterações' : 'Criar produto'}</button></div>
    </form>`);

  wireImageUploads($('#productForm'));

  $('#productForm').onsubmit = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = {
      name: form.name.value,
      category_id: form.category_id.value ? Number(form.category_id.value) : null,
      sku: nullable(form.sku.value),
      price: Number(form.price.value),
      compare_at_price: form.compare_at_price.value === '' ? null : Number(form.compare_at_price.value),
      description: nullable(form.description.value),
      image_url: nullable(form.image_url.value),
      track_inventory: form.track_inventory.checked,
    };
    if (item) payload.is_active = form.is_active.checked;
    else {
      payload.slug = null;
      payload.initial_stock = Number(form.initial_stock.value || 0);
      payload.min_stock = Number(form.min_stock.value || 0);
    }

    try {
      await api(item ? `/api/admin/products/${item.id}` : '/api/admin/products', {
        method: item ? 'PUT' : 'POST',
        body: JSON.stringify(payload),
      });
      closeModal();
      showToast(item ? 'Produto atualizado.' : 'Produto criado.');
      await Promise.all([loadProducts(), loadInventory()]);
    } catch (error) {
      showToast(error.message, 'error');
    }
  };
};

window.toggleProduct = async function toggleProduct(id) {
  const item = products.find((product) => product.id === id);
  if (!item) return;
  try {
    if (item.is_active) await api(`/api/admin/products/${id}`, { method: 'DELETE' });
    else await api(`/api/admin/products/${id}`, { method: 'PUT', body: JSON.stringify({ is_active: true }) });
    await loadProducts();
    showToast(item.is_active ? 'Produto desativado.' : 'Produto ativado.');
  } catch (error) {
    showToast(error.message, 'error');
  }
};

window.openProductExtrasModal = function openProductExtrasModal(id) {
  const product = products.find((row) => row.id === id);
  if (!product) return;
  const variantsHtml = (product.variants || []).map(v => `<div class="mini-row"><span><b>${escapeHtml(v.name)}</b> · ${money(v.price ?? product.price)}${v.sku ? ` · ${escapeHtml(v.sku)}` : ''}</span><span>${v.inventory ? `Estoque ${v.inventory.quantity}` : ''}</span></div>`).join('') || '<div class="empty">Sem variantes.</div>';
  const optionsHtml = (product.options || []).map(o => `<div class="mini-row"><span><b>${escapeHtml(o.name)}</b><br><small>${(o.items || []).map(i => `${escapeHtml(i.name)}${Number(i.price_adjustment) ? ` (+${money(i.price_adjustment)})` : ''}`).join(' · ')}</small></span></div>`).join('') || '<div class="empty">Sem adicionais.</div>';
  openModal('Variações e adicionais', product.name, `
    <div class="split-panel"><div><h3>Variações</h3>${variantsHtml}</div><div><h3>Adicionais</h3>${optionsHtml}</div></div>
    <hr class="soft-line">
    <form id="variantForm" class="form-grid modal-form"><div class="field full"><b>Adicionar variante</b></div><div class="field"><label>Nome</label><input class="input" name="name" required placeholder="Ex.: Grande"></div><div class="field"><label>SKU</label><input class="input" name="sku"></div><div class="field"><label>Preço opcional</label><input class="input" name="price" type="number" min="0" step="0.01"></div><div class="field"><label>Estoque inicial</label><input class="input" name="initial_stock" type="number" min="0" value="0"></div><div class="field full"><button class="btn primary small" type="submit">Adicionar variante</button></div></form>
    <hr class="soft-line">
    <form id="optionForm" class="form-grid modal-form"><div class="field full"><b>Adicionar grupo de adicionais</b></div><div class="field"><label>Nome do grupo</label><input class="input" name="name" required placeholder="Ex.: Molhos"></div><div class="field"><label>Máximo de escolhas</label><input class="input" name="max_selections" type="number" min="1" value="1"></div><div class="field checkbox-field"><label><input type="checkbox" name="required"> Obrigatório</label></div><div class="field full"><label>Itens — um por linha no formato Nome|Preço</label><textarea class="textarea" name="items" rows="4" placeholder="Bacon|3.00\nQueijo|2.00\nSem acréscimo|0"></textarea></div><div class="field full"><button class="btn primary small" type="submit">Adicionar grupo</button></div></form>`);
  $('#variantForm').onsubmit = async (event) => {
    event.preventDefault(); const f = event.currentTarget;
    try { await api(`/api/admin/products/${id}/variants`, {method:'POST', body:JSON.stringify({name:f.name.value, sku:nullable(f.sku.value), price:f.price.value === '' ? null : Number(f.price.value), sort_order:0, initial_stock:Number(f.initial_stock.value||0), min_stock:0})}); closeModal(); await Promise.all([loadProducts(), loadInventory()]); showToast('Variante adicionada.'); } catch(e){ showToast(e.message,'error'); }
  };
  $('#optionForm').onsubmit = async (event) => {
    event.preventDefault(); const f = event.currentTarget;
    const items = f.items.value.split(/\n+/).map(x=>x.trim()).filter(Boolean).map((line,index)=>{const [name,price='0']=line.split('|');return {name:name.trim(),price_adjustment:Number(price||0),sort_order:index};});
    try { await api(`/api/admin/products/${id}/options`, {method:'POST', body:JSON.stringify({name:f.name.value, required:f.required.checked, min_selections:f.required.checked?1:0, max_selections:Number(f.max_selections.value||1), sort_order:0, items})}); closeModal(); await loadProducts(); showToast('Grupo de adicionais criado.'); } catch(e){ showToast(e.message,'error'); }
  };
};

window.loadOrders = async function loadOrders() {
  orders = await api('/api/admin/orders');
  $('#ordersTable').innerHTML = orders.length
    ? `<table class="table"><thead><tr><th>Pedido</th><th>Cliente</th><th>Total</th><th>Pagamento</th><th>Status</th><th>Alterar</th></tr></thead><tbody>${orders.map((order) => `
      <tr>
        <td><b>${escapeHtml(order.order_number)}</b><br><small>${new Date(order.created_at).toLocaleString('pt-BR')}</small></td>
        <td>${escapeHtml(order.customer?.name || '—')}</td>
        <td>${money(order.total)}</td>
        <td>${order.payment ? `<span class="status ${order.payment.status}">${escapeHtml(order.payment.status)}</span><br><small>${escapeHtml(order.payment.method_label || order.payment.method)}</small>` : '<small>A combinar</small>'}</td>
        <td><span class="status ${order.status}">${escapeHtml(order.status)}</span></td>
        <td><select class="select compact-select" onchange="changeOrderStatus(${order.id},this.value)">${['PENDENTE','CONFIRMADO','EM_PREPARACAO','PRONTO','SAIU_PARA_ENTREGA','ENTREGUE','CANCELADO'].map((status) => `<option ${status === order.status ? 'selected' : ''}>${status}</option>`).join('')}</select></td>
      </tr>`).join('')}</tbody></table>`
    : '<div class="empty">Nenhum pedido.</div>';
  renderStats();
};

window.changeOrderStatus = async function changeOrderStatus(id, status) {
  try {
    await api(`/api/admin/orders/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) });
    showToast('Status do pedido atualizado.');
    await Promise.all([loadOrders(), loadInventory()]);
  } catch (error) {
    showToast(error.message, 'error');
    loadOrders();
  }
};

window.loadInventory = async function loadInventory() {
  inventory = await api('/api/admin/inventory');
  const names = Object.fromEntries(products.map((product) => [product.id, product.name]));
  $('#inventoryTable').innerHTML = inventory.length
    ? `<table class="table"><thead><tr><th>Produto</th><th>Quantidade</th><th>Mínimo</th><th>Situação</th><th>Ação</th></tr></thead><tbody>${inventory.map((item) => `
      <tr>
        <td>${escapeHtml(names[item.product_id] || `Produto #${item.product_id}`)}${item.variant_id ? `<br><small>Variante #${item.variant_id}</small>` : ''}</td>
        <td><b>${item.quantity}</b></td>
        <td>${item.min_quantity}</td>
        <td><span class="status ${item.quantity <= item.min_quantity ? 'CANCELADO' : 'CONFIRMADO'}">${item.quantity <= item.min_quantity ? 'Baixo' : 'Normal'}</span></td>
        <td><button class="btn ghost small" onclick="openInventoryModal(${item.id})">Ajustar</button></td>
      </tr>`).join('')}</tbody></table>`
    : '<div class="empty">Nenhum estoque registrado.</div>';
  renderStats();
};

window.openInventoryModal = function openInventoryModal(id) {
  const item = inventory.find((row) => row.id === id);
  if (!item) return;
  const product = products.find((row) => row.id === item.product_id);
  openModal('Ajustar estoque', product?.name || `Produto #${item.product_id}`, `
    <form id="inventoryForm" class="form-grid modal-form">
      <div class="field"><label>Quantidade atual</label><input class="input" name="quantity" type="number" min="0" required value="${item.quantity}"></div>
      <div class="field"><label>Estoque mínimo</label><input class="input" name="min_quantity" type="number" min="0" required value="${item.min_quantity}"></div>
      <div class="field full notice">Use este ajuste para correções manuais. Pedidos continuam baixando e devolvendo estoque automaticamente.</div>
      <div class="field full form-actions"><button type="button" class="btn ghost" onclick="closeModal()">Cancelar</button><button class="btn primary" type="submit">Salvar estoque</button></div>
    </form>`);

  $('#inventoryForm').onsubmit = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      await api(`/api/admin/inventory/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ quantity: Number(form.quantity.value), min_quantity: Number(form.min_quantity.value) }),
      });
      closeModal();
      showToast('Estoque atualizado.');
      await Promise.all([loadInventory(), loadProducts()]);
    } catch (error) {
      showToast(error.message, 'error');
    }
  };
};

window.loadCoupons = async function loadCoupons() {
  coupons = await api('/api/admin/coupons');
  const productNames = Object.fromEntries(products.map(product => [product.id, product.name]));
  $('#couponsTable').innerHTML = coupons.length ? `<table class="table"><thead><tr><th>Código</th><th>Desconto</th><th>Aplicação</th><th>Pedido mínimo</th><th>Validade</th><th>Usos</th><th>No site</th><th>Status</th><th>Ações</th></tr></thead><tbody>${coupons.map(c=>{
    const scopedNames=(c.product_ids||[]).map(id=>productNames[id]).filter(Boolean);
    const scopeText=scopedNames.length ? scopedNames.slice(0,2).map(escapeHtml).join(', ')+(scopedNames.length>2?` +${scopedNames.length-2}`:'') : 'Pedido inteiro';
    return `<tr><td><b>${escapeHtml(c.code)}</b><br><small>${escapeHtml(c.description||'Sem descrição')}</small></td><td>${c.discount_type==='PERCENT'?`${c.value}%`:money(c.value)}${c.max_discount?`<br><small>máx. ${money(c.max_discount)}</small>`:''}</td><td><b>${scopedNames.length?'Produtos selecionados':'Todos os produtos'}</b><br><small>${scopeText}</small></td><td>${money(c.min_order_value)}</td><td><small>${escapeHtml(couponValidityLabel(c))}</small></td><td>${c.usage_count}${c.usage_limit?` / ${c.usage_limit}`:' / ∞'}</td><td><span class="status ${c.is_public?'CONFIRMADO':'PENDENTE'}">${c.is_public?'Visível':'Oculto'}</span></td><td><span class="status ${c.is_active?'CONFIRMADO':'CANCELADO'}">${c.is_active?'Ativo':'Inativo'}</span></td><td><div class="row-actions"><button class="btn ghost small" onclick="openCouponModal(${c.id})">Editar</button><button class="btn ${c.is_active?'danger':'ghost'} small" onclick="toggleCoupon(${c.id})">${c.is_active?'Desativar':'Ativar'}</button></div></td></tr>`;
  }).join('')}</tbody></table>` : '<div class="empty">Nenhum cupom cadastrado. Você pode criar um cupom para o pedido inteiro ou apenas para produtos selecionados.</div>';
};

window.openCouponModal = function openCouponModal(id=null, preselectedProductId=null) {
  const c = id ? coupons.find(x=>x.id===id) : null;
  const initialProductIds = c ? (c.product_ids || []) : (preselectedProductId ? [Number(preselectedProductId)] : []);
  const scope = initialProductIds.length ? 'PRODUCTS' : 'ORDER';
  const productChecks = products.filter(product=>product.is_active || initialProductIds.includes(product.id)).map(product=>`<label><input type="checkbox" name="product_ids" value="${product.id}" ${initialProductIds.includes(product.id)?'checked':''}> ${escapeHtml(product.name)}${product.sku?` <small>(${escapeHtml(product.sku)})</small>`:''}</label>`).join('') || '<span class="muted-note">Cadastre produtos para usar cupons específicos.</span>';
  openModal(c?'Editar cupom':(preselectedProductId?'Novo cupom para produto':'Novo cupom'),'Marketing',`<form id="couponForm" class="form-grid modal-form">
    <div class="field"><label>Código</label><input class="input" name="code" required maxlength="40" value="${escapeHtml(c?.code||'')}" placeholder="BEMVINDO10"></div>
    <div class="field"><label>Tipo</label><select class="select" name="discount_type"><option value="PERCENT" ${optionSelected(c?.discount_type,'PERCENT')}>Percentual</option><option value="FIXED" ${optionSelected(c?.discount_type,'FIXED')}>Valor fixo</option></select></div>
    <div class="field"><label>Valor do desconto</label><input class="input" name="value" type="number" min="0" step="0.01" required value="${c?.value??10}"></div>
    <div class="field"><label>Onde o cupom vale</label><select class="select" name="scope"><option value="ORDER" ${optionSelected(scope,'ORDER')}>Pedido inteiro</option><option value="PRODUCTS" ${optionSelected(scope,'PRODUCTS')}>Produtos selecionados</option></select></div>
    <div class="field full coupon-product-scope ${scope==='PRODUCTS'?'':'hidden'}" id="couponProductScope"><label>Produtos válidos</label><div class="check-grid">${productChecks}</div><small>O desconto será calculado somente sobre os itens selecionados que estiverem no carrinho.</small></div>
    <div class="field"><label>Pedido mínimo</label><input class="input" name="min_order_value" type="number" min="0" step="0.01" value="${c?.min_order_value??0}"></div>
    <div class="field"><label>Desconto máximo</label><input class="input" name="max_discount" type="number" min="0" step="0.01" value="${c?.max_discount??''}" placeholder="Opcional"></div>
    <div class="field"><label>Limite de usos</label><input class="input" name="usage_limit" type="number" min="1" value="${c?.usage_limit??''}" placeholder="Ilimitado"></div>
    <div class="field"><label>Início da validade</label><input class="input" name="starts_at" type="datetime-local" value="${toDateTimeLocal(c?.starts_at)}"></div>
    <div class="field"><label>Fim da validade</label><input class="input" name="ends_at" type="datetime-local" value="${toDateTimeLocal(c?.ends_at)}"></div>
    <div class="field full"><label>Descrição</label><textarea class="textarea" name="description" rows="3" placeholder="Ex.: 10% de desconto nos produtos selecionados">${escapeHtml(c?.description||'')}</textarea></div>
    <div class="field checkbox-field"><label><input type="checkbox" name="is_public" ${checked(c?.is_public??false)}> Exibir este cupom no site da loja</label></div>
    <div class="field checkbox-field"><label><input type="checkbox" name="is_active" ${checked(c?.is_active??true)}> Cupom ativo</label></div>
    <div class="field full notice">Cupons por produto só dão desconto nos produtos escolhidos. O pedido mínimo continua considerando o total do carrinho.</div>
    <div class="field full form-actions"><button type="button" class="btn ghost" onclick="closeModal()">Cancelar</button><button class="btn primary" type="submit">Salvar cupom</button></div>
  </form>`);
  const form=$('#couponForm');
  const syncScope=()=>$('#couponProductScope')?.classList.toggle('hidden',form.scope.value!=='PRODUCTS');
  form.scope.onchange=syncScope; syncScope();
  form.onsubmit=async e=>{
    e.preventDefault();
    const f=e.currentTarget;
    if (f.starts_at.value && f.ends_at.value && new Date(f.ends_at.value) <= new Date(f.starts_at.value)) return showToast('A data final deve ser posterior à inicial.','error');
    const product_ids=f.scope.value==='PRODUCTS'?[...f.querySelectorAll('input[name="product_ids"]:checked')].map(input=>Number(input.value)):[];
    if(f.scope.value==='PRODUCTS'&&!product_ids.length)return showToast('Escolha pelo menos um produto para este cupom.','error');
    const payload={
      code:f.code.value,description:nullable(f.description.value),discount_type:f.discount_type.value,value:Number(f.value.value),
      min_order_value:Number(f.min_order_value.value||0),max_discount:f.max_discount.value===''?null:Number(f.max_discount.value),
      starts_at:f.starts_at.value?new Date(f.starts_at.value).toISOString():null,ends_at:f.ends_at.value?new Date(f.ends_at.value).toISOString():null,
      usage_limit:f.usage_limit.value===''?null:Number(f.usage_limit.value),is_active:f.is_active.checked,is_public:f.is_public.checked,product_ids
    };
    try{
      await api(c?`/api/admin/coupons/${c.id}`:'/api/admin/coupons',{method:c?'PUT':'POST',body:JSON.stringify(payload)});
      closeModal();await loadCoupons();showToast(c?'Cupom atualizado.':'Cupom criado.');
    }catch(err){showToast(err.message,'error')}
  };
};

window.toggleCoupon = async function toggleCoupon(id) {
  const c = coupons.find(item => item.id === id);
  if (!c) return;
  const payload = {
    code:c.code, description:c.description || null, discount_type:c.discount_type, value:Number(c.value),
    min_order_value:Number(c.min_order_value || 0), max_discount:c.max_discount == null ? null : Number(c.max_discount),
    starts_at:c.starts_at || null, ends_at:c.ends_at || null, usage_limit:c.usage_limit == null ? null : Number(c.usage_limit),
    is_active:!c.is_active, is_public:Boolean(c.is_public), product_ids:[...(c.product_ids || [])],
  };
  try {
    await api(`/api/admin/coupons/${id}`, {method:'PUT', body:JSON.stringify(payload)});
    await loadCoupons();
    showToast(payload.is_active ? 'Cupom ativado.' : 'Cupom desativado.');
  } catch (err) { showToast(err.message, 'error'); }
};

window.loadPromotions = async function loadPromotions() {
  promotions = await api('/api/admin/promotions');
  const names=Object.fromEntries(products.map(p=>[p.id,p.name]));
  $('#promotionsTable').innerHTML = promotions.length ? `<table class="table"><thead><tr><th>Promoção</th><th>Desconto</th><th>Produtos</th><th>Status</th><th>Ação</th></tr></thead><tbody>${promotions.map(p=>`<tr><td><b>${escapeHtml(p.name)}</b><br><small>${escapeHtml(p.description||'')}</small></td><td>${p.discount_type==='PERCENT'?`${p.value}%`:money(p.value)}</td><td>${(p.product_ids||[]).map(id=>escapeHtml(names[id]||`#${id}`)).join(', ')}</td><td><span class="status ${p.is_active?'CONFIRMADO':'CANCELADO'}">${p.is_active?'Ativa':'Inativa'}</span></td><td><button class="btn ghost small" onclick="openPromotionModal(${p.id})">Editar</button></td></tr>`).join('')}</tbody></table>` : '<div class="empty">Nenhuma promoção cadastrada.</div>';
};

window.openPromotionModal = function openPromotionModal(id=null) {
  const promo=id?promotions.find(x=>x.id===id):null;
  openModal(promo?'Editar promoção':'Nova promoção','Marketing',`<form id="promotionForm" class="form-grid modal-form"><div class="field full"><label>Nome</label><input class="input" name="name" required value="${escapeHtml(promo?.name||'')}"></div><div class="field"><label>Tipo</label><select class="select" name="discount_type"><option value="PERCENT" ${optionSelected(promo?.discount_type,'PERCENT')}>Percentual</option><option value="FIXED" ${optionSelected(promo?.discount_type,'FIXED')}>Valor fixo</option></select></div><div class="field"><label>Valor</label><input class="input" name="value" type="number" min="0" step="0.01" required value="${promo?.value??10}"></div><div class="field full"><label>Produtos</label><div class="check-grid">${products.filter(p=>p.is_active).map(p=>`<label><input type="checkbox" name="product_ids" value="${p.id}" ${(promo?.product_ids||[]).includes(p.id)?'checked':''}> ${escapeHtml(p.name)}</label>`).join('')}</div></div><div class="field full"><label>Descrição</label><textarea class="textarea" name="description">${escapeHtml(promo?.description||'')}</textarea></div><div class="field checkbox-field"><label><input type="checkbox" name="is_active" ${checked(promo?.is_active??true)}> Ativa</label></div><div class="field full form-actions"><button class="btn primary" type="submit">Salvar promoção</button></div></form>`);
  $('#promotionForm').onsubmit=async e=>{e.preventDefault();const f=e.currentTarget;const product_ids=[...f.querySelectorAll('input[name="product_ids"]:checked')].map(x=>Number(x.value));if(!product_ids.length)return showToast('Escolha pelo menos um produto.','error');const payload={name:f.name.value,description:nullable(f.description.value),discount_type:f.discount_type.value,value:Number(f.value.value),product_ids,starts_at:null,ends_at:null,is_active:f.is_active.checked};try{await api(promo?`/api/admin/promotions/${promo.id}`:'/api/admin/promotions',{method:promo?'PUT':'POST',body:JSON.stringify(payload)});closeModal();await loadPromotions();showToast('Promoção salva.');}catch(err){showToast(err.message,'error')}};
};

window.loadServices = async function loadServices() {
  services = await api('/api/admin/services');
  renderServices();
  renderStats();
};

function renderServices() {
  $('#servicesTable').innerHTML = services.length
    ? `<table class="table"><thead><tr><th>Serviço</th><th>Categoria</th><th>Preço</th><th>Duração</th><th>Status</th><th>Ações</th></tr></thead><tbody>${services.map((service) => `
      <tr>
        <td><b>${escapeHtml(service.name)}</b><br><small>${escapeHtml(service.description || '')}</small></td>
        <td>${escapeHtml(categoryName(service.category_id))}</td>
        <td>${Number(service.price) > 0 ? money(service.price) : 'Sob orçamento'}</td>
        <td>${service.duration_minutes} min</td>
        <td><span class="status ${service.is_active ? 'CONFIRMADO' : 'CANCELADO'}">${service.is_active ? 'Ativo' : 'Inativo'}</span></td>
        <td><div class="row-actions"><button class="btn ghost small" onclick="openServiceModal(${service.id})">Editar</button><button class="btn ${service.is_active ? 'danger' : 'ghost'} small" onclick="toggleService(${service.id})">${service.is_active ? 'Desativar' : 'Ativar'}</button></div></td>
      </tr>`).join('')}</tbody></table>`
    : '<div class="empty">Nenhum serviço cadastrado.</div>';
}

window.openServiceModal = function openServiceModal(id = null) {
  const item = id ? services.find((service) => service.id === id) : null;
  const categoryOptions = ['<option value="">Sem categoria</option>', ...categories.filter((category) => category.is_active || category.id === item?.category_id).map((category) => `<option value="${category.id}" ${optionSelected(category.id, item?.category_id)}>${escapeHtml(category.name)}</option>`)].join('');

  openModal(item ? 'Editar serviço' : 'Novo serviço', 'Serviços', `
    <form id="serviceForm" class="form-grid modal-form">
      <div class="field full"><label>Nome</label><input class="input" name="name" required value="${escapeHtml(item?.name || '')}"></div>
      <div class="field"><label>Categoria</label><select class="select" name="category_id">${categoryOptions}</select></div>
      <div class="field"><label>Duração (minutos)</label><input class="input" name="duration_minutes" type="number" min="5" required value="${item?.duration_minutes ?? 60}"></div>
      <div class="field"><label>Preço</label><input class="input" name="price" type="number" min="0" step="0.01" required value="${item?.price ?? 0}"></div>
      ${item ? `<div class="field checkbox-field"><label><input type="checkbox" name="is_active" ${checked(item.is_active)}> Serviço ativo</label></div>` : '<div></div>'}
      <div class="field full"><label>Descrição</label><textarea class="textarea" name="description" rows="3">${escapeHtml(item?.description || '')}</textarea></div>
      ${imageUploadField('image_url', 'Imagem do serviço', 'service', item?.image_url || '')}
      <div class="field full form-actions"><button type="button" class="btn ghost" onclick="closeModal()">Cancelar</button><button class="btn primary" type="submit">${item ? 'Salvar alterações' : 'Criar serviço'}</button></div>
    </form>`);

  wireImageUploads($('#serviceForm'));

  $('#serviceForm').onsubmit = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = {
      name: form.name.value,
      category_id: form.category_id.value ? Number(form.category_id.value) : null,
      price: Number(form.price.value),
      duration_minutes: Number(form.duration_minutes.value),
      description: nullable(form.description.value),
      image_url: nullable(form.image_url.value),
    };
    if (!item) payload.slug = null;
    else payload.is_active = form.is_active.checked;

    try {
      await api(item ? `/api/admin/services/${item.id}` : '/api/admin/services', {
        method: item ? 'PUT' : 'POST',
        body: JSON.stringify(payload),
      });
      closeModal();
      showToast(item ? 'Serviço atualizado.' : 'Serviço criado.');
      await loadServices();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };
};

window.toggleService = async function toggleService(id) {
  const item = services.find((service) => service.id === id);
  if (!item) return;
  try {
    if (item.is_active) await api(`/api/admin/services/${id}`, { method: 'DELETE' });
    else await api(`/api/admin/services/${id}`, { method: 'PUT', body: JSON.stringify({ is_active: true }) });
    await loadServices();
    showToast(item.is_active ? 'Serviço desativado.' : 'Serviço ativado.');
  } catch (error) {
    showToast(error.message, 'error');
  }
};

window.loadProfessionals = async function loadProfessionals() {
  professionals = await api('/api/admin/professionals');
  renderProfessionals();
};

function renderProfessionals() {
  $('#professionalsTable').innerHTML = professionals.length
    ? `<table class="table"><thead><tr><th>Profissional</th><th>Serviços</th><th>Agenda</th><th>Status</th><th>Ações</th></tr></thead><tbody>${professionals.map((professional) => `
      <tr>
        <td><b>${escapeHtml(professional.name)}</b><br><small>${escapeHtml(professional.email || professional.phone || '')}</small></td>
        <td>${professional.service_ids.length} serviço(s)</td>
        <td>${professional.hours.filter((hour) => hour.is_active).length} dia(s)</td>
        <td><span class="status ${professional.is_active ? 'CONFIRMADO' : 'CANCELADO'}">${professional.is_active ? 'Ativo' : 'Inativo'}</span></td>
        <td><div class="row-actions"><button class="btn ghost small" onclick="openProfessionalModal(${professional.id})">Editar</button><button class="btn ${professional.is_active ? 'danger' : 'ghost'} small" onclick="toggleProfessional(${professional.id})">${professional.is_active ? 'Desativar' : 'Ativar'}</button></div></td>
      </tr>`).join('')}</tbody></table>`
    : '<div class="empty">Nenhum profissional cadastrado.</div>';
}

function hoursEditor(professional) {
  const current = Object.fromEntries((professional?.hours || []).map((hour) => [hour.day_of_week, hour]));
  return weekdayLabels.map((label, day) => {
    const hour = current[day];
    return `<div class="hours-row">
      <label class="hours-day"><input type="checkbox" name="day_${day}" ${checked(hour?.is_active)}> ${label}</label>
      <input class="input" type="time" name="start_${day}" value="${hour?.start_time || '09:00'}">
      <span>até</span>
      <input class="input" type="time" name="end_${day}" value="${hour?.end_time || '18:00'}">
    </div>`;
  }).join('');
}

window.openProfessionalModal = function openProfessionalModal(id = null) {
  const item = id ? professionals.find((professional) => professional.id === id) : null;
  const serviceChecks = services.filter((service) => service.is_active || item?.service_ids.includes(service.id)).map((service) => `
    <label class="check-card"><input type="checkbox" name="service_ids" value="${service.id}" ${checked(item?.service_ids.includes(service.id))}><span><b>${escapeHtml(service.name)}</b><small>${money(service.price)} · ${service.duration_minutes} min</small></span></label>`).join('') || '<div class="empty">Cadastre serviços antes de vincular profissionais.</div>';

  openModal(item ? 'Editar profissional' : 'Novo profissional', 'Equipe e agenda', `
    <form id="professionalForm" class="form-grid modal-form">
      <div class="field full"><label>Nome</label><input class="input" name="name" required value="${escapeHtml(item?.name || '')}"></div>
      <div class="field"><label>E-mail</label><input class="input" name="email" type="email" value="${escapeHtml(item?.email || '')}"></div>
      <div class="field"><label>Telefone</label><input class="input" name="phone" value="${escapeHtml(item?.phone || '')}"></div>
      <div class="field full"><label>Descrição</label><textarea class="textarea" name="description" rows="3">${escapeHtml(item?.description || '')}</textarea></div>
      ${imageUploadField('image_url', 'Foto do profissional', 'professional', item?.image_url || '')}
      ${item ? `<div class="field full checkbox-field"><label><input type="checkbox" name="is_active" ${checked(item.is_active)}> Profissional ativo</label></div>` : ''}
      <div class="field full"><label>Serviços atendidos</label><div class="check-grid">${serviceChecks}</div></div>
      <div class="field full"><label>Horários de atendimento</label><div class="hours-editor">${hoursEditor(item)}</div></div>
      <div class="field full form-actions"><button type="button" class="btn ghost" onclick="closeModal()">Cancelar</button><button class="btn primary" type="submit">${item ? 'Salvar profissional' : 'Criar profissional'}</button></div>
    </form>`);

  wireImageUploads($('#professionalForm'));

  $('#professionalForm').onsubmit = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const basePayload = {
      name: form.name.value,
      description: nullable(form.description.value),
      phone: nullable(form.phone.value),
      email: nullable(form.email.value),
      image_url: nullable(form.image_url.value),
    };
    if (item) basePayload.is_active = form.is_active.checked;

    const serviceIds = [...form.querySelectorAll('input[name="service_ids"]:checked')].map((input) => Number(input.value));
    const hours = weekdayLabels.map((_, day) => ({
      day_of_week: day,
      start_time: form[`start_${day}`].value,
      end_time: form[`end_${day}`].value,
      is_active: form[`day_${day}`].checked,
    })).filter((hour) => hour.is_active);

    try {
      const professional = await api(item ? `/api/admin/professionals/${item.id}` : '/api/admin/professionals', {
        method: item ? 'PUT' : 'POST',
        body: JSON.stringify(basePayload),
      });
      await api(`/api/admin/professionals/${professional.id}/services`, { method: 'PUT', body: JSON.stringify({ service_ids: serviceIds }) });
      await api(`/api/admin/professionals/${professional.id}/hours`, { method: 'PUT', body: JSON.stringify({ hours }) });
      closeModal();
      showToast(item ? 'Profissional atualizado.' : 'Profissional criado.');
      await loadProfessionals();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };
};

window.toggleProfessional = async function toggleProfessional(id) {
  const item = professionals.find((professional) => professional.id === id);
  if (!item) return;
  try {
    if (item.is_active) await api(`/api/admin/professionals/${id}`, { method: 'DELETE' });
    else await api(`/api/admin/professionals/${id}`, { method: 'PUT', body: JSON.stringify({ is_active: true }) });
    await loadProfessionals();
    showToast(item.is_active ? 'Profissional desativado.' : 'Profissional ativado.');
  } catch (error) {
    showToast(error.message, 'error');
  }
};

function appointmentStatusOptions(current) {
  const allowed = {
    PENDENTE: ['PENDENTE','CONFIRMADO','CANCELADO'],
    CONFIRMADO: ['CONFIRMADO','CONCLUIDO','CANCELADO','NAO_COMPARECEU'],
    CONCLUIDO: ['CONCLUIDO'], CANCELADO: ['CANCELADO'], NAO_COMPARECEU: ['NAO_COMPARECEU'],
  };
  return (allowed[current] || [current]).map(status => `<option ${status === current ? 'selected' : ''}>${status}</option>`).join('');
}

function renderAppointmentsTable() {
  const status = $('#appointmentStatusFilter')?.value || '';
  const date = $('#appointmentDateFilter')?.value || '';
  const visible = appointments.filter(item => {
    if (status && item.status !== status) return false;
    if (date) {
      const local = new Date(item.starts_at);
      const key = `${local.getFullYear()}-${String(local.getMonth()+1).padStart(2,'0')}-${String(local.getDate()).padStart(2,'0')}`;
      if (key !== date) return false;
    }
    return true;
  });
  $('#appointmentsTable').innerHTML = visible.length
    ? `<table class="table"><thead><tr><th>Horário</th><th>Cliente</th><th>Serviço</th><th>Profissional</th><th>Status</th></tr></thead><tbody>${visible.map((appointment) => {
        const start = new Date(appointment.starts_at);
        return `<tr>
          <td><b>${start.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}</b><br><small>${start.toLocaleDateString('pt-BR')}</small></td>
          <td>${escapeHtml(appointment.customer?.name || '—')}<br><small>${escapeHtml(appointment.customer?.phone || '')}</small></td>
          <td>${escapeHtml(appointment.service?.name || '—')}<br><small>${appointment.service?.duration_minutes || ''} min</small></td>
          <td>${escapeHtml(appointment.professional?.name || '—')}</td>
          <td><select class="select compact-select" onchange="changeAppointmentStatus(${appointment.id},this.value)">${appointmentStatusOptions(appointment.status)}</select></td>
        </tr>`;
      }).join('')}</tbody></table>`
    : '<div class="empty">Nenhum agendamento para este filtro.</div>';
}

window.loadAppointments = async function loadAppointments() {
  appointments = await api('/api/admin/appointments');
  renderAppointmentsTable();
  renderStats();
};

$('#appointmentStatusFilter')?.addEventListener('change', renderAppointmentsTable);
$('#appointmentDateFilter')?.addEventListener('change', renderAppointmentsTable);
$('#appointmentTodayBtn')?.addEventListener('click', () => {
  const now = new Date();
  $('#appointmentDateFilter').value = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
  renderAppointmentsTable();
});
$('#appointmentClearBtn')?.addEventListener('click', () => {
  $('#appointmentStatusFilter').value = '';
  $('#appointmentDateFilter').value = '';
  renderAppointmentsTable();
});

window.openAgendaBlocksModal = async function openAgendaBlocksModal() {
  if (!professionals.length) await loadProfessionals();
  let blocks = [];
  try { blocks = await api('/api/admin/appointment-blocks'); } catch (error) { return showToast(error.message, 'error'); }
  const proName = id => professionals.find(p => p.id === id)?.name || `Profissional #${id}`;
  openModal('Bloqueios de agenda', 'Disponibilidade', `
    <form id="agendaBlockForm" class="form-grid">
      <div class="field"><label>Profissional</label><select class="select" name="professional_id" required><option value="">Selecione</option>${professionals.filter(p=>p.is_active).map(p=>`<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('')}</select></div>
      <div class="field"><label>Motivo</label><input class="input" name="reason" placeholder="Ex.: Folga, almoço, compromisso"></div>
      <div class="field"><label>Início</label><input class="input" type="datetime-local" name="starts_at" required></div>
      <div class="field"><label>Fim</label><input class="input" type="datetime-local" name="ends_at" required></div>
      <div class="field full"><button class="btn primary" type="submit">Criar bloqueio</button></div>
    </form>
    <hr class="soft-line">
    <h3>Bloqueios cadastrados</h3>
    <div class="agenda-block-list">${blocks.length ? blocks.map(b=>`<div class="agenda-block-row"><div><b>${escapeHtml(proName(b.professional_id))}</b><br><small>${new Date(b.starts_at).toLocaleString('pt-BR')} → ${new Date(b.ends_at).toLocaleString('pt-BR')}</small>${b.reason?`<br><small>${escapeHtml(b.reason)}</small>`:''}</div><button class="btn ghost small" type="button" onclick="deleteAgendaBlock(${b.id})">Excluir</button></div>`).join('') : '<div class="empty">Nenhum bloqueio cadastrado.</div>'}</div>
  `);
  $('#agendaBlockForm').onsubmit = async event => {
    event.preventDefault(); const form = event.currentTarget;
    const start = new Date(form.starts_at.value), end = new Date(form.ends_at.value);
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return showToast('Informe início e fim válidos.', 'error');
    if (end <= start) return showToast('O fim deve ser posterior ao início.', 'error');
    try {
      await api('/api/admin/appointment-blocks', {method:'POST', body:JSON.stringify({professional_id:Number(form.professional_id.value), starts_at:start.toISOString(), ends_at:end.toISOString(), reason:nullable(form.reason.value)})});
      showToast('Horário bloqueado.');
      openAgendaBlocksModal();
    } catch (error) { showToast(error.message,'error'); }
  };
};

window.deleteAgendaBlock = async function deleteAgendaBlock(id) {
  if (!confirm('Excluir este bloqueio de agenda?')) return;
  try { await api(`/api/admin/appointment-blocks/${id}`, {method:'DELETE'}); showToast('Bloqueio removido.'); openAgendaBlocksModal(); }
  catch (error) { showToast(error.message,'error'); }
};

window.changeAppointmentStatus = async function changeAppointmentStatus(id, status) {
  try {
    await api(`/api/admin/appointments/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) });
    showToast('Agendamento atualizado.');
    await loadAppointments();
  } catch (error) {
    showToast(error.message, 'error');
    loadAppointments();
  }
};

window.loadQuotes = async function loadQuotes() {
  quotes = await api('/api/admin/quotes');
  $('#quotesTable').innerHTML = quotes.length
    ? `<table class="table"><thead><tr><th>Solicitação</th><th>Cliente</th><th>Valor</th><th>Status</th><th>Ações</th></tr></thead><tbody>${quotes.map((quote) => `
      <tr>
        <td><b>${escapeHtml(quote.title)}</b><br><small>${escapeHtml(quote.service_name || quote.description || '')}</small></td>
        <td>${escapeHtml(quote.customer?.name || '—')}<br><small>${escapeHtml(quote.customer?.phone || '')}</small></td>
        <td>${quote.estimated_amount != null ? money(quote.estimated_amount) : '—'}</td>
        <td><select class="select compact-select" onchange="changeQuoteStatus(${quote.id},this.value)">${['RECEBIDO','EM_ANALISE','ORCAMENTO_ENVIADO','APROVADO','RECUSADO','CANCELADO','CONCLUIDO'].map((status) => `<option ${status === quote.status ? 'selected' : ''}>${status}</option>`).join('')}</select></td>
        <td><div class="row-actions">${['RECEBIDO','EM_ANALISE','ORCAMENTO_ENVIADO'].includes(quote.status) ? `<button class="btn primary small" onclick="openQuoteResponseModal(${quote.id})">Responder</button>` : ''}<button class="btn ghost small" onclick="openQuoteDetails(${quote.id})">Detalhes</button></div></td>
      </tr>`).join('')}</tbody></table>`
    : '<div class="empty">Nenhum orçamento.</div>';
  renderStats();
};

window.changeQuoteStatus = async function changeQuoteStatus(id, status) {
  try {
    await api(`/api/admin/quotes/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) });
    showToast('Orçamento atualizado.');
    await loadQuotes();
  } catch (error) {
    showToast(error.message, 'error');
    loadQuotes();
  }
};

window.openQuoteResponseModal = function openQuoteResponseModal(id) {
  const quote = quotes.find((item) => item.id === id);
  if (!quote) return;
  const expires = quote.expires_at ? new Date(quote.expires_at).toISOString().slice(0, 16) : '';
  openModal('Responder orçamento', quote.title, `
    <form id="quoteResponseForm" class="form-grid modal-form">
      <div class="field"><label>Valor estimado</label><input class="input" name="estimated_amount" type="number" min="0" step="0.01" required value="${quote.estimated_amount ?? ''}"></div>
      <div class="field"><label>Validade (opcional)</label><input class="input" name="expires_at" type="datetime-local" value="${expires}"></div>
      <div class="field full"><label>Mensagem ao cliente</label><textarea class="textarea" name="response_message" rows="6" required>${escapeHtml(quote.response_message || '')}</textarea></div>
      <div class="field full form-actions"><button type="button" class="btn ghost" onclick="closeModal()">Cancelar</button><button class="btn primary" type="submit">Enviar proposta</button></div>
    </form>`);

  $('#quoteResponseForm').onsubmit = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const rawExpires = form.expires_at.value;
    try {
      await api(`/api/admin/quotes/${id}/response`, {
        method: 'PUT',
        body: JSON.stringify({
          estimated_amount: Number(form.estimated_amount.value),
          response_message: form.response_message.value,
          expires_at: rawExpires ? new Date(rawExpires).toISOString() : null,
        }),
      });
      closeModal();
      showToast('Proposta enviada ao orçamento.');
      await loadQuotes();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };
};

window.openQuoteDetails = function openQuoteDetails(id) {
  const quote = quotes.find((item) => item.id === id);
  if (!quote) return;
  openModal('Detalhes do orçamento', quote.title, `
    <div class="detail-grid">
      <div><small>Cliente</small><b>${escapeHtml(quote.customer?.name || '—')}</b></div>
      <div><small>Contato</small><b>${escapeHtml(quote.customer?.phone || quote.customer?.email || '—')}</b></div>
      <div><small>Status</small><b>${escapeHtml(quote.status)}</b></div>
      <div><small>Valor</small><b>${quote.estimated_amount != null ? money(quote.estimated_amount) : 'Ainda não informado'}</b></div>
      <div class="full"><small>Descrição</small><p>${escapeHtml(quote.description || '')}</p></div>
      <div class="full"><small>Endereço do serviço</small><p>${escapeHtml([quote.service_address, quote.service_city, quote.service_state].filter(Boolean).join(', ') || 'Não informado')}</p></div>
      ${quote.response_message ? `<div class="full"><small>Resposta enviada</small><p>${escapeHtml(quote.response_message)}</p></div>` : ''}
    </div>`);
};


window.loadResources = async function loadResources() {
  resources = await api('/api/admin/resources');
  $('#resourcesTable').innerHTML = resources.length ? `<table class="table"><thead><tr><th>Recurso</th><th>Tipo</th><th>Capacidade</th><th>Diária</th><th>Status</th><th>Ações</th></tr></thead><tbody>${resources.map(x => `<tr><td><b>${escapeHtml(x.name)}</b><br><small>${escapeHtml(x.description || '')}</small></td><td>${escapeHtml(x.resource_type)}</td><td>${x.capacity}</td><td>${money(x.price_per_day)}</td><td>${x.is_active ? 'Ativo' : 'Inativo'}</td><td><button class="btn ghost small" onclick="openResourceModal(${x.id})">Editar</button></td></tr>`).join('')}</tbody></table>` : '<div class="empty">Nenhum recurso cadastrado.</div>';
};

window.openResourceModal = function openResourceModal(id = null) {
  const item = resources.find(x => x.id === id) || {};
  openModal(id ? 'Editar recurso' : 'Novo recurso', 'Reservas', `<form id="resourceForm" class="form-grid modal-form">
    <div class="field full"><label>Nome</label><input class="input" name="name" required value="${escapeHtml(item.name || '')}"></div>
    <div class="field"><label>Tipo</label><input class="input" name="resource_type" value="${escapeHtml(item.resource_type || 'RECURSO')}"></div>
    <div class="field"><label>Capacidade</label><input class="input" name="capacity" type="number" min="1" value="${item.capacity || 1}"></div>
    <div class="field"><label>Preço por dia</label><input class="input" name="price_per_day" type="number" min="0" step="0.01" value="${item.price_per_day ?? '0.00'}"></div>
    <div class="field full"><label>Descrição</label><textarea class="textarea" name="description" rows="3">${escapeHtml(item.description || '')}</textarea></div>
    ${imageUploadField('image_url','Imagem do recurso','resource',item.image_url || '')}
    ${id ? `<div class="field"><label><input type="checkbox" name="is_active" ${checked(item.is_active)}> Ativo</label></div>` : ''}
    <div class="field full form-actions"><button type="button" class="btn ghost" onclick="closeModal()">Cancelar</button><button class="btn primary" type="submit">Salvar</button></div>
  </form>`);
  const f = $('#resourceForm'); wireImageUploads(f);
  f.onsubmit = async e => { e.preventDefault(); const payload = { name:f.name.value, resource_type:f.resource_type.value, capacity:Number(f.capacity.value), price_per_day:Number(f.price_per_day.value), description:nullable(f.description.value), image_url:nullable(f.image_url.value) }; if (id) payload.is_active = f.is_active.checked; try { await api(id ? `/api/admin/resources/${id}` : '/api/admin/resources', {method:id?'PUT':'POST', body:JSON.stringify(payload)}); closeModal(); showToast('Recurso salvo.'); await loadResources(); } catch(err){showToast(err.message,'error');} };
};

window.loadReservations = async function loadReservations() {
  reservations = await api('/api/admin/reservations');
  $('#reservationsTable').innerHTML = reservations.length ? `<table class="table"><thead><tr><th>Recurso</th><th>Cliente</th><th>Período</th><th>Total</th><th>Status</th></tr></thead><tbody>${reservations.map(x => `<tr><td><b>${escapeHtml(x.resource?.name || '—')}</b></td><td>${escapeHtml(x.customer?.name || '—')}<br><small>${escapeHtml(x.customer?.phone || '')}</small></td><td>${new Date(x.starts_at).toLocaleString('pt-BR')}<br><small>até ${new Date(x.ends_at).toLocaleString('pt-BR')}</small></td><td>${money(x.total)}</td><td><select class="select compact-select" onchange="changeReservationStatus(${x.id},this.value)">${['PENDENTE','CONFIRMADA','CONCLUIDA','CANCELADA'].map(st => `<option ${st===x.status?'selected':''}>${st}</option>`).join('')}</select></td></tr>`).join('')}</tbody></table>` : '<div class="empty">Nenhuma reserva.</div>';
};
window.changeReservationStatus = async function(id,status){ try{await api(`/api/admin/reservations/${id}/status`,{method:'PATCH',body:JSON.stringify({status})});showToast('Reserva atualizada.');await loadReservations();}catch(err){showToast(err.message,'error');await loadReservations();} };

window.loadRentalItems = async function loadRentalItems() {
  rentalItems = await api('/api/admin/rental-items');
  $('#rentalItemsTable').innerHTML = rentalItems.length ? `<table class="table"><thead><tr><th>Item</th><th>SKU</th><th>Diária</th><th>Caução</th><th>Qtd.</th><th>Ações</th></tr></thead><tbody>${rentalItems.map(x => `<tr><td><b>${escapeHtml(x.name)}</b><br><small>${escapeHtml(x.description || '')}</small></td><td>${escapeHtml(x.sku || '—')}</td><td>${money(x.daily_rate)}</td><td>${money(x.deposit_amount)}</td><td>${x.quantity_total}</td><td><button class="btn ghost small" onclick="openRentalItemModal(${x.id})">Editar</button></td></tr>`).join('')}</tbody></table>` : '<div class="empty">Nenhum item de locação.</div>';
};

window.openRentalItemModal = function openRentalItemModal(id = null) {
  const item = rentalItems.find(x => x.id === id) || {};
  openModal(id ? 'Editar item de locação' : 'Novo item de locação', 'Locações', `<form id="rentalItemForm" class="form-grid modal-form">
    <div class="field full"><label>Nome</label><input class="input" name="name" required value="${escapeHtml(item.name || '')}"></div>
    <div class="field"><label>SKU</label><input class="input" name="sku" value="${escapeHtml(item.sku || '')}"></div>
    <div class="field"><label>Quantidade total</label><input class="input" name="quantity_total" type="number" min="1" value="${item.quantity_total || 1}"></div>
    <div class="field"><label>Diária</label><input class="input" name="daily_rate" type="number" min="0" step="0.01" value="${item.daily_rate ?? '0.00'}"></div>
    <div class="field"><label>Caução por unidade</label><input class="input" name="deposit_amount" type="number" min="0" step="0.01" value="${item.deposit_amount ?? '0.00'}"></div>
    <div class="field full"><label>Descrição</label><textarea class="textarea" name="description" rows="3">${escapeHtml(item.description || '')}</textarea></div>
    ${imageUploadField('image_url','Imagem do item','product',item.image_url || '')}
    ${id ? `<div class="field"><label><input type="checkbox" name="is_active" ${checked(item.is_active)}> Ativo</label></div>` : ''}
    <div class="field full form-actions"><button type="button" class="btn ghost" onclick="closeModal()">Cancelar</button><button class="btn primary" type="submit">Salvar</button></div>
  </form>`);
  const f=$('#rentalItemForm'); wireImageUploads(f);
  f.onsubmit=async e=>{e.preventDefault();const payload={name:f.name.value,sku:nullable(f.sku.value),quantity_total:Number(f.quantity_total.value),daily_rate:Number(f.daily_rate.value),deposit_amount:Number(f.deposit_amount.value),description:nullable(f.description.value),image_url:nullable(f.image_url.value)};if(id)payload.is_active=f.is_active.checked;try{await api(id?`/api/admin/rental-items/${id}`:'/api/admin/rental-items',{method:id?'PUT':'POST',body:JSON.stringify(payload)});closeModal();showToast('Item salvo.');await loadRentalItems();}catch(err){showToast(err.message,'error');}};
};

window.loadRentals = async function loadRentals() {
  rentals = await api('/api/admin/rentals');
  $('#rentalsTable').innerHTML = rentals.length ? `<table class="table"><thead><tr><th>Item</th><th>Cliente</th><th>Período</th><th>Qtd.</th><th>Total</th><th>Status</th></tr></thead><tbody>${rentals.map(x => `<tr><td><b>${escapeHtml(x.item?.name || '—')}</b></td><td>${escapeHtml(x.customer?.name || '—')}<br><small>${escapeHtml(x.customer?.phone || '')}</small></td><td>${new Date(x.starts_at).toLocaleString('pt-BR')}<br><small>até ${new Date(x.ends_at).toLocaleString('pt-BR')}</small></td><td>${x.quantity}</td><td>${money(x.total)}</td><td><select class="select compact-select" onchange="changeRentalStatus(${x.id},this.value)">${['PENDENTE','CONFIRMADA','RETIRADA','DEVOLVIDA','CANCELADA'].map(st => `<option ${st===x.status?'selected':''}>${st}</option>`).join('')}</select></td></tr>`).join('')}</tbody></table>` : '<div class="empty">Nenhuma locação.</div>';
};
window.changeRentalStatus = async function(id,status){try{await api(`/api/admin/rentals/${id}/status`,{method:'PATCH',body:JSON.stringify({status})});showToast('Locação atualizada.');await loadRentals();}catch(err){showToast(err.message,'error');await loadRentals();}};


window.loadPaymentSettings = async function loadPaymentSettings() {
  paymentSettings = await api('/api/admin/payment-settings');
  renderPaymentSettings();
};

window.loadPayments = async function loadPayments() {
  payments = await api('/api/admin/payments');
  const labels = { ORDER: 'Pedido', APPOINTMENT: 'Agendamento', RESERVATION: 'Reserva', RENTAL: 'Locação' };
  const box = $('#paymentsTable');
  if (!box) return;
  box.innerHTML = payments.length ? `<table class="table"><thead><tr><th>Referência</th><th>Forma</th><th>Valor</th><th>Status</th><th>Alterar</th></tr></thead><tbody>${payments.map(item => `<tr>
    <td><b>${escapeHtml(labels[item.reference_type] || item.reference_type)} #${item.reference_id}</b><br><small>${new Date(item.created_at).toLocaleString('pt-BR')}</small></td>
    <td>${escapeHtml(item.method_label || item.method)}<br><small>${escapeHtml(item.provider || 'MANUAL')}</small></td>
    <td>${money(item.amount)}</td>
    <td><span class="status ${item.status}">${escapeHtml(item.status)}</span></td>
    <td><select class="select compact-select" onchange="changePaymentStatus(${item.id},this.value)">${['PENDENTE','PAGO','RECUSADO','CANCELADO'].map(status => `<option ${status === item.status ? 'selected' : ''}>${status}</option>`).join('')}</select></td>
  </tr>`).join('')}</tbody></table>` : '<div class="empty">Nenhum pagamento registrado ainda.</div>';
  renderStats();
};

window.changePaymentStatus = async function changePaymentStatus(id, status) {
  try {
    await api(`/api/admin/payments/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) });
    showToast('Status do pagamento atualizado.');
    await Promise.all([loadPayments(), store.capabilities?.catalog ? loadOrders() : Promise.resolve()]);
  } catch (error) {
    showToast(error.message, 'error');
    await loadPayments();
  }
};

function renderPaymentSettings() {
  const form = $('#paymentSettingsForm');
  if (!form || !paymentSettings) return;
  form.innerHTML = `
    <div class="field full settings-group-title"><b>PIX manual</b><small>A chave informada ficará visível para o cliente quando ele escolher PIX.</small></div>
    <div class="field checkbox-field"><label><input type="checkbox" name="pix_enabled" ${checked(paymentSettings.pix_enabled)}> Aceitar PIX</label></div>
    <div class="field"><label>Tipo da chave</label><select class="select" name="pix_key_type"><option value="">Selecione</option>${['CPF','CNPJ','EMAIL','TELEFONE','ALEATORIA'].map(value => `<option ${optionSelected(paymentSettings.pix_key_type, value)}>${value}</option>`).join('')}</select></div>
    <div class="field full"><label>Chave PIX</label><input class="input" name="pix_key" value="${escapeHtml(paymentSettings.pix_key || '')}" placeholder="Informe a chave que será exibida aos clientes"></div>
    <div class="field"><label>Nome do recebedor</label><input class="input" name="pix_receiver_name" value="${escapeHtml(paymentSettings.pix_receiver_name || '')}"></div>
    <div class="field"><label>Cidade do recebedor</label><input class="input" name="pix_receiver_city" value="${escapeHtml(paymentSettings.pix_receiver_city || '')}"></div>
    <div class="field full notice">Se usar CPF ou CNPJ como chave PIX, esse dado será mostrado ao cliente. Prefira uma chave que você esteja confortável em divulgar.</div>
    <div class="field full settings-group-title"><b>Outras formas</b><small>Pagamentos manuais continuam sendo confirmados pelo administrador.</small></div>
    <div class="field checkbox-field"><label><input type="checkbox" name="cash_enabled" ${checked(paymentSettings.cash_enabled)}> Dinheiro</label></div>
    <div class="field checkbox-field"><label><input type="checkbox" name="card_on_delivery_enabled" ${checked(paymentSettings.card_on_delivery_enabled)}> Cartão no atendimento/entrega</label></div>
    <div class="field checkbox-field"><label><input type="checkbox" name="whatsapp_enabled" ${checked(paymentSettings.whatsapp_enabled)}> Combinar pelo WhatsApp</label></div>
    <div class="field full notice">Gateway online: <b>não configurado nesta fase</b>. A estrutura já registra provedor e referência externa para futura integração com Mercado Pago.</div>
    <div class="field full form-actions"><button class="btn primary" type="submit">Salvar pagamentos</button></div>`;

  form.onsubmit = async (event) => {
    event.preventDefault();
    const f = event.currentTarget;
    const data = {
      pix_enabled: f.pix_enabled.checked,
      pix_key_type: nullable(f.pix_key_type.value),
      pix_key: nullable(f.pix_key.value),
      pix_receiver_name: nullable(f.pix_receiver_name.value),
      pix_receiver_city: nullable(f.pix_receiver_city.value),
      cash_enabled: f.cash_enabled.checked,
      card_on_delivery_enabled: f.card_on_delivery_enabled.checked,
      whatsapp_enabled: f.whatsapp_enabled.checked,
    };
    try {
      paymentSettings = await api('/api/admin/payment-settings', { method: 'PATCH', body: JSON.stringify(data) });
      renderPaymentSettings();
      showToast('Formas de pagamento salvas.');
    } catch (error) {
      showToast(error.message, 'error');
    }
  };
}

function renderSettings() {
  const form = $('#settingsForm');
  form.innerHTML = `
    <div class="field full settings-group-title"><b>Identidade do painel</b><small>Use apenas para identificar o sistema da sua empresa no painel administrativo.</small></div>
    <div class="field full"><label>Nome exibido no painel</label><input class="input" name="panel_brand_name" value="${escapeHtml(store.panel_brand_name || 'Catálogo Digital')}" maxlength="80" placeholder="Ex.: Minha Central"></div>
    ${imageUploadField('panel_logo_url', 'Logo do painel', 'panel_logo', store.panel_logo_url || '', 'Opcional · usada somente em pontos principais do painel · JPG, PNG ou WebP · máximo 8 MB')}
    <div class="field full settings-group-title"><b>Identidade da empresa</b><small>Essas informações aparecem para seus clientes.</small></div>
    <div class="field full"><label>Nome da loja</label><input class="input" name="name" value="${escapeHtml(store.name || '')}" required></div>
    <div class="field full"><label>Descrição</label><textarea class="textarea" name="description" rows="4">${escapeHtml(store.description || '')}</textarea></div>
    ${imageUploadField('logo_url', 'Logo da loja', 'logo', store.logo_url || '', 'Recomendado: imagem quadrada · JPG, PNG ou WebP · máximo 8 MB')}
    ${imageUploadField('banner_url', 'Banner da loja', 'banner', store.banner_url || '', 'Recomendado: imagem horizontal · JPG, PNG ou WebP · máximo 8 MB')}
    <div class="field"><label>Cor principal</label><div class="color-field"><input name="primary_color" type="color" value="${escapeHtml(store.primary_color || '#7C3AED')}"><input class="input" data-color-text="primary_color" value="${escapeHtml(store.primary_color || '#7C3AED')}" maxlength="7"></div></div>
    <div class="field"><label>Cor secundária</label><div class="color-field"><input name="secondary_color" type="color" value="${escapeHtml(store.secondary_color || '#4F46E5')}"><input class="input" data-color-text="secondary_color" value="${escapeHtml(store.secondary_color || '#4F46E5')}" maxlength="7"></div></div>
    <div class="field full settings-group-title"><b>Contato e localização</b><small>Preencha apenas os canais que deseja divulgar.</small></div>
    <div class="field"><label>WhatsApp</label><input class="input" name="whatsapp" value="${escapeHtml(store.whatsapp || '')}" placeholder="5511999999999"></div>
    <div class="field"><label>Telefone</label><input class="input" name="phone" value="${escapeHtml(store.phone || '')}"></div>
    <div class="field full"><label>E-mail</label><input class="input" name="email" type="email" value="${escapeHtml(store.email || '')}"></div>
    <div class="field full"><label>Endereço</label><input class="input" name="address" value="${escapeHtml(store.address || '')}"></div>
    <div class="field"><label>Cidade</label><input class="input" name="city" value="${escapeHtml(store.city || '')}"></div>
    <div class="field"><label>UF</label><input class="input" name="state" maxlength="2" value="${escapeHtml(store.state || '')}"></div>
    <div class="field"><label>CEP</label><input class="input" name="zip_code" value="${escapeHtml(store.zip_code || '')}"></div>
    <div class="field full form-actions"><button class="btn primary" type="submit">Salvar configurações</button></div>`;

  $$('[data-color-text]').forEach((input) => {
    const color = form.elements[input.dataset.colorText];
    input.oninput = () => { if (/^#[0-9a-fA-F]{6}$/.test(input.value)) color.value = input.value; renderStorePreview(); };
    color.oninput = () => { input.value = color.value; renderStorePreview(); };
  });
  form.addEventListener('input', renderStorePreview);
  wireImageUploads(form, renderStorePreview);

  form.onsubmit = async (event) => {
    event.preventDefault();
    const names = ['panel_brand_name','panel_logo_url','name','description','primary_color','secondary_color','whatsapp','phone','email','address','city','state','zip_code','logo_url','banner_url'];
    const data = {};
    names.forEach((name) => {
      const value = form.elements[name]?.value;
      data[name] = value === '' ? null : value;
    });
    try {
      store = await api('/api/admin/store', { method: 'PATCH', body: JSON.stringify(data) });
      applyStoreTheme();
      $('#sideStoreName').textContent = store.name;
      renderAdminIdentity();
      $('#openStoreBtn').href = `loja.html?slug=${encodeURIComponent(store.slug)}`;
      renderSettings();
      showToast('Configurações salvas.');
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  renderStorePreview();
}

function renderStorePreview() {
  const form = $('#settingsForm');
  if (!form || !store) return;
  const name = form.elements.name?.value || store.name;
  const description = form.elements.description?.value || 'Descrição da sua empresa.';
  const primary = form.elements.primary_color?.value || store.primary_color || '#7C3AED';
  const secondary = form.elements.secondary_color?.value || store.secondary_color || '#4F46E5';
  const logo = form.elements.logo_url?.value;
  const banner = form.elements.banner_url?.value;

  $('#storePreview').innerHTML = `
    <div class="preview-banner" style="background:${banner ? `linear-gradient(rgba(15,23,42,.42),rgba(15,23,42,.72)),url('${escapeHtml(assetUrl(banner))}') center/cover` : `linear-gradient(135deg,${primary},${secondary})`}">
      <div class="preview-logo">${logo ? `<img src="${escapeHtml(assetUrl(logo))}" alt="">` : escapeHtml(name.split(/\s+/).slice(0,2).map((part)=>part[0]).join('').toUpperCase())}</div>
      <span class="preview-kicker">${escapeHtml(store.business_category?.name || 'Seu negócio')}</span>
      <h3>${escapeHtml(name)}</h3>
      <p>${escapeHtml(description)}</p>
      <span class="preview-button" style="background:${primary}">${escapeHtml(store.business_model?.primary_action || 'Explorar')}</span>
    </div>`;
}

window.closeModal = closeModal;

if (getAuthToken()) startAdmin();


window.loadPrivacy = async function loadPrivacy() {
  const [requestsResult, logsResult] = await Promise.allSettled([
    api('/api/admin/privacy/requests'),
    api('/api/admin/privacy/audit-logs?limit=80'),
  ]);
  privacyRequests = requestsResult.status === 'fulfilled' ? requestsResult.value : [];
  auditLogs = logsResult.status === 'fulfilled' ? logsResult.value : [];
  renderPrivacy();
};

function renderPrivacy() {
  const requestsRoot = $('#privacyRequestsTable');
  const logsRoot = $('#auditLogsTable');
  if (requestsRoot) {
    requestsRoot.innerHTML = privacyRequests.length ? `<table class="table"><thead><tr><th>Protocolo</th><th>Tipo</th><th>Contato</th><th>Status</th><th>Ações</th></tr></thead><tbody>${privacyRequests.map(item => `<tr>
      <td><b>${escapeHtml(item.protocol)}</b><br><small>${item.created_at ? new Date(item.created_at).toLocaleString('pt-BR') : ''}</small></td>
      <td>${escapeHtml(item.request_type)}</td>
      <td>${escapeHtml(item.customer_name || '')}<br><small>${escapeHtml(item.customer_email || item.customer_phone || '')}</small></td>
      <td><span class="status ${item.status === 'CONCLUIDA' ? 'CONFIRMADO' : item.status === 'RECUSADA' ? 'CANCELADO' : 'PENDENTE'}">${escapeHtml(item.status)}</span></td>
      <td><button class="btn ghost small" onclick="openPrivacyModal(${item.id})">Atualizar</button></td>
    </tr>`).join('')}</tbody></table>` : '<div class="empty">Nenhuma solicitação de privacidade registrada.</div>';
  }
  if (logsRoot) {
    logsRoot.innerHTML = auditLogs.length ? `<table class="table"><thead><tr><th>Quando</th><th>Evento</th><th>Entidade</th></tr></thead><tbody>${auditLogs.map(item => `<tr>
      <td>${item.created_at ? new Date(item.created_at).toLocaleString('pt-BR') : ''}</td>
      <td><b>${escapeHtml(item.action)}</b></td>
      <td>${escapeHtml(item.entity_type || '—')} ${item.entity_id ? `#${escapeHtml(item.entity_id)}` : ''}</td>
    </tr>`).join('')}</tbody></table>` : '<div class="empty">Nenhum evento de auditoria para exibir.</div>';
  }
}

window.openPrivacyModal = function openPrivacyModal(id) {
  const item = privacyRequests.find(row => row.id === id);
  if (!item) return;
  openModal('Solicitação de privacidade', 'LGPD', `<form id="privacyUpdateForm" class="form-grid">
    <div class="field full"><label>Protocolo</label><input class="input" value="${escapeHtml(item.protocol)}" disabled></div>
    <div class="field"><label>Tipo</label><input class="input" value="${escapeHtml(item.request_type)}" disabled></div>
    <div class="field"><label>Status</label><select class="select" name="status"><option ${optionSelected(item.status,'PENDENTE')}>PENDENTE</option><option ${optionSelected(item.status,'EM_ANALISE')}>EM_ANALISE</option><option ${optionSelected(item.status,'CONCLUIDA')}>CONCLUIDA</option><option ${optionSelected(item.status,'RECUSADA')}>RECUSADA</option></select></div>
    <div class="field full"><label>Solicitação</label><textarea class="textarea" rows="4" disabled>${escapeHtml(item.details || '')}</textarea></div>
    <div class="field full"><label>Notas internas</label><textarea class="textarea" name="admin_notes" rows="4">${escapeHtml(item.admin_notes || '')}</textarea></div>
    <div class="field full"><button class="btn primary" type="submit">Salvar</button></div>
  </form>`);
  $('#privacyUpdateForm').onsubmit = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    try {
      await api(`/api/admin/privacy/requests/${id}`, { method:'PATCH', body:JSON.stringify({ status:form.status.value, admin_notes:form.admin_notes.value }) });
      closeModal();
      await loadPrivacy();
      showToast('Solicitação atualizada.');
    } catch (error) { showToast(error.message, 'error'); }
  };
};
