// Auto-dismiss alerts
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s, transform 0.5s';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      setTimeout(() => alert.remove(), 500);
    }, 4000);
  });

  // Amount input formatting
  document.querySelectorAll('input[name="amount"]').forEach(input => {
    input.addEventListener('input', () => {
      const val = parseFloat(input.value);
      const preview = document.getElementById('amount-preview');
      if (preview && !isNaN(val) && val > 0) {
        preview.textContent = '৳' + val.toLocaleString('en-BD', { minimumFractionDigits: 2 });
        preview.style.display = 'block';
      } else if (preview) {
        preview.style.display = 'none';
      }
    });
  });

  // Mobile sidebar toggle
  const toggle = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
      sidebar.style.width = sidebar.style.width === '260px' ? '0' : '260px';
    });
  }

  // Confirm on freeze/unfreeze
  document.querySelectorAll('.confirm-action').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm || 'Are you sure?')) e.preventDefault();
    });
  });
});
