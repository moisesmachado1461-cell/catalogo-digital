const trackQs = new URLSearchParams(location.search);
const trackSlug = trackQs.get('slug') || trackQs.get('loja') || '';
const trackToken = trackQs.get('token') || trackQs.get('pedido') || trackQs.get('agendamento') || '';
const rawTrackType = String(trackQs.get('tipo') || (trackQs.get('pedido') ? 'pedido' : trackQs.get('agendamento') ? 'agendamento' : '')).toLowerCase();
const trackType = ['agendamento','appointment'].includes(rawTrackType) ? 'APPOINTMENT' : 'ORDER';
const trackCard = document.querySelector('#trackingCard');

function trackInitials(value='') { return String(value).trim().split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase() || 'CD'; }
function trackStatusClass(status) { return ['CANCELADO','NAO_COMPARECEU'].includes(status) ? 'is-danger' : ['ENTREGUE','CONCLUIDO'].includes(status) ? 'is-success' : 'is-warning'; }
function orderLabel(status, fulfillment) { return ({PENDENTE:'Pedido recebido',CONFIRMADO:'Confirmado',EM_PREPARACAO:'Em preparação',PRONTO:fulfillment==='RETIRADA'?'Pronto para retirada':'Pronto',SAIU_PARA_ENTREGA:'Saiu para entrega',ENTREGUE:fulfillment==='RETIRADA'?'Retirado':'Entregue',CANCELADO:'Cancelado'})[status] || status; }
function appointmentLabel(status) { return ({PENDENTE:'Pendente',CONFIRMADO:'Confirmado',CONCLUIDO:'Concluído',CANCELADO:'Cancelado',NAO_COMPARECEU:'Não compareceu'})[status] || status; }

function applyTrackStore(store) {
  if (!store) return;
  document.documentElement.style.setProperty('--brand', store.primary_color || '#6d5dfc');
  document.documentElement.style.setProperty('--brand2', store.secondary_color || '#4f46e5');
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', store.primary_color || '#6d5dfc');
  document.querySelector('#trackingBrandName').textContent = store.name;
  document.querySelector('#trackingBrandMark').innerHTML = store.logo_url ? `<img src="${escapeHtml(assetUrl(store.logo_url))}" alt="Logo de ${escapeHtml(store.name)}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit">` : escapeHtml(trackInitials(store.name));
  document.querySelector('#trackingBackStore').href = `loja.html?slug=${encodeURIComponent(trackSlug)}`;
  document.querySelector('#trackingAccountLink').href = `cliente.html?slug=${encodeURIComponent(trackSlug)}`;
}

function progressHtml(steps, current, canceled=false) {
  if (canceled) return '<div class="notice" style="background:#fef3f2;color:#b42318;border:1px solid #fecdca">Este acompanhamento foi cancelado.</div>';
  const currentIndex = Math.max(0, steps.findIndex(step => step.key === current));
  return `<div class="tracking-progress" style="--steps:${steps.length}">${steps.map((step,index)=>`<div class="tracking-step ${index < currentIndex ? 'done' : index === currentIndex ? 'current' : ''}"><span>${escapeHtml(step.label)}</span></div>`).join('')}</div>`;
}

function paymentTrackHtml(payment) {
  if (!payment) return '';
  return `<div class="tracking-data"><small>Pagamento</small><strong>${escapeHtml(payment.method_label || payment.method || '—')} · ${escapeHtml(payment.status || '')}</strong></div>`;
}

async function loadOrderTracking() {
  const data = await api(`/api/public/stores/${encodeURIComponent(trackSlug)}/orders/${encodeURIComponent(trackToken)}`);
  applyTrackStore(data.store);
  document.title = `Pedido ${data.order_number} — ${data.store.name}`;
  document.querySelector('#trackingEyebrow').textContent = 'ACOMPANHAMENTO DO PEDIDO';
  document.querySelector('#trackingTitle').textContent = `Pedido ${data.order_number}`;
  document.querySelector('#trackingSubtitle').textContent = 'Veja em que etapa seu pedido está agora.';
  const steps = data.fulfillment_method === 'ENTREGA'
    ? [{key:'PENDENTE',label:'Recebido'},{key:'CONFIRMADO',label:'Confirmado'},{key:'EM_PREPARACAO',label:'Preparando'},{key:'PRONTO',label:'Pronto'},{key:'SAIU_PARA_ENTREGA',label:'Em entrega'},{key:'ENTREGUE',label:'Entregue'}]
    : [{key:'PENDENTE',label:'Recebido'},{key:'CONFIRMADO',label:'Confirmado'},{key:'EM_PREPARACAO',label:'Preparando'},{key:'PRONTO',label:'Pronto'},{key:'ENTREGUE',label:'Retirado'}];
  trackCard.innerHTML = `
    <div class="tracking-overview"><div><span class="section-kicker">${escapeHtml(data.store.name)}</span><h2>${escapeHtml(orderLabel(data.status,data.fulfillment_method))}</h2><small>Atualizado em ${new Date(data.updated_at).toLocaleString('pt-BR')}</small></div><span class="customer-status ${trackStatusClass(data.status)}">${escapeHtml(orderLabel(data.status,data.fulfillment_method))}</span></div>
    ${progressHtml(steps,data.status,data.status==='CANCELADO')}
    <div class="tracking-data-grid">
      <div class="tracking-data"><small>Cliente</small><strong>${escapeHtml(data.customer?.name || 'Cliente')}</strong></div>
      <div class="tracking-data"><small>Forma de recebimento</small><strong>${data.fulfillment_method === 'ENTREGA' ? 'Entrega' : 'Retirada'}</strong></div>
      <div class="tracking-data"><small>Data do pedido</small><strong>${new Date(data.created_at).toLocaleString('pt-BR')}</strong></div>
      ${paymentTrackHtml(data.payment)}
    </div>
    <div class="tracking-items">${(data.items||[]).map(item=>`<div class="tracking-item"><span>${item.quantity}× ${escapeHtml(item.product_name)}${item.variant_name?` · ${escapeHtml(item.variant_name)}`:''}</span><strong>${money(item.line_total)}</strong></div>`).join('')}</div>
    <div class="tracking-total"><span>Total</span><strong>${money(data.total)}</strong></div>
    <div class="tracking-account-cta"><div><b>Quer guardar seu histórico?</b><p>Crie sua conta de cliente e acompanhe seus próximos pedidos e agendamentos em um só lugar.</p></div><a class="btn primary" href="cliente.html?slug=${encodeURIComponent(trackSlug)}&modo=cadastro&tipo=pedido&token=${encodeURIComponent(trackToken)}">Criar minha conta</a></div>`;
}

async function cancelTrackedAppointment() {
  if (!confirm('Deseja realmente cancelar este agendamento?')) return;
  const button = document.querySelector('#trackCancelAppointment');
  if (button) { button.disabled = true; button.textContent = 'Cancelando...'; }
  try {
    await api(`/api/public/stores/${encodeURIComponent(trackSlug)}/appointments/${encodeURIComponent(trackToken)}/cancel`, {method:'PATCH'});
    showToast('Agendamento cancelado.');
    await loadAppointmentTracking();
  } catch (error) { showToast(error.message,'error'); if(button){button.disabled=false;button.textContent='Cancelar agendamento';} }
}

async function loadAppointmentTracking() {
  const data = await api(`/api/public/stores/${encodeURIComponent(trackSlug)}/appointments/${encodeURIComponent(trackToken)}`);
  applyTrackStore(data.store);
  document.title = `Agendamento — ${data.store.name}`;
  document.querySelector('#trackingEyebrow').textContent = 'ACOMPANHAMENTO DO AGENDAMENTO';
  document.querySelector('#trackingTitle').textContent = data.service.name;
  document.querySelector('#trackingSubtitle').textContent = 'Consulte o horário e a situação do seu atendimento.';
  const start = new Date(data.starts_at), end = new Date(data.ends_at);
  const steps = [{key:'PENDENTE',label:'Solicitado'},{key:'CONFIRMADO',label:'Confirmado'},{key:'CONCLUIDO',label:'Concluído'}];
  const canceled = ['CANCELADO','NAO_COMPARECEU'].includes(data.status);
  trackCard.innerHTML = `
    <div class="tracking-overview"><div><span class="section-kicker">${escapeHtml(data.store.name)}</span><h2>${escapeHtml(appointmentLabel(data.status))}</h2></div><span class="customer-status ${trackStatusClass(data.status)}">${escapeHtml(appointmentLabel(data.status))}</span></div>
    ${progressHtml(steps,data.status,canceled)}
    <div class="tracking-data-grid">
      <div class="tracking-data"><small>Data</small><strong>${start.toLocaleDateString('pt-BR',{weekday:'long',day:'2-digit',month:'long',year:'numeric'})}</strong></div>
      <div class="tracking-data"><small>Horário</small><strong>${start.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})} – ${end.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}</strong></div>
      <div class="tracking-data"><small>Profissional</small><strong>${escapeHtml(data.professional.name)}</strong></div>
      <div class="tracking-data"><small>Cliente</small><strong>${escapeHtml(data.customer?.name || 'Cliente')}</strong></div>
      ${paymentTrackHtml(data.payment)}
    </div>
    ${data.notes ? `<div class="tracking-data"><small>Observações</small><strong>${escapeHtml(data.notes)}</strong></div>` : ''}
    <div class="customer-record-actions">${data.can_cancel ? '<button id="trackCancelAppointment" class="btn danger" type="button">Cancelar agendamento</button>' : ''}</div>
    <div class="tracking-account-cta"><div><b>Tenha seus agendamentos sempre à mão.</b><p>Crie sua conta e acompanhe este e os próximos atendimentos.</p></div><a class="btn primary" href="cliente.html?slug=${encodeURIComponent(trackSlug)}&modo=cadastro&tipo=agendamento&token=${encodeURIComponent(trackToken)}">Criar minha conta</a></div>`;
  document.querySelector('#trackCancelAppointment')?.addEventListener('click', cancelTrackedAppointment);
}

async function startTracking() {
  if (!trackSlug || !trackToken) {
    trackCard.innerHTML = '<div class="empty"><h2>Link incompleto</h2><p>Use o link recebido após seu pedido ou agendamento.</p></div>';
    return;
  }
  try {
    if (trackType === 'APPOINTMENT') await loadAppointmentTracking();
    else await loadOrderTracking();
  } catch (error) {
    trackCard.innerHTML = `<div class="empty"><h2>Não encontramos este acompanhamento</h2><p>${escapeHtml(error.message)}</p></div>`;
  }
}

startTracking();
