const $s = s => document.querySelector(s);
let superMe = null;
let superStores = [];
let businessCategories = [];
let plans = [];

$s('#superLoginForm').onsubmit = async e => {
  e.preventDefault();
  const f = e.currentTarget;
  try {
    const out = await api('/api/auth/login', {method:'POST', body:JSON.stringify({email:f.email.value,password:f.password.value})});
    sessionStorage.setItem('catalogo_token', out.access_token);
    await startSuperAdmin();
  } catch (err) { showToast(err.message, 'error'); }
};

$s('#superLogoutBtn').onclick = () => { clearAuthToken(); location.reload(); };

document.querySelectorAll('[data-super-section]').forEach(btn => btn.onclick = () => switchSuperSection(btn.dataset.superSection));

function switchSuperSection(id) {
  document.querySelectorAll('#superView .admin-section').forEach(s => s.classList.remove('active'));
  $s(`#super-${id}`)?.classList.add('active');
  document.querySelectorAll('[data-super-section]').forEach(b => b.classList.toggle('active', b.dataset.superSection === id));
  const titles = {dashboard:'Dashboard',stores:'Lojas',plans:'Planos'};
  $s('#superTitle').textContent = titles[id] || id;
}

async function startSuperAdmin() {
  try {
    superMe = await api('/api/auth/me');
    if (superMe.role !== 'SUPER_ADMINISTRADOR') throw new Error('Esta conta não possui acesso de Super Admin.');
    $s('#superLoginView').classList.add('hidden');
    $s('#superView').classList.remove('hidden');
    await Promise.all([loadBusinessCategories(), loadPlans()]);
    await Promise.all([loadSuperDashboard(), loadSuperStores()]);
  } catch (err) {
    clearAuthToken();
    $s('#superLoginView').classList.remove('hidden');
    $s('#superView').classList.add('hidden');
    showToast(err.message, 'error');
  }
}

window.loadSuperDashboard = async function() {
  const d = await api('/api/super-admin/dashboard');
  const rows = [
    ['Lojas ativas', `${d.active_stores}/${d.stores}`],
    ['Assinaturas ativas', d.active_subscriptions ?? '—'],
    ['Pedidos', d.orders],
    ['Clientes', d.customers],
    ['Valor bruto', money(d.gross_order_value)],
    ['Produtos', d.products],
    ['Agendamentos', d.appointments],
    ['Admins de loja', d.store_admins],
  ];
  $s('#superStats').innerHTML = rows.map(([l,v]) => `<div class="stat-card"><span>${l}</span><strong>${v}</strong></div>`).join('');
};

function planNameFromStore(store) {
  return store.subscription?.plan?.name || 'Gratuito';
}

window.loadSuperStores = async function() {
  superStores = await api('/api/super-admin/stores');
  $s('#superStoresTable').innerHTML = superStores.length ? `<table class="table"><thead><tr><th>Loja</th><th>Modelo</th><th>Plano</th><th>Admin</th><th>Indicadores</th><th>Status</th><th>Ações</th></tr></thead><tbody>${superStores.map(store => `<tr>
    <td><b>${escapeHtml(store.name)}</b><br><small>/${escapeHtml(store.slug)}</small></td>
    <td>${escapeHtml(store.business_category?.name || '—')}<br><small>${escapeHtml(store.business_model?.name || '—')}</small></td>
    <td><b>${escapeHtml(planNameFromStore(store))}</b><br><select class="select compact-select" onchange="changeStorePlan(${store.id},this.value)">${plans.filter(p=>p.is_active).map(p=>`<option value="${p.id}" ${p.id===store.subscription?.plan?.id?'selected':''}>${escapeHtml(p.name)}</option>`).join('')}</select></td>
    <td>${escapeHtml(store.admin?.name || '—')}<br><small>${escapeHtml(store.admin?.email || '')}</small></td>
    <td><small>${store.metrics.products} produtos · ${store.metrics.orders} pedidos<br>${store.metrics.customers} clientes · ${store.metrics.appointments} agendas · ${store.metrics.quotes} orçamentos</small></td>
    <td><span class="status ${store.is_active?'CONFIRMADO':'CANCELADO'}">${store.is_active?'Ativa':'Inativa'}</span></td>
    <td><div style="display:flex;gap:6px;flex-wrap:wrap"><a class="btn ghost small" target="_blank" href="loja.html?slug=${encodeURIComponent(store.slug)}">Abrir</a><button class="btn ${store.is_active?'danger':'primary'} small" onclick="toggleStoreStatus(${store.id},${!store.is_active})">${store.is_active?'Desativar':'Ativar'}</button></div></td>
  </tr>`).join('')}</tbody></table>` : '<div class="empty">Nenhuma loja cadastrada.</div>';
};

window.changeStorePlan = async function(storeId, planId) {
  try {
    await api(`/api/super-admin/stores/${storeId}/subscription`, {method:'PUT', body:JSON.stringify({plan_id:Number(planId),status:'ACTIVE',billing_cycle:'MONTHLY'})});
    showToast('Plano da loja atualizado.');
    await Promise.all([loadSuperStores(), loadSuperDashboard()]);
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
  $s('#businessCategorySelect').innerHTML = '<option value="">Selecione...</option>' + businessCategories.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('');
}

window.loadPlans = async function() {
  plans = await api('/api/super-admin/plans');
  const select = $s('#newStorePlanSelect');
  if (select) select.innerHTML = plans.filter(p=>p.is_active).map(p => `<option value="${p.id}" ${p.code==='GRATUITO'?'selected':''}>${escapeHtml(p.name)} — ${money(p.monthly_price)}/mês</option>`).join('');
  renderPlans();
};

function renderPlans() {
  const root = $s('#plansTable');
  if (!root) return;
  root.innerHTML = plans.length ? `<table class="table"><thead><tr><th>Plano</th><th>Preço</th><th>Limites</th><th>Recursos</th><th>Status</th><th></th></tr></thead><tbody>${plans.map(p=>`<tr>
    <td><b>${escapeHtml(p.name)}</b><br><small class="plan-code">${escapeHtml(p.code)}</small></td>
    <td>${money(p.monthly_price)}/mês<br><small>${p.yearly_price?`${money(p.yearly_price)}/ano`:'—'}</small></td>
    <td><small>${limitText(p.limits?.products)} produtos · ${limitText(p.limits?.services)} serviços · ${limitText(p.limits?.professionals)} profissionais</small></td>
    <td><small>${Object.entries(p.features||{}).filter(([,v])=>v).map(([k])=>featureLabel(k)).join(' · ') || 'Recursos essenciais'}</small></td>
    <td><span class="status ${p.is_active?'CONFIRMADO':'CANCELADO'}">${p.is_active?'Ativo':'Inativo'}</span></td>
    <td><button class="btn ghost small" onclick="openPlanModal(${p.id})">Editar</button></td>
  </tr>`).join('')}</tbody></table>` : '<div class="empty">Nenhum plano cadastrado.</div>';
}

function limitText(value) { return value == null || Number(value) < 0 ? '∞' : Number(value); }
function featureLabel(key) { return ({coupons:'Cupons',promotions:'Promoções',custom_branding:'Marca',reports:'Relatórios',priority_support:'Suporte',custom_domain:'Domínio',online_payments:'Pagamentos online'})[key] || key; }

window.openSuperModal = () => $s('#superStoreModal').classList.add('open');
window.closeSuperModal = () => $s('#superStoreModal').classList.remove('open');
window.closePlanModal = () => $s('#planModal').classList.remove('open');

window.openPlanModal = function(id = null) {
  const p = id ? plans.find(x=>x.id===id) : null;
  const f = $s('#planForm');
  f.reset();
  f.elements['id'].value = p?.id || '';
  f.elements['name'].value = p?.name || '';
  f.elements['code'].value = p?.code || '';
  f.elements['code'].disabled = Boolean(p);
  f.elements['monthly_price'].value = Number(p?.monthly_price || 0);
  f.elements['yearly_price'].value = p?.yearly_price ?? '';
  f.elements['description'].value = p?.description || '';
  f.elements['limit_products'].value = p?.limits?.products ?? 20;
  f.elements['limit_services'].value = p?.limits?.services ?? 10;
  f.elements['limit_professionals'].value = p?.limits?.professionals ?? 1;
  ['coupons','promotions','custom_branding','reports','priority_support','custom_domain','online_payments'].forEach(k => f.elements[`feature_${k}`].checked = Boolean(p?.features?.[k]));
  f.elements['is_active'].checked = p?.is_active ?? true;
  $s('#planModalTitle').textContent = p ? `Editar ${p.name}` : 'Novo plano';
  $s('#planModal').classList.add('open');
};

$s('#planForm').onsubmit = async e => {
  e.preventDefault(); const f=e.currentTarget; const id=Number(f.elements['id'].value||0);
  const payload={
    name:f.elements['name'].value,
    description:f.elements['description'].value||null,
    monthly_price:Number(f.elements['monthly_price'].value||0),
    yearly_price:f.elements['yearly_price'].value===''?null:Number(f.elements['yearly_price'].value),
    limits:{products:Number(f.elements['limit_products'].value),services:Number(f.elements['limit_services'].value),professionals:Number(f.elements['limit_professionals'].value)},
    features:{coupons:f.elements['feature_coupons'].checked,promotions:f.elements['feature_promotions'].checked,custom_branding:f.elements['feature_custom_branding'].checked,reports:f.elements['feature_reports'].checked,priority_support:f.elements['feature_priority_support'].checked,custom_domain:f.elements['feature_custom_domain'].checked,online_payments:f.elements['feature_online_payments'].checked},
    is_active:f.elements['is_active'].checked,
    sort_order:id ? (plans.find(p=>p.id===id)?.sort_order||0) : plans.length+1,
  };
  if (!id) payload.code=f.elements['code'].value;
  try {
    await api(id?`/api/super-admin/plans/${id}`:'/api/super-admin/plans',{method:id?'PATCH':'POST',body:JSON.stringify(payload)});
    closePlanModal(); showToast(id?'Plano atualizado.':'Plano criado.'); await Promise.all([loadPlans(),loadSuperStores()]);
  } catch(err){showToast(err.message,'error');}
};

$s('#superStoreForm').onsubmit = async e => {
  e.preventDefault();
  const f = e.currentTarget;
  const payload = {
    name: f.name.value,
    business_category_id: Number(f.business_category_id.value),
    plan_id: f.plan_id.value ? Number(f.plan_id.value) : null,
    description: f.description.value || null,
    primary_color: f.primary_color.value,
    secondary_color: f.secondary_color.value,
    whatsapp: f.whatsapp.value || null,
    phone: f.phone.value || null,
    admin_name: f.admin_name.value,
    admin_email: f.admin_email.value,
    admin_password: f.admin_password.value,
  };
  try {
    const created = await api('/api/super-admin/stores', {method:'POST', body:JSON.stringify(payload)});
    closeSuperModal(); f.reset(); f.primary_color.value='#7C3AED'; f.secondary_color.value='#4F46E5'; await loadPlans();
    showToast(`Loja ${created.name} criada com sucesso.`);
    await Promise.all([loadSuperDashboard(), loadSuperStores()]);
    switchSuperSection('stores');
  } catch (err) { showToast(err.message, 'error'); }
};

if (getAuthToken()) startSuperAdmin();
