(function () {
  const tableBody = document.querySelector('#items-table tbody');
  const addButton = document.querySelector('#add-item');

  if (!tableBody || !addButton) {
    return;
  }

  const ensurePlaceholder = () => {
    if (!tableBody.querySelector('tr')) {
      const placeholder = document.createElement('tr');
      placeholder.classList.add('placeholder-row');
      placeholder.innerHTML = '<td colspan="4" class="text-center text-muted">Belum ada item, klik "Tambah Item".</td>';
      tableBody.appendChild(placeholder);
    }
  };

  const removePlaceholder = () => {
    const placeholder = tableBody.querySelector('.placeholder-row');
    if (placeholder) {
      placeholder.remove();
    }
  };

  const formatCurrency = (value) => {
    const numericValue = Number(value || 0);
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 2,
    }).format(numericValue);
  };

  const renderOptions = (selectedId) => {
    const options = PRODUCTS_DATA || [];
    const optionHtml = options
      .map((product) => {
        const selected = Number(selectedId) === Number(product.id) ? 'selected' : '';
        const label = product.type ? `${product.name} (${product.type})` : product.name;
        return `<option value="${product.id}" data-price="${product.price}" ${selected}>${label}</option>`;
      })
      .join('');

    return `<option value="">-- Pilih Produk --</option>${optionHtml}`;
  };

  const attachRowEvents = (row) => {
    const productSelect = row.querySelector('[data-role="product"]');
    const priceCell = row.querySelector('[data-role="price"]');
    const removeButton = row.querySelector('[data-action="remove-item"]');

    if (productSelect) {
      productSelect.addEventListener('change', (event) => {
        const option = event.target.selectedOptions[0];
        if (option && priceCell) {
          const price = option.getAttribute('data-price');
          priceCell.textContent = price ? formatCurrency(price) : 'Rp 0,00';
        }
      });
      productSelect.dispatchEvent(new Event('change'));
    }

    if (removeButton) {
      removeButton.addEventListener('click', () => {
        row.remove();
        if (!tableBody.querySelector('tr:not(.placeholder-row)')) {
          ensurePlaceholder();
        }
      });
    }
  };

  const createRow = () => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>
        <select class="form-select" name="product_id[]" required data-role="product">
          ${renderOptions('')}
        </select>
      </td>
      <td>
        <input type="number" class="form-control text-center" name="quantity[]" min="1" value="1" required>
      </td>
      <td class="text-end" data-role="price">Rp 0,00</td>
      <td class="text-center">
        <button type="button" class="btn btn-outline-danger btn-sm" data-action="remove-item">Hapus</button>
      </td>
    `;
    return row;
  };

  addButton.addEventListener('click', () => {
    removePlaceholder();
    const newRow = createRow();
    tableBody.appendChild(newRow);
    attachRowEvents(newRow);
  });

  tableBody.querySelectorAll('tr').forEach((row) => {
    if (!row.classList.contains('placeholder-row')) {
      if (!row.querySelector('[data-role="product"]')) {
        // For existing rows rendered from server, ensure select has data attributes.
        const select = row.querySelector('select[name="product_id[]"]');
        if (select) {
          const selectedValue = select.value;
          select.innerHTML = renderOptions(selectedValue);
        }
      }
      attachRowEvents(row);
    }
  });

  ensurePlaceholder();
})();
