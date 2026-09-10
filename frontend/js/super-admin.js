const $s = s => document.querySelector(s);
let superMe = null;
let superStores = [];
let businessCategories = [];
let plans = [];
let billingSubscriptions = [];
let billingInvoices = [];
let billingProviders = [];

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
  const titles = {dashboard:'Dashboard',stores:'Lojas',plans:'Planos',billing:'Cobrança'};
  $s('#superTitle').textContent = titles[id] || id;
}

async function startSuperAdmin() {
  try {
    superMe = await api('/api/auth/me');
    if (superMe.role !== 'SUPER_ADMINISTRADOR') throw new Error('Esta conta não possui acesso de Super Admin.');
    $s('#superLoginView').classList.add('hidden');
    $s('#superView').classList.remove('hidden');
    await Promise.all([loadBusinessCategories(), loadPlans()]);
    await Promise.all([loadSuperDashboard(), loadSuperStores(), loadBillingCenter()]);
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


function billingDate(value, fallback = '—') {
  if (!value) return fallback;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return fallback;
  return date.toLocaleDateString('pt-BR');
}

function billingLabel(value) {
  return ({ACTIVE:'Ativa',TRIAL:'Teste',PAST_DUE:'Em atraso',EXPIRED:'Expirada',CANCELED:'Cancelada',PENDING:'Pendente',PAID:'Pago',FAILED:'Falhou'})[String(value || '').toUpperCase()] || String(value || '—');
}

function billingClass(value) {
  const status=String(value||'').toUpperCase();
  if(['ACTIVE','PAID'].includes(status)) return 'CONFIRMADO';
  if(['PAST_DUE','FAILED','PENDING','TRIAL'].includes(status)) return 'PENDENTE';
  return 'CANCELADO';
}

function billingProviderName(code) {
  const key=String(code||'MANUAL').toUpperCase();
  return billingProviders.find(p=>p.code===key)?.display_name || ({MANUAL:'Controle manual'})[key] || key.replaceAll('_',' ');
}

function billingCycle(value) { return String(value||'MONTHLY').toUpperCase()==='YEARLY' ? 'Anual' : 'Mensal'; }

function currentBillingSubscriptions() {
  const seen=new Set();
  return billingSubscriptions.filter(row=>{
    if(seen.has(row.store_id)) return false;
    seen.add(row.store_id);
    return true;
  });
}

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
};

function renderBillingStats() {
  const root=$s('#billingStats'); if(!root) return;
  const rows=currentBillingSubscriptions();
  const active=rows.filter(r=>['ACTIVE','TRIAL'].includes(r.status)).length;
  const late=rows.filter(r=>r.status==='PAST_DUE').length;
  const open=billingInvoices.filter(r=>['PENDING','FAILED'].includes(r.status));
  const paid=billingInvoices.filter(r=>r.status==='PAID');
  const stats=[
    ['Assinaturas ativas',active],
    ['Em atraso',late],
    ['A receber',money(open.reduce((sum,row)=>sum+Number(row.amount||0),0))],
    ['Recebido',money(paid.reduce((sum,row)=>sum+Number(row.amount||0),0))],
  ];
  root.innerHTML=stats.map(([label,value])=>`<div class="stat-card billing-stat"><span>${escapeHtml(label)}</span><strong>${value}</strong></div>`).join('');
}

function renderBillingProviders() {
  const root=$s('#billingProviders'); if(!root) return;
  root.innerHTML=billingProviders.map(provider=>`<div class="billing-provider-card ${provider.configured?'is-ready':''}">
    <div><b>${escapeHtml(provider.display_name)}</b><small>${provider.automatic?'Cobrança automática':'Operação manual'}</small></div>
    <span class="status ${provider.configured?'CONFIRMADO':'PENDENTE'}">${provider.configured?'Configurado':'Pendente'}</span>
  </div>`).join('') || '<div class="empty">Nenhum provedor cadastrado.</div>';
}

window.renderBillingSubscriptions = function() {
  const root=$s('#billingSubscriptionsTable'); if(!root) return;
  const query=String($s('#billingSearch')?.value||'').trim().toLowerCase();
  const status=String($s('#billingStatusFilter')?.value||'').toUpperCase();
  const rows=currentBillingSubscriptions().filter(row=>{
    const haystack=`${row.store_name||''} ${row.plan?.name||''} ${row.provider||''}`.toLowerCase();
    return (!query || haystack.includes(query)) && (!status || row.status===status);
  });
  root.innerHTML=rows.length?`<table class="table billing-table"><thead><tr><th>Loja</th><th>Plano</th><th>Status</th><th>Cobrança</th><th>Próximo vencimento</th><th>Ações</th></tr></thead><tbody>${rows.map(row=>{
    const paidPlan=Number(row.billing_cycle==='YEARLY'?row.plan?.yearly_price:row.plan?.monthly_price||0)>0;
    const canManage=['ACTIVE','TRIAL','PAST_DUE'].includes(row.status);
    return `<tr>
      <td><b>${escapeHtml(row.store_name||`Loja #${row.store_id}`)}</b><br><small>Assinatura #${row.id}</small></td>
      <td><b>${escapeHtml(row.plan?.name||'—')}</b><br><small>${billingCycle(row.billing_cycle)}</small></td>
      <td><span class="status ${billingClass(row.status)}">${escapeHtml(billingLabel(row.status))}</span></td>
      <td>${escapeHtml(billingProviderName(row.provider))}<br><small>${row.auto_renew?'Renovação automática':'Renovação manual'}</small></td>
      <td>${billingDate(row.next_billing_at||row.current_period_end)}${row.cancel_at_period_end?'<br><small>Cancelará no fim do período</small>':''}</td>
      <td><div class="billing-row-actions">${paidPlan&&canManage?`<button class="btn ghost small" onclick="createRenewalInvoice(${row.id})">Gerar fatura</button>`:''}${canManage?`<button class="btn ghost small" onclick="cancelBillingSubscription(${row.id},true)">Cancelar no vencimento</button><button class="btn danger small" onclick="cancelBillingSubscription(${row.id},false)">Cancelar agora</button>`:'<span class="muted-note">Sem ações</span>'}</div></td>
    </tr>`;
  }).join('')}</tbody></table>`:'<div class="empty">Nenhuma assinatura encontrada com os filtros atuais.</div>';
};

window.renderBillingInvoices = function() {
  const root=$s('#billingInvoicesTable'); if(!root) return;
  const status=String($s('#invoiceStatusFilter')?.value||'').toUpperCase();
  const rows=billingInvoices.filter(row=>!status||row.status===status);
  root.innerHTML=rows.length?`<table class="table billing-table"><thead><tr><th>Fatura</th><th>Loja</th><th>Plano</th><th>Vencimento</th><th>Valor</th><th>Método</th><th>Status</th><th>Ações</th></tr></thead><tbody>${rows.map(row=>`<tr>
    <td><b>#${row.id}</b><br><small>${row.invoice_type==='PLAN_CHANGE'?'Troca de plano':'Renovação'}</small></td>
    <td>${escapeHtml(row.store_name||`Loja #${row.store_id}`)}</td>
    <td>${escapeHtml(row.plan_name||'—')}</td>
    <td>${billingDate(row.due_at||row.created_at)}</td>
    <td><b>${money(row.amount)}</b></td>
    <td>${escapeHtml(row.payment_method||billingProviderName(row.provider))}</td>
    <td><span class="status ${billingClass(row.status)}">${escapeHtml(billingLabel(row.status))}</span></td>
    <td><div class="billing-row-actions">${['PENDING','FAILED'].includes(row.status)?`<button class="btn primary small" onclick="setInvoiceStatus(${row.id},'PAID')">Registrar pago</button><button class="btn ghost small" onclick="setInvoiceStatus(${row.id},'FAILED')">Marcar falha</button><button class="btn danger small" onclick="setInvoiceStatus(${row.id},'CANCELED')">Cancelar</button>`:'<span class="muted-note">Concluída</span>'}</div></td>
  </tr>`).join('')}</tbody></table>`:'<div class="empty">Nenhuma fatura encontrada.</div>';
};

window.createRenewalInvoice = async function(subscriptionId) {
  try {
    await api(`/api/super-admin/billing/subscriptions/${subscriptionId}/renewal-invoice`,{method:'POST',body:JSON.stringify({payment_method:'MANUAL'})});
    showToast('Fatura de renovação criada.');
    await loadBillingCenter();
  } catch(err){ showToast(err.message,'error'); }
};

window.setInvoiceStatus = async function(invoiceId,status) {
  const action=status==='PAID'?'registrar esta fatura como paga':status==='FAILED'?'marcar esta cobrança como falha':'cancelar esta fatura';
  if(!confirm(`Deseja ${action}?`)) return;
  try {
    const payload={status};
    if(status==='PAID') payload.payment_method='MANUAL';
    if(status==='FAILED') payload.failure_reason='Falha registrada manualmente pelo Super Admin';
    await api(`/api/super-admin/billing/invoices/${invoiceId}/status`,{method:'PATCH',body:JSON.stringify(payload)});
    showToast('Fatura atualizada.');
    await Promise.all([loadBillingCenter(),loadSuperDashboard(),loadSuperStores()]);
  } catch(err){ showToast(err.message,'error'); }
};

window.cancelBillingSubscription = async function(subscriptionId,atPeriodEnd=true) {
  const text=atPeriodEnd?'cancelar ao final do período atual':'cancelar imediatamente';
  if(!confirm(`Tem certeza que deseja ${text}?`)) return;
  try {
    await api(`/api/super-admin/billing/subscriptions/${subscriptionId}/cancel`,{method:'POST',body:JSON.stringify({at_period_end:atPeriodEnd})});
    showToast(atPeriodEnd?'Cancelamento agendado.':'Assinatura cancelada.');
    await Promise.all([loadBillingCenter(),loadSuperDashboard(),loadSuperStores()]);
  } catch(err){ showToast(err.message,'error'); }
};

window.processDueBilling = async function() {
  if(!confirm('Processar agora os vencimentos e regras de cobrança das assinaturas?')) return;
  try {
    const result=await api('/api/super-admin/billing/process-due',{method:'POST'});
    showToast(`Processamento concluído: ${result.invoices_created||0} nova(s) fatura(s).`);
    await Promise.all([loadBillingCenter(),loadSuperDashboard(),loadSuperStores()]);
  } catch(err){ showToast(err.message,'error'); }
};

if (getAuthToken()) startSuperAdmin();
