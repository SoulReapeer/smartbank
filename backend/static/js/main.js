document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss alerts after 4s
  document.querySelectorAll('.alert').forEach(a => {
    setTimeout(() => {
      a.style.transition = 'opacity 0.5s, transform 0.5s';
      a.style.opacity = '0'; a.style.transform = 'translateY(-8px)';
      setTimeout(() => a.remove(), 500);
    }, 4000);
  });

  // Confirm actions
  document.querySelectorAll('.confirm-action').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm || 'Are you sure?')) e.preventDefault();
    });
  });

  // Pre-fill receiver account from query param ?to=ACC...
  const params = new URLSearchParams(window.location.search);
  const toAcc = params.get('to');
  if (toAcc) {
    const inp = document.getElementById('receiver-account-input');
    if (inp) inp.value = toAcc;
  }
});
