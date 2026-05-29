const _root      = document.getElementById('detailRoot');
const IMG_BASE    = _root.dataset.imgBase;
const FALLBACK_IMG = _root.dataset.fallbackImg;

let producto = null;
let cantidad  = 1;

// ── Galería ────────────────────────────────────────────────────────────────

function seleccionarThumb(index) {
  const thumbs = document.querySelectorAll('.detail-thumb');
  document.getElementById('mainImg').src = thumbs[index].src;
  thumbs.forEach(t => t.classList.remove('active'));
  thumbs[index].classList.add('active');
}

// ── Cantidad ──────────────────────────────────────────────────────────────

function cambiarCantidad(delta) {
  cantidad = Math.max(1, Math.min(producto.stock, cantidad + delta));
  document.getElementById('cantidadNum').textContent = cantidad;
}

// ── Modal ─────────────────────────────────────────────────────────────────

function abrirModal() {
  document.getElementById('modalQty').textContent   = cantidad;
  document.getElementById('modalTotal').textContent =
    '$' + (producto.precio * cantidad).toLocaleString('es-CL');
  document.getElementById('modalOverlay').classList.add('open');
}

function cerrarModal() {
  document.getElementById('modalOverlay').classList.remove('open');
}

function confirmarCarrito() {
  cerrarModal();
  window.location.href = '/carrito';
}

document.getElementById('modalOverlay').addEventListener('click', function (e) {
  if (e.target === this) cerrarModal();
});

document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') cerrarModal();
});

// ── Render ────────────────────────────────────────────────────────────────

function renderDetalle(p) {
  const imgSrc = IMG_BASE + p.imagen;

  document.title = p.nombre + ' - Peque Mundo';
  document.getElementById('breadcrumbNombre').textContent = p.nombre;

  // Imagen principal
  const mainImg = document.getElementById('mainImg');
  mainImg.src = imgSrc;
  mainImg.alt = p.nombre;
  mainImg.onerror = () => { mainImg.src = FALLBACK_IMG; };

  // Miniaturas (misma imagen repetida simulando una galería)
  document.querySelectorAll('.detail-thumb').forEach((t, i) => {
    t.src   = imgSrc;
    t.alt   = p.nombre + ' vista ' + (i + 1);
    t.onerror = () => { t.src = FALLBACK_IMG; };
  });
  document.querySelectorAll('.detail-thumb')[0].classList.add('active');

  // Info principal
  document.getElementById('detailCategoria').textContent = p.categoria;
  document.getElementById('detailNombre').textContent    = p.nombre;
  document.getElementById('detailPrecio').textContent    = '$' + p.precio.toLocaleString('es-CL');
  document.getElementById('detailDesc').textContent      = p.descripcion;

  // Stock
  const stockEl = document.getElementById('detailStock');
  if (p.stock > 0) {
    stockEl.className   = 'detail-info__stock--in';
    stockEl.textContent = '● En stock — ' + p.stock + ' unidades disponibles';
  } else {
    stockEl.className   = 'detail-info__stock--out';
    stockEl.textContent = '● Agotado';
  }

  // Ficha de características
  document.getElementById('specCategoria').textContent = p.categoria;
  document.getElementById('specStock').textContent     = p.stock > 0 ? p.stock + ' unidades' : 'Agotado';
  document.getElementById('specPrecio').textContent    = '$' + p.precio.toLocaleString('es-CL');
  document.getElementById('specId').textContent        = '#' + String(p.id).padStart(4, '0');

  // Botón carrito
  if (p.stock === 0) {
    const btn = document.getElementById('btnAgregarCarrito');
    btn.disabled    = true;
    btn.textContent = 'Sin stock';
    btn.classList.add('btn-disabled');
  }

  // Modal
  const modalImg = document.getElementById('modalImg');
  modalImg.src   = imgSrc;
  modalImg.alt   = p.nombre;
  modalImg.onerror = () => { modalImg.src = FALLBACK_IMG; };
  document.getElementById('modalNombre').textContent = p.nombre;
  document.getElementById('modalPrecio').textContent = '$' + p.precio.toLocaleString('es-CL');
}

// ── Carga desde la API ────────────────────────────────────────────────────

async function cargarProducto() {
  const id = parseInt(window.location.pathname.split('/').pop());
  try {
    const res = await fetch('/api/productos/' + id);
    if (!res.ok) throw new Error('not found');
    producto = await res.json();
    renderDetalle(producto);
  } catch {
    _root.innerHTML = '<p class="catalog-empty" style="grid-column:1/-1">Producto no encontrado. <a href="/catalogo">Volver al catálogo</a></p>';
  }
}

cargarProducto();
