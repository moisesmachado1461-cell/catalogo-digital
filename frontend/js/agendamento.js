const qs = new URLSearchParams(location.search);
const slug = qs.get('slug');
const token = qs.get('token');
const card = document.querySelector('#trackingCard');
const back = document.querySelector('#backStoreLink');
if (slug) back.href = `loja.html?slug=${encodeURIComponent(slug)}`;

function statusLabel(status) {
  return ({PENDENTE:'Pendente',CONFIRMADO:'Confirmado',CONCLUIDO:'Concluído',CANCELADO:'Cancelado',NAO_COMPARECEU:'Não compareceu'})[status] || status;
}

function statusClass(status) {
  return `status-${String(status || '').toLowerCase()}`;
}


function paymentHtml(payment) {
  if (!payment) return '';
  const pix = payment.method === 'PIX' ? `<div class="pix-box"><small>Chave PIX ${payment.pix_key_type ? `· ${escapeHtml(payment.pix_key_type)}` : ''}</small><div class="pix-key-row"><code>${escapeHtml(payment.pix_key || '')}</code><button id="copyAppointmentPix" class="btn ghost small" type="button">Copiar chave</button></div>${payment.pix_receiver_name ? `<small>Recebedor: ${escapeHtml(payment.pix_receiver_name)}${payment.pix_receiver_city ? ` · ${escapeHtml(payment.pix_receiver_city)}` : ''}</small>` : ''}</div>` : '';
  return `<div class="payment-track-box"><div class="payment-card"><div class="payment-card-head"><div><small>Pagamento</small><strong>${escapeHtml(payment.method_label || payment.method)}</strong></div><span class="status ${escapeHtml(payment.status)}">${escapeHtml(payment.status)}</span></div><div class="payment-amount">${money(payment.amount)}</div><p>${escapeHtml(payment.instructions || '')}</p>${pix}</div></div>`;
}

async function copyPaymentPix(value) {
  try { await navigator.clipboard.writeText(value); showToast('Chave PIX copiada.'); }
  catch (_error) { showToast('Copie a chave manualmente.', 'error'); }
}

async function loadAppointment() {
  if (!slug || !token) {
    card.innerHTML = '<div class="empty"><h2>Link incompleto</h2><p>Abra o link de acompanhamento recebido após o agendamento.</p></div>';
    return;
  }
  try {
    const data = await api(`/api/public/stores/${encodeURIComponent(slug)}/appointments/${encodeURIComponent(token)}`);
    document.title = `Agendamento — ${data.store.name}`;
    const start = new Date(data.starts_at), end = new Date(data.ends_at);
    const whatsapp = data.store.whatsapp ? String(data.store.whatsapp).replace(/\D/g,'') : '';
    card.innerHTML = `
      <div class="tracking-head"><div><span class="section-kicker">${escapeHtml(data.store.name)}</span><h2>${escapeHtml(data.service.name)}</h2></div><span class="tracking-status ${statusClass(data.status)}">${escapeHtml(statusLabel(data.status))}</span></div>
      <div class="tracking-grid">
        <div class="tracking-detail"><small>Data</small><strong>${start.toLocaleDateString('pt-BR',{weekday:'long',day:'2-digit',month:'long',year:'numeric'})}</strong></div>
        <div class="tracking-detail"><small>Horário</small><strong>${start.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})} – ${end.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})}</strong></div>
        <div class="tracking-detail"><small>Profissional</small><strong>${escapeHtml(data.professional.name)}</strong></div>
        <div class="tracking-detail"><small>Cliente</small><strong>${escapeHtml(data.customer?.name || '—')}</strong></div>
      </div>
      ${data.notes ? `<div class="tracking-notes"><small>Observações</small><p>${escapeHtml(data.notes)}</p></div>` : ''}
      ${paymentHtml(data.payment)}
      <div class="protocol-box"><small>Protocolo</small><strong>${escapeHtml(data.public_token)}</strong></div>
      <div class="booking-actions tracking-actions">
        ${whatsapp ? `<a class="btn ghost" target="_blank" rel="noopener" href="https://wa.me/${whatsapp}">Falar no WhatsApp</a>` : ''}
        ${data.can_cancel ? '<button id="cancelAppointmentBtn" class="btn danger" type="button">Cancelar agendamento</button>' : ''}
      </div>`;
    document.querySelector('#cancelAppointmentBtn')?.addEventListener('click', cancelAppointment);
    document.querySelector('#copyAppointmentPix')?.addEventListener('click', () => copyPaymentPix(data.payment?.pix_key || ''));
  } catch (error) {
    card.innerHTML = `<div class="empty"><h2>Não encontramos este agendamento</h2><p>${escapeHtml(error.message)}</p></div>`;
  }
}

async function cancelAppointment() {
  if (!confirm('Deseja realmente cancelar este agendamento?')) return;
  const button = document.querySelector('#cancelAppointmentBtn');
  if (button) { button.disabled = true; button.textContent = 'Cancelando...'; }
  try {
    await api(`/api/public/stores/${encodeURIComponent(slug)}/appointments/${encodeURIComponent(token)}/cancel`, {method:'PATCH'});
    showToast('Agendamento cancelado.');
    await loadAppointment();
  } catch (error) {
    showToast(error.message, 'error');
    if (button) { button.disabled = false; button.textContent = 'Cancelar agendamento'; }
  }
}

loadAppointment();
