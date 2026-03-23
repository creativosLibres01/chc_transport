
// Mobile menu toggle
const nav = document.getElementById('nav');
const burger = document.getElementById('hamburger');
if (burger) {
  burger.addEventListener('click', () => {
    nav.classList.toggle('open');
    burger.classList.toggle('open');
  });
}

// Modal Reserva
const modal = document.getElementById('reservaModal');
const openers = document.querySelectorAll('[data-open-reserva]');
const closers = document.querySelectorAll('[data-close-reserva]');
openers.forEach(btn => btn.addEventListener('click', (e) => {
  e.preventDefault();
  modal.classList.add('show');
}));
closers.forEach(btn => btn.addEventListener('click', () => modal.classList.remove('show')));
// Abrir modal si la URL incluye #reserva
if (location.hash === '#reserva') modal.classList.add('show');

// WhatsApp dynamic links
const wspFab = document.getElementById('wsp-fab');
const wspNumber = (wspFab?.dataset?.whatsapp || '51999999999').replace(/\D/g,'');
const wspText = encodeURIComponent('Hola, quisiera una *reserva*.');
const wspHref = `https://wa.me/${wspNumber}?text=${wspText}`;
if (wspFab) wspFab.href = wspHref;
const linkWspContacto = document.getElementById('linkWspContacto');
const linkWspModal = document.getElementById('linkWspModal');
if (linkWspContacto) linkWspContacto.href = wspHref;
if (linkWspModal) linkWspModal.href = wspHref;

// CSRF token para peticiones
function getCSRFToken(){
  return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}
function apiHeaders(){
  return {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCSRFToken()
  };
}

// Toast de feedback
function showToast(message, isError = false){
  const existing = document.getElementById('toast-msg');
  if (existing) existing.remove();
  const toast = document.createElement('div');
  toast.id = 'toast-msg';
  toast.className = 'toast-msg' + (isError ? ' toast-error' : '');
  toast.textContent = message;
  document.body.appendChild(toast);
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Helper: serialize form to JSON
function formToJSON(form){
  const fd = new FormData(form);
  return Object.fromEntries(fd.entries());
}

// Validación: fecha no pasada
function setMinDate(input){
  if (input && input.type === 'date'){
    const today = new Date().toISOString().split('T')[0];
    input.setAttribute('min', today);
  }
}

// Submit Reserva
const formReserva = document.getElementById('formReserva');
if (formReserva){
  setMinDate(formReserva.querySelector('input[name="fecha"]'));
  formReserva.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const payload = formToJSON(formReserva);
    const btn = formReserva.querySelector('button[type="submit"]');
    const originalText = btn?.textContent;
    if (btn) { btn.disabled = true; btn.textContent = 'Enviando...'; }
    try{
      const res = await fetch('/api/reservar', {method:'POST', headers: apiHeaders(), body: JSON.stringify(payload)});
      const data = await res.json();
      if (data.ok){
        showToast(data.message || '¡Reserva registrada!');
        modal.classList.remove('show');
        formReserva.reset();
      } else {
        showToast((data.errors || [data.message]).join('. ') || 'Revisa los datos.', true);
      }
    }catch(err){
      console.error(err);
      showToast('No se pudo registrar. Intenta de nuevo.', true);
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = originalText; }
    }
  });
}
// Submit Contacto
const formContacto = document.getElementById('formContacto');
if (formContacto){
  formContacto.addEventListener('submit', async (e)=>{
    e.preventDefault();
    const payload = formToJSON(formContacto);
    const btn = formContacto.querySelector('button[type="submit"]');
    const originalText = btn?.textContent;
    if (btn) { btn.disabled = true; btn.textContent = 'Enviando...'; }
    try{
      const res = await fetch('/api/contacto', {method:'POST', headers: apiHeaders(), body: JSON.stringify(payload)});
      const data = await res.json();
      if (data.ok){
        showToast(data.message || 'Mensaje enviado.');
        formContacto.reset();
      } else {
        showToast((data.errors || [data.message]).join('. ') || 'Revisa los datos.', true);
      }
    }catch(err){
      console.error(err);
      showToast('No se pudo enviar. Intenta de nuevo.', true);
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = originalText; }
    }
  });
}
