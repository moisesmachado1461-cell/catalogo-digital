const $s = selector => document.querySelector(selector);
let superMe = null;
let superStores = [];
let businessCategories = [];
let plans = [];
let billingSubscriptions = [];
let billingInvoices = [];
let billingProviders = [];
let superDashboardData = null;
let currentSuperSection = 'dashboard';

function initials(value, fallback = 'SA') {
  const parts = String(value || '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return fallback;
  return parts.slice(0, 2).map(part => part[0]).join('').toUpperCase();
}

function metricCard(label, value, iconText, note) {
  return `<div class="stat-card"><span class="super-metric-icon">${escapeHtml(iconText)}</span><span>${escapeHtml(label)}</span><strong>${value}</strong><small class="super-metric-note">${escapeHtml(note)}</small></div>`;
}

function renderSuperIdentity() {
  const name = superMe?.name || superMe?.full_name || 'Super Admin';
  const firstName = name.split(' ')[0] || 'Super Admin';
  const avatar = initials(name, 'SA');
  ['#superProfileName', '#superUserName'].forEach(selector => { const el = $s(selector); if (el) el.textContent = name; });
  ['#superProfileAvatar', '#superUserAvatar'].forEach(selector => { const el = $s(selector); if (el) el.textContent = avatar; });
  const title = $s('#superWelcomeTitle');
  if (title) title.textContent = `Olá, ${firstName}. A plataforma está sob controle.`;
  const today = $s('#superTodayLabel');
  if (today) today.textContent = new Intl.DateTimeFormat('pt-BR', { weekday:'long', day:'2-digit', month:'long', year:'numeric' }).format(new Date());
}

function updateSuperBreadcrumb(id) {
  const titles = {dashboard:'Dashboard', stores:'Lojas', plans:'Planos', billing:'Cobrança'};
  const text = titles[id] || id;
  const title = $s('#superTitle');
  const crumb = $s('#superBreadcrumbCurrent');
  if (title) title.textContent = text;
  if (crumb) crumb.textContent = text;
}

window.switchSuperSection = function(id) {
  currentSuperSection = id;
  document.querySelectorAll('#superView .admin-section').forEach(section => section.classList.remove('active'));
  $s(`#super-${id}`)?.classList.add('active');
  document.querySelectorAll('[data-super-section]').forEach(button => button.classList.toggle('active', button.dataset.superSection === id));
  updateSuperBreadcrumb(id);
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

document.querySelectorAll('[data-super-section]').forEach(button => {
  button.onclick = () => switchSuperSection(button.dataset.superSection);
});

window.refreshCurrentSuperSection = async function() {
  try {
    if (currentSuperSection === 'stores') await loadSuperStores();
    else if (currentSuperSection === 'plans') await loadPlans();
    else if (currentSuperSection === 'billing') await loadBillingCenter();
    else await Promise.all([loadSuperDashboard(), loadSuperStores(), loadBillingCenter()]);
    renderPlatformInsights();
    showToast('Painel atualizado.');
  } catch (err) { showToast(err.message, 'error'); }
};

$s('#superLoginForm').onsubmit = async event => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const out = await api('/api/auth/login', {method:'POST', body:JSON.stringify({email:form.email.value,password:form.password.value})});
    sessionStorage.setItem('catalogo_token', out.access_token);
    await startSuperAdmin();
  } catch (err) { showToast(err.message, 'error'); }
};

$s('#superLogoutBtn').onclick = () => { clearAuthToken(); location.reload(); };

async function startSuperAdmin() {
  try {
    superMe = await api('/api/auth/me');
    if (superMe.role !== 'SUPER_ADMINISTRADOR') throw new Error('Esta conta não possui acesso de Super Admin.');
    $s('#superLoginView').classList.add('hidden');
    $s('#superView').classList.remove('hidden');
    renderSuperIdentity();
    await Promise.all([loadBusinessCategories(), loadPlans()]);
    await Promise.all([loadSuperDashboard(), loadSuperStores(), loadBillingCenter()]);
    renderPlatformInsights();
  } catch (err) {
    clearAuthToken();
    $s('#superLoginView').classList.remove('hidden');
    $s('#superView').classList.add('hidden');
    showToast(err.message, 'error');
  }
}

window.loadSuperDashboard = async function() {
  const data = await api('/api/super-admin/dashboard');
  superDashboardData = data;
  const root = $s('#superStats');
  if (!root) return;
  root.innerHTML = [
    metricCard('Lojas ativas', `${data.active_stores}/${data.stores}`, 'L', 'Operação ativa'),
    metricCard('Assinaturas', data.active_subscriptions ?? '—', 'A', 'Planos ativos'),
    metricCard('Pedidos', data.orders, 'P', 'Volume acumulado'),
    metricCard('Clientes', data.customers, 'C', 'Base cadastrada'),
    metricCard('Valor bruto', money(data.gross_order_value), 'R$', 'Pedidos da plataforma'),
    metricCard('Produtos', data.products, 'PR', 'Itens cadastrados'),
    metricCard('Agendamentos', data.appointments, 'AG', 'Serviços agendados'),
    metricCard('Admins de loja', data.store_admins, 'AD', 'Gestores cadastrados'),
  ].join('');
};

function renderPlatformInsights() {
  const root = $s('#superPlatformInsights');
  if (!root) return;
  const totalStores = superStores.length;
  const activeStores = superStores.filter(store => store.is_active).length;
  const inactiveStores = Math.max(totalStores - activeStores, 0);
  const currentSubscriptions = currentBillingSubscriptions();
  const lateSubscriptions = currentSubscriptions.filter(row => row.status === 'PAST_DUE').length;
  const paidInvoices = billingInvoices.filter(row => row.status === 'PAID');
  const pendingInvoices = billingInvoices.filter(row => ['PENDING','FAILED'].includes(row.status));
  const received = paidInvoices.reduce((sum,row) => sum + Number(row.amount || 0), 0);
  const pending = pendingInvoices.reduce((sum,row) => sum + Number(row.amount || 0), 0);
  const activeRate = totalStores ? Math.round((activeStores / totalStores) * 100) : 0;
  root.innerHTML = [
    ['Lojas operando', `${activeRate}%`, `${activeStores} ativa(s) e ${inactiveStores} inativa(s)`],
    ['Receita SaaS registrada', money(received), `${paidInvoices.length} fatura(s) paga(s)`],
    ['Valores pendentes', money(pending), `${pendingInvoices.length} fatura(s) exigindo atenção`],
    ['Assinaturas em atraso', String(lateSubscriptions), lateSubscriptions ? 'Requer acompanhamento' : 'Nenhuma pendência crítica'],
  ].map(([label,value,note]) => `<div class="super-insight-card"><span>${escapeHtml(label)}</span><b>${value}</b><small>${escapeHtml(note)}</small></div>`).join('');
}

function planNameFromStore(store) {
  return store.subscription?.plan?.name || 'Gratuito';
}

window.loadSuperStores = async function() {
  superStores = await api('/api/super-admin/stores');
  renderSuperStores();
  renderPlatformInsights();
};

window.renderSuperStores = function() {
  const root = $s('#superStoresTable');
  if (!root) return;
  const query = String($s('#superStoreSearch')?.value || '').trim().toLowerCase();
  const status = String($s('#superStoreStatus')?.value || '');
  const rows = superStores.filter(store => {
    const haystack = `${store.name || ''} ${store.slug || ''} ${store.business_category?.name || ''} ${store.business_model?.name || ''} ${store.admin?.name || ''} ${store.admin?.email || ''}`.toLowerCase();
    const statusOk = !status || (status === 'active' ? store.is_active : !store.is_active);
    return (!query || haystack.includes(query)) && statusOk;
  });
  root.innerHTML = rows.length ? `<table class="table super-stores-table"><thead><tr><th>Loja</th><th>Segmento</th><th>Plano</th><th>Administrador</th><th>Indicadores</th><th>Status</th><th>Ações</th></tr></thead><tbody>${rows.map(store => `
    <tr>
      <td><div class="super-store-title"><span class="super-store-logo">${escapeHtml(initials(store.name, 'L'))}</span><div><b>${escapeHtml(store.name)}</b><small>/${escapeHtml(store.slug)}</small></div></div></td>
      <td>${escapeHtml(store.business_category?.name || '—')}<br><small>${escapeHtml(store.business_model?.name || '—')}</small></td>
      <td><b>${escapeHtml(planNameFromStore(store))}</b><br><select class="select compact-select" onchange="changeStorePlan(${store.id},this.value)">${plans.filter(p=>p.is_active).map(p=>`<option value="${p.id}" ${p.id===store.subscription?.plan?.id?'selected':''}>${escapeHtml(p.name)}</option>`).join('')}</select></td>
      <td>${escapeHtml(store.admin?.name || '—')}<br><small>${escapeHtml(store.admin?.email || '')}</small></td>
      <td><div class="super-indicators"><span class="super-indicator-chip">${store.metrics.products} produtos</span><span class="super-indicator-chip">${store.metrics.orders} pedidos</span><span class="super-indicator-chip">${store.metrics.customers} clientes</span><span class="super-indicator-chip">${store.metrics.appointments} agendas</span><span class="super-indicator-chip">${store.metrics.quotes} orçamentos</span></div></td>
      <td><span class="status ${store.is_active?'CONFIRMADO':'CANCELADO'}">${store.is_active?'Ativa':'Inativa'}</span></td>
      <td><div class="super-table-actions"><a class="btn ghost small" target="_blank" href="loja.html?slug=${encodeURIComponent(store.slug)}">Abrir</a><button class="btn ${store.is_active?'danger':'primary'} small" onclick="toggleStoreStatus(${store.id},${!store.is_active})">${store.is_active?'Desativar':'Ativar'}</button></div></td>
    </tr>`).join('')}</tbody></table>` : '<div class="empty">Nenhuma loja encontrada com os filtros atuais.</div>';
};

window.changeStorePlan = async function(storeId, planId) {
  try {
    await api(`/api/super-admin/stores/${storeId}/subscription`, {method:'PUT', body:JSON.stringify({plan_id:Number(planId),status:'ACTIVE',billing_cycle:'MONTHLY'})});
    showToast('Plano da loja atualizado.');
    await Promise.all([loadSuperStores(), loadSuperDashboard(), loadBillingCenter()]);
  } catch (err) { showToast(err.message, 'error'); await loadSuperStores(); }
};

window.toggleStoreStatus = async function(id, isActive) {
  try {
    await api(`/api/super-admin/stores/${id}/status`, {method:'PATCH', body:JSON.stringify({is_active:isActive})});
    showToast(isActive ? 'Loja ativada.' : 'Loja desativada.');
    await Promise.all([loadSuperDashboard(), loadSuperStores()]);
  } catch (err) { showToast(err.message, 'error'); }
};

async function loadBusinessCategories() {
  businessCategories = await api('/api/business/categories');
  const select = $s('#businessCategorySelect');
  if (select) select.innerHTML = '<option value="">Selecione...</option>' + businessCategories.map(category => `<option value="${category.id}">${escapeHtml(category.name)}</option>`).join('');
}

window.loadPlans = async function() {
  plans = await api('/api/super-admin/plans');
  const select = $s('#newStorePlanSelect');
  if (select) select.innerHTML = plans.filter(plan=>plan.is_active).map(plan => `<option value="${plan.id}" ${plan.code==='GRATUITO'?'selected':''}>${escapeHtml(plan.name)} — ${money(plan.monthly_price)}/mês</option>`).join('');
  renderPlans();
};

function renderPlans() {
  const root = $s('#plansTable');
  if (!root) return;
  root.innerHTML = plans.length ? plans.map(plan => {
    const activeFeatures = Object.entries(plan.features || {}).filter(([,value]) => value).map(([key]) => featureLabel(key));
    const description = plan.description || 'Plano comercial do Catálogo Digital.';
    return `<article class="super-plan-card ${plan.is_active?'':'is-inactive'}">
      <div class="super-plan-card-head"><div><h3>${escapeHtml(plan.name)}</h3><span class="super-plan-code">${escapeHtml(plan.code)}</span></div><span class="status ${plan.is_active?'CONFIRMADO':'CANCELADO'}">${plan.is_active?'Ativo':'Inativo'}</span></div>
      <div class="super-plan-price"><strong>${money(plan.monthly_price)}</strong><span>/ mês</span></div>
      <p class="super-plan-description">${escapeHtml(description)}</p>
      <div class="super-plan-limits"><span class="super-plan-chip">${limitText(plan.limits?.products)} produtos</span><span class="super-plan-chip">${limitText(plan.limits?.services)} serviços</span><span class="super-plan-chip">${limitText(plan.limits?.professionals)} profissionais</span></div>
      <div class="super-plan-features">${activeFeatures.length ? activeFeatures.slice(0,5).map(feature => `<span class="super-plan-feature">${escapeHtml(feature)}</span>`).join('') : '<span class="super-plan-chip">Recursos essenciais</span>'}</div>
      <div class="super-plan-footer"><small>${plan.yearly_price ? `${money(plan.yearly_price)}/ano` : 'Sem preço anual'}</small><button class="btn ghost small" onclick="openPlanModal(${plan.id})">Editar plano</button></div>
    </article>`;
  }).join('') : '<div class="empty">Nenhum plano cadastrado.</div>';
}

function limitText(value) { return value == null || Number(value) < 0 ? '∞' : Number(value); }
function featureLabel(key) { return ({coupons:'Cupons',promotions:'Promoções',custom_branding:'Marca própria',reports:'Relatórios',priority_support:'Suporte prioritário',custom_domain:'Domínio próprio',online_payments:'Pagamentos online'})[key] || key; }

window.openSuperModal = () => $s('#superStoreModal').classList.add('open');
window.closeSuperModal = () => $s('#superStoreModal').classList.remove('open');
window.closePlanModal = () => $s('#planModal').classList.remove('open');

window.openPlanModal = function(id = null) {
  const plan = id ? plans.find(item=>item.id===id) : null;
  const form = $s('#planForm');
  form.reset();
  form.elements['id'].value = plan?.id || '';
  form.elements['name'].value = plan?.name || '';
  form.elements['code'].value = plan?.code || '';
  form.elements['code'].disabled = Boolean(plan);
  form.elements['monthly_price'].value = Number(plan?.monthly_price || 0);
  form.elements['yearly_price'].value = plan?.yearly_price ?? '';
  form.elements['description'].value = plan?.description || '';
  form.elements['limit_products'].value = plan?.limits?.products ?? 20;
  form.elements['limit_services'].value = plan?.limits?.services ?? 10;
  form.elements['limit_professionals'].value = plan?.limits?.professionals ?? 1;
  ['coupons','promotions','custom_branding','reports','priority_support','custom_domain','online_payments'].forEach(key => form.elements[`feature_${key}`].checked = Boolean(plan?.features?.[key]));
  form.elements['is_active'].checked = plan?.is_active ?? true;
  $s('#planModalTitle').textContent = plan ? `Editar ${plan.name}` : 'Novo plano';
  $s('#planModal').classList.add('open');
};

$s('#planForm').onsubmit = async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const id = Number(form.elements['id'].value || 0);
  const payload = {
    name:form.elements['name'].value,
    description:form.elements['description'].value || null,
    monthly_price:Number(form.elements['monthly_price'].value || 0),
    yearly_price:form.elements['yearly_price'].value === '' ? null : Number(form.elements['yearly_price'].value),
    limits:{products:Number(form.elements['limit_products'].value),services:Number(form.elements['limit_services'].value),professionals:Number(form.elements['limit_professionals'].value)},
    features:{coupons:form.elements['feature_coupons'].checked,promotions:form.elements['feature_promotions'].checked,custom_branding:form.elements['feature_custom_branding'].checked,reports:form.elements['feature_reports'].checked,priority_support:form.elements['feature_priority_support'].checked,custom_domain:form.elements['feature_custom_domain'].checked,online_payments:form.elements['feature_online_payments'].checked},
    is_active:form.elements['is_active'].checked,
    sort_order:id ? (plans.find(plan=>plan.id===id)?.sort_order || 0) : plans.length + 1,
  };
  if (!id) payload.code = form.elements['code'].value;
  try {
    await api(id ? `/api/super-admin/plans/${id}` : '/api/super-admin/plans', {method:id?'PATCH':'POST',body:JSON.stringify(payload)});
    closePlanModal();
    showToast(id ? 'Plano atualizado.' : 'Plano criado.');
    await Promise.all([loadPlans(), loadSuperStores()]);
  } catch(err) { showToast(err.message,'error'); }
};

$s('#superStoreForm').onsubmit = async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = {
    name: form.name.value,
    business_category_id: Number(form.business_category_id.value),
    plan_id: form.plan_id.value ? Number(form.plan_id.value) : null,
    description: form.description.value || null,
    primary_color: form.primary_color.value,
    secondary_color: form.secondary_color.value,
    whatsapp: form.whatsapp.value || null,
    phone: form.phone.value || null,
    admin_name: form.admin_name.value,
    admin_email: form.admin_email.value,
    admin_password: form.admin_password.value,
  };
  try {
    const created = await api('/api/super-admin/stores', {method:'POST', body:JSON.stringify(payload)});
    closeSuperModal();
    form.reset();
    form.primary_color.value = '#7C3AED';
    form.secondary_color.value = '#4F46E5';
    await loadPlans();
    showToast(`Loja ${created.name} criada com sucesso.`);
    await Promise.all([loadSuperDashboard(), loadSuperStores(), loadBillingCenter()]);
    switchSuperSection('stores');
  } catch (err) { showToast(err.message, 'error'); }
};

function billingDate(value, fallback = '—') {
  if (!value) return fallback;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? fallback : date.toLocaleDateString('pt-BR');
}
function billingLabel(value) { return ({ACTIVE:'Ativa',TRIAL:'Teste',PAST_DUE:'Em atraso',EXPIRED:'Expirada',CANCELED:'Cancelada',PENDING:'Pendente',PAID:'Pago',FAILED:'Falhou'})[String(value || '').toUpperCase()] || String(value || '—'); }
function billingClass(value) { const status=String(value||'').toUpperCase(); if(['ACTIVE','PAID'].includes(status)) return 'CONFIRMADO'; if(['PAST_DUE','FAILED','PENDING','TRIAL'].includes(status)) return 'PENDENTE'; return 'CANCELADO'; }
function billingProviderName(code) { const key=String(code||'MANUAL').toUpperCase(); return billingProviders.find(provider=>provider.code===key)?.display_name || ({MANUAL:'Controle manual'})[key] || key.replaceAll('_',' '); }
function billingCycle(value) { return String(value||'MONTHLY').toUpperCase()==='YEARLY' ? 'Anual' : 'Mensal'; }
function currentBillingSubscriptions() { const seen=new Set(); return billingSubscriptions.filter(row=>{ if(seen.has(row.store_id)) return false; seen.add(row.store_id); return true; }); }

window.loadBillingCenter = async function() {
  const [subscriptions, invoices, providers] = await Promise.all([
    api('/api/super-admin/subscriptions'),
    api('/api/super-admin/billing/invoices?limit=200'),
    api('/api/super-admin/billing/providers'),
  ]);
  billingSubscriptions = subscriptions || [];
  billingInvoices = invoices || [];
  billingProviders = providers || [];
  renderBillingStats();
  renderBillingProviders();
  renderBillingSubscriptions();
  renderBillingInvoices();
  renderPlatformInsights();
};

function renderBillingStats() {
  const root = $s('#billingStats'); if (!root) return;
  const rows = currentBillingSubscriptions();
  const active = rows.filter(row=>['ACTIVE','TRIAL'].includes(row.status)).length;
  const late = rows.filter(row=>row.status==='PAST_DUE').length;
  const open = billingInvoices.filter(row=>['PENDING','FAILED'].includes(row.status));
  const paid = billingInvoices.filter(row=>row.status==='PAID');
  root.innerHTML = [
    metricCard('Assinaturas ativas', active, 'A', 'Clientes em operação'),
    metricCard('Em atraso', late, '!', late ? 'Requer acompanhamento' : 'Sem atrasos'),
    metricCard('A receber', money(open.reduce((sum,row)=>sum+Number(row.amount||0),0)), 'R$', `${open.length} fatura(s) aberta(s)`),
    metricCard('Recebido', money(paid.reduce((sum,row)=>sum+Number(row.amount||0),0)), '✓', `${paid.length} fatura(s) paga(s)`),
  ].join('');
}

function renderBillingProviders() {
  const root = $s('#billingProviders'); if (!root) return;
  root.innerHTML = billingProviders.map(provider=>`<div class="billing-provider-card ${provider.configured?'is-ready':''}"><div><b>${escapeHtml(provider.display_name)}</b><small>${provider.automatic?'Cobrança automática':'Operação manual'}</small></div><span class="status ${provider.configured?'CONFIRMADO':'PENDENTE'}">${provider.configured?'Configurado':'Pendente'}</span></div>`).join('') || '<div class="empty">Nenhum provedor cadastrado.</div>';
}

window.renderBillingSubscriptions = function() {
  const root = $s('#billingSubscriptionsTable'); if (!root) return;
  const query = String($s('#billingSearch')?.value || '').trim().toLowerCase();
  const status = String($s('#billingStatusFilter')?.value || '').toUpperCase();
  const rows = currentBillingSubscriptions().filter(row => {
    const haystack = `${row.store_name||''} ${row.plan?.name||''} ${row.provider||''}`.toLowerCase();
    return (!query || haystack.includes(query)) && (!status || row.status===status);
  });
  root.innerHTML = rows.length ? `<table class="table billing-table"><thead><tr><th>Loja</th><th>Plano</th><th>Status</th><th>Cobrança</th><th>Próximo vencimento</th><th>Ações</th></tr></thead><tbody>${rows.map(row=>{
    const paidPlan=Number(row.billing_cycle==='YEARLY'?row.plan?.yearly_price:row.plan?.monthly_price||0)>0;
    const canManage=['ACTIVE','TRIAL','PAST_DUE'].includes(row.status);
    return `<tr><td><b>${escapeHtml(row.store_name||`Loja #${row.store_id}`)}</b><br><small>Assinatura #${row.id}</small></td><td><b>${escapeHtml(row.plan?.name||'—')}</b><br><small>${billingCycle(row.billing_cycle)}</small></td><td><span class="status ${billingClass(row.status)}">${escapeHtml(billingLabel(row.status))}</span></td><td>${escapeHtml(billingProviderName(row.provider))}<br><small>${row.auto_renew?'Renovação automática':'Renovação manual'}</small></td><td>${billingDate(row.next_billing_at||row.current_period_end)}${row.cancel_at_period_end?'<br><small>Cancelará no fim do período</small>':''}</td><td><div class="billing-row-actions">${paidPlan&&canManage?`<button class="btn ghost small" onclick="createRenewalInvoice(${row.id})">Gerar fatura</button>`:''}${canManage?`<button class="btn ghost small" onclick="cancelBillingSubscription(${row.id},true)">Cancelar no vencimento</button><button class="btn danger small" onclick="cancelBillingSubscription(${row.id},false)">Cancelar agora</button>`:'<span class="muted-note">Sem ações</span>'}</div></td></tr>`;
  }).join('')}</tbody></table>` : '<div class="empty">Nenhuma assinatura encontrada com os filtros atuais.</div>';
};

window.renderBillingInvoices = function() {
  const root = $s('#billingInvoicesTable'); if (!root) return;
  const status = String($s('#invoiceStatusFilter')?.value || '').toUpperCase();
  const rows = billingInvoices.filter(row=>!status||row.status===status);
  root.innerHTML = rows.length ? `<table class="table billing-table"><thead><tr><th>Fatura</th><th>Loja</th><th>Plano</th><th>Vencimento</th><th>Valor</th><th>Método</th><th>Status</th><th>Ações</th></tr></thead><tbody>${rows.map(row=>`<tr><td><b>#${row.id}</b><br><small>${row.invoice_type==='PLAN_CHANGE'?'Troca de plano':'Renovação'}</small></td><td>${escapeHtml(row.store_name||`Loja #${row.store_id}`)}</td><td>${escapeHtml(row.plan_name||'—')}</td><td>${billingDate(row.due_at||row.created_at)}</td><td><b>${money(row.amount)}</b></td><td>${escapeHtml(row.payment_method||billingProviderName(row.provider))}</td><td><span class="status ${billingClass(row.status)}">${escapeHtml(billingLabel(row.status))}</span></td><td><div class="billing-row-actions">${['PENDING','FAILED'].includes(row.status)?`<button class="btn primary small" onclick="setInvoiceStatus(${row.id},'PAID')">Registrar pago</button><button class="btn ghost small" onclick="setInvoiceStatus(${row.id},'FAILED')">Marcar falha</button><button class="btn danger small" onclick="setInvoiceStatus(${row.id},'CANCELED')">Cancelar</button>`:'<span class="muted-note">Concluída</span>'}</div></td></tr>`).join('')}</tbody></table>` : '<div class="empty">Nenhuma fatura encontrada.</div>';
};

window.createRenewalInvoice = async function(subscriptionId) {
  try { await api(`/api/super-admin/billing/subscriptions/${subscriptionId}/renewal-invoice`,{method:'POST',body:JSON.stringify({payment_method:'MANUAL'})}); showToast('Fatura de renovação criada.'); await loadBillingCenter(); }
  catch(err){ showToast(err.message,'error'); }
};
window.setInvoiceStatus = async function(invoiceId,status) {
  const action=status==='PAID'?'registrar esta fatura como paga':status==='FAILED'?'marcar esta cobrança como falha':'cancelar esta fatura';
  if(!confirm(`Deseja ${action}?`)) return;
  try { const payload={status}; if(status==='PAID') payload.payment_method='MANUAL'; if(status==='FAILED') payload.failure_reason='Falha registrada manualmente pelo Super Admin'; await api(`/api/super-admin/billing/invoices/${invoiceId}/status`,{method:'PATCH',body:JSON.stringify(payload)}); showToast('Fatura atualizada.'); await Promise.all([loadBillingCenter(),loadSuperDashboard(),loadSuperStores()]); }
  catch(err){ showToast(err.message,'error'); }
};
window.cancelBillingSubscription = async function(subscriptionId,atPeriodEnd=true) {
  const text=atPeriodEnd?'cancelar ao final do período atual':'cancelar imediatamente';
  if(!confirm(`Tem certeza que deseja ${text}?`)) return;
  try { await api(`/api/super-admin/billing/subscriptions/${subscriptionId}/cancel`,{method:'POST',body:JSON.stringify({at_period_end:atPeriodEnd})}); showToast(atPeriodEnd?'Cancelamento agendado.':'Assinatura cancelada.'); await Promise.all([loadBillingCenter(),loadSuperDashboard(),loadSuperStores()]); }
  catch(err){ showToast(err.message,'error'); }
};
window.processDueBilling = async function() {
  if(!confirm('Processar agora os vencimentos e regras de cobrança das assinaturas?')) return;
  try { const result=await api('/api/super-admin/billing/process-due',{method:'POST'}); showToast(`Processamento concluído: ${result.invoices_created||0} nova(s) fatura(s).`); await Promise.all([loadBillingCenter(),loadSuperDashboard(),loadSuperStores()]); }
  catch(err){ showToast(err.message,'error'); }
};

if (getAuthToken()) startSuperAdmin();
