const trackQs = new URLSearchParams(location.search);
const trackSlug = trackQs.get('slug') || trackQs.get('loja') || '';
const trackToken = trackQs.get('token') || trackQs.get('pedido') || trackQs.get('agendamento') || '';
const rawTrackType = String(
  trackQs.get('tipo') || (trackQs.get('pedido') ? 'pedido' : trackQs.get('agendamento') ? 'agendamento' : ''),
).toLowerCase();
const trackType = ['agendamento', 'appointment'].includes(rawTrackType) ? 'APPOINTMENT' : 'ORDER';
const { query: trackQuery, initials } = window.CatalogoUtils;
const trackCard = trackQuery('#trackingCard');

const APPOINTMENT_STATUS_LABELS = {
  PENDENTE: 'Pendente',
  CONFIRMADO: 'Confirmado',
  CONCLUIDO: 'Concluído',
  CANCELADO: 'Cancelado',
  NAO_COMPARECEU: 'Não compareceu',
};

const DELIVERY_ORDER_STEPS = [
  { key: 'PENDENTE', label: 'Recebido' },
  { key: 'CONFIRMADO', label: 'Confirmado' },
  { key: 'EM_PREPARACAO', label: 'Preparando' },
  { key: 'PRONTO', label: 'Pronto' },
  { key: 'SAIU_PARA_ENTREGA', label: 'Em entrega' },
  { key: 'ENTREGUE', label: 'Entregue' },
];

const PICKUP_ORDER_STEPS = [
  { key: 'PENDENTE', label: 'Recebido' },
  { key: 'CONFIRMADO', label: 'Confirmado' },
  { key: 'EM_PREPARACAO', label: 'Preparando' },
  { key: 'PRONTO', label: 'Pronto' },
  { key: 'ENTREGUE', label: 'Retirado' },
];

const APPOINTMENT_STEPS = [
  { key: 'PENDENTE', label: 'Solicitado' },
  { key: 'CONFIRMADO', label: 'Confirmado' },
  { key: 'CONCLUIDO', label: 'Concluído' },
];

function trackStatusClass(status) {
  if (['CANCELADO', 'NAO_COMPARECEU'].includes(status)) return 'is-danger';
  if (['ENTREGUE', 'CONCLUIDO'].includes(status)) return 'is-success';
  return 'is-warning';
}

function orderLabel(status, fulfillment) {
  const labels = {
    PENDENTE: 'Pedido recebido',
    CONFIRMADO: 'Confirmado',
    EM_PREPARACAO: 'Em preparação',
    PRONTO: fulfillment === 'RETIRADA' ? 'Pronto para retirada' : 'Pronto',
    SAIU_PARA_ENTREGA: 'Saiu para entrega',
    ENTREGUE: fulfillment === 'RETIRADA' ? 'Retirado' : 'Entregue',
    CANCELADO: 'Cancelado',
  };
  return labels[status] || status;
}

function appointmentLabel(status) {
  return APPOINTMENT_STATUS_LABELS[status] || status;
}

function applyTrackStore(store) {
  if (!store) return;

  const primaryColor = store.primary_color || '#6d5dfc';
  const secondaryColor = store.secondary_color || '#4f46e5';
  document.documentElement.style.setProperty('--brand', primaryColor);
  document.documentElement.style.setProperty('--brand2', secondaryColor);
  trackQuery('meta[name="theme-color"]')?.setAttribute('content', primaryColor);

  trackQuery('#trackingBrandName').textContent = store.name;
  trackQuery('#trackingBrandMark').innerHTML = store.logo_url
    ? `<img src="${escapeHtml(assetUrl(store.logo_url))}" alt="Logo de ${escapeHtml(store.name)}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit">`
    : escapeHtml(initials(store.name, 'CD'));
  trackQuery('#trackingBackStore').href = `loja.html?slug=${encodeURIComponent(trackSlug)}`;
  trackQuery('#trackingAccountLink').href = `cliente.html?slug=${encodeURIComponent(trackSlug)}`;
}

function progressHtml(steps, current, canceled = false) {
  if (canceled) {
    return '<div class="notice" style="background:#fef3f2;color:#b42318;border:1px solid #fecdca">Este acompanhamento foi cancelado.</div>';
  }

  const currentIndex = Math.max(0, steps.findIndex(step => step.key === current));
  const progressSteps = steps.map((step, index) => {
    const stateClass = index < currentIndex ? 'done' : index === currentIndex ? 'current' : '';
    return `<div class="tracking-step ${stateClass}"><span>${escapeHtml(step.label)}</span></div>`;
  }).join('');

  return `<div class="tracking-progress" style="--steps:${steps.length}">${progressSteps}</div>`;
}

function paymentTrackHtml(payment) {
  if (!payment) return '';
  const method = payment.method_label || payment.method || '—';
  const base = `<div class="tracking-data"><small>Pagamento</small><strong>${escapeHtml(method)} · ${escapeHtml(payment.status || '')}</strong></div>`;
  if (payment.method === 'PIX' && ['PENDENTE', 'INFORMADO'].includes(payment.status)) {
    const informed = payment.status === 'INFORMADO';
    return `${base}<div class="tracking-online-pix"><div><small>Valor final</small><b>${money(payment.amount)}</b><code>${escapeHtml(payment.pix_qr_code || payment.pix_key || '')}</code>${informed ? '<span class="payment-informed"><strong>Pagamento informado</strong><small>A loja verificará o recebimento.</small></span>' : `<button class="btn primary small" type="button" data-inform-payment="${escapeHtml(payment.public_token || '')}">Já paguei</button>`}</div></div>`;
  }
  if (payment.method !== 'PIX_ONLINE' || payment.status !== 'PENDENTE') return base;
  const qrImage = payment.pix_qr_code_base64 ? (String(payment.pix_qr_code_base64).startsWith('data:') ? payment.pix_qr_code_base64 : `data:image/png;base64,${payment.pix_qr_code_base64}`) : '';
  return `${base}<div class="tracking-online-pix">${qrImage ? `<img src="${escapeHtml(qrImage)}" alt="QR Code Pix">` : ''}<div><small>Pagamento pendente</small><b>Conclua pelo Pix</b><code>${escapeHtml(payment.pix_qr_code || '')}</code><button class="btn primary small" type="button" data-copy-tracking-pix="${escapeHtml(payment.pix_qr_code || '')}">Copiar Pix</button></div></div>`;
}

function orderItemsHtml(items = []) {
  return items.map(item => {
    const variant = item.variant_name ? ` · ${escapeHtml(item.variant_name)}` : '';
    return `<div class="tracking-item"><span>${item.quantity}× ${escapeHtml(item.product_name)}${variant}</span><strong>${money(item.line_total)}</strong></div>`;
  }).join('');
}

async function loadOrderTracking() {
  const data = await api(`/api/public/stores/${encodeURIComponent(trackSlug)}/orders/${encodeURIComponent(trackToken)}`);
  applyTrackStore(data.store);

  document.title = `Pedido ${data.order_number} — ${data.store.name}`;
  trackQuery('#trackingEyebrow').textContent = 'ACOMPANHAMENTO DO PEDIDO';
  trackQuery('#trackingTitle').textContent = `Pedido ${data.order_number}`;
  trackQuery('#trackingSubtitle').textContent = 'Veja em que etapa seu pedido está agora.';

  const isDelivery = data.fulfillment_method === 'ENTREGA';
  const steps = isDelivery ? DELIVERY_ORDER_STEPS : PICKUP_ORDER_STEPS;
  const statusLabel = orderLabel(data.status, data.fulfillment_method);

  trackCard.innerHTML = `
    <div class="tracking-overview"><div><span class="section-kicker">${escapeHtml(data.store.name)}</span><h2>${escapeHtml(statusLabel)}</h2><small>Atualizado em ${new Date(data.updated_at).toLocaleString('pt-BR')}</small></div><span class="customer-status ${trackStatusClass(data.status)}">${escapeHtml(statusLabel)}</span></div>
    ${progressHtml(steps, data.status, data.status === 'CANCELADO')}
    <div class="tracking-data-grid">
      <div class="tracking-data"><small>Cliente</small><strong>${escapeHtml(data.customer?.name || 'Cliente')}</strong></div>
      <div class="tracking-data"><small>Forma de recebimento</small><strong>${isDelivery ? 'Entrega' : 'Retirada'}</strong></div>
      <div class="tracking-data"><small>Data do pedido</small><strong>${new Date(data.created_at).toLocaleString('pt-BR')}</strong></div>
      ${paymentTrackHtml(data.payment)}
    </div>
    <div class="tracking-items">${orderItemsHtml(data.items)}</div>
    <div class="tracking-total"><span>Total</span><strong>${money(data.total)}</strong></div>
    <div class="tracking-account-cta"><div><b>Quer guardar seu histórico?</b><p>Crie sua conta de cliente e acompanhe seus próximos pedidos e agendamentos em um só lugar.</p></div><a class="btn primary" href="cliente.html?slug=${encodeURIComponent(trackSlug)}&modo=cadastro&tipo=pedido&token=${encodeURIComponent(trackToken)}">Criar minha conta</a></div>`;
}

async function cancelTrackedAppointment() {
  if (!confirm('Deseja realmente cancelar este agendamento?')) return;

  const button = trackQuery('#trackCancelAppointment');
  if (button) {
    button.disabled = true;
    button.textContent = 'Cancelando...';
  }

  try {
    await api(`/api/public/stores/${encodeURIComponent(trackSlug)}/appointments/${encodeURIComponent(trackToken)}/cancel`, { method: 'PATCH' });
    showToast('Agendamento cancelado.');
    await loadAppointmentTracking();
  } catch (error) {
    showToast(error.message, 'error');
    if (button) {
      button.disabled = false;
      button.textContent = 'Cancelar agendamento';
    }
  }
}

async function loadAppointmentTracking() {
  const data = await api(`/api/public/stores/${encodeURIComponent(trackSlug)}/appointments/${encodeURIComponent(trackToken)}`);
  applyTrackStore(data.store);

  document.title = `Agendamento — ${data.store.name}`;
  trackQuery('#trackingEyebrow').textContent = 'ACOMPANHAMENTO DO AGENDAMENTO';
  trackQuery('#trackingTitle').textContent = data.service.name;
  trackQuery('#trackingSubtitle').textContent = 'Consulte o horário e a situação do seu atendimento.';

  const start = new Date(data.starts_at);
  const end = new Date(data.ends_at);
  const canceled = ['CANCELADO', 'NAO_COMPARECEU'].includes(data.status);
  const statusLabel = appointmentLabel(data.status);

  trackCard.innerHTML = `
    <div class="tracking-overview"><div><span class="section-kicker">${escapeHtml(data.store.name)}</span><h2>${escapeHtml(statusLabel)}</h2></div><span class="customer-status ${trackStatusClass(data.status)}">${escapeHtml(statusLabel)}</span></div>
    ${progressHtml(APPOINTMENT_STEPS, data.status, canceled)}
    <div class="tracking-data-grid">
      <div class="tracking-data"><small>Data</small><strong>${start.toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })}</strong></div>
      <div class="tracking-data"><small>Horário</small><strong>${start.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })} – ${end.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</strong></div>
      <div class="tracking-data"><small>Profissional</small><strong>${escapeHtml(data.professional.name)}</strong></div>
      <div class="tracking-data"><small>Cliente</small><strong>${escapeHtml(data.customer?.name || 'Cliente')}</strong></div>
      ${paymentTrackHtml(data.payment)}
    </div>
    ${data.notes ? `<div class="tracking-data"><small>Observações</small><strong>${escapeHtml(data.notes)}</strong></div>` : ''}
    <div class="customer-record-actions">${data.can_cancel ? '<button id="trackCancelAppointment" class="btn danger" type="button">Cancelar agendamento</button>' : ''}</div>
    <div class="tracking-account-cta"><div><b>Tenha seus agendamentos sempre à mão.</b><p>Crie sua conta e acompanhe este e os próximos atendimentos.</p></div><a class="btn primary" href="cliente.html?slug=${encodeURIComponent(trackSlug)}&modo=cadastro&tipo=agendamento&token=${encodeURIComponent(trackToken)}">Criar minha conta</a></div>`;

  trackQuery('#trackCancelAppointment')?.addEventListener('click', cancelTrackedAppointment);
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

document.addEventListener('click', async (event) => {
  const informButton = event.target.closest('[data-inform-payment]');
  if (informButton) {
    if (!confirm('Você já concluiu o pagamento? A loja verificará o recebimento antes de confirmar.')) return;
    informButton.disabled = true;
    try {
      await api(`/api/public/stores/${encodeURIComponent(trackSlug)}/payments/${encodeURIComponent(informButton.dataset.informPayment)}/inform-paid`, { method: 'POST' });
      showToast('Pagamento informado. Aguarde a confirmação da loja.');
      if (trackType === 'APPOINTMENT') await loadAppointmentTracking(); else await loadOrderTracking();
    } catch (error) {
      informButton.disabled = false;
      showToast(error.message, 'error');
    }
    return;
  }
  const button = event.target.closest('[data-copy-tracking-pix]');
  if (!button) return;
  try { await navigator.clipboard.writeText(button.dataset.copyTrackingPix || ''); showToast('Código Pix copiado.'); }
  catch (_error) { showToast('Não foi possível copiar automaticamente.', 'error'); }
});

startTracking();
