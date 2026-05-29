// Lee las URLs de imágenes desde data-attributes del grid (inyectadas por Jinja en el HTML)
const _grid = document.getElementById('productGrid');
const IMG_BASE    = _grid.dataset.imgBase;
const FALLBACK_IMG = _grid.dataset.fallbackImg;

let todosLosProductos = [];
let catActual = '';

// ── Render ────────────────────────────────────────────────────────────────────

function renderProductos(lista, palabras = []) {
  const grid = document.getElementById('productGrid');
  if (!lista.length) {
    grid.innerHTML = '<p class="catalog-empty">No se encontraron productos para esa búsqueda.</p>';
    return;
  }
  grid.innerHTML = lista.map((p, i) => {
    const imgSrc   = IMG_BASE + p.imagen;
    const badge    = i === 0
      ? '<span class="badge">Nuevo</span>'
      : i === 1
        ? '<span class="badge popular">Popular</span>'
        : '';
    const stockHtml = p.stock > 0
      ? `<p class="stock">● En stock (${p.stock} disponibles)</p>
         <button type="button">Agregar al carrito</button>`
      : `<p class="out-of-stock">● Agotado</p>
         <button type="button" disabled class="btn-disabled">Sin stock</button>`;
    const descCorta = p.descripcion.length > 60
      ? p.descripcion.slice(0, 60) + '...'
      : p.descripcion;

    return `
      <article class="product-card" data-nombre="${escaparHTML(p.nombre.toLowerCase())}" data-cat="${escaparHTML(p.categoria)}">
        ${badge}
        <a href="/producto/${p.id}" class="product-card__img-link">
          <img src="${imgSrc}" alt="${escaparHTML(p.nombre)}" onerror="this.src='${FALLBACK_IMG}'">
        </a>
        <h3><a href="/producto/${p.id}" class="product-card__title-link">${resaltar(p.nombre, palabras)}</a></h3>
        <p class="card-desc">${resaltar(descCorta, palabras)}</p>
        <p class="price">$${formatPrecio(p.precio)}</p>
        ${stockHtml}
        <a href="/producto/${p.id}" class="product-card__detail-link">Ver producto →</a>
      </article>`;
  }).join('');
}

// ── Búsqueda y filtrado ───────────────────────────────────────────────────────

function filtrar() {
  const input   = document.getElementById('buscador').value.toLowerCase().trim();
  const palabras = input ? input.split(/\s+/).filter(Boolean) : [];

  document.getElementById('btnLimpiar').style.display = input ? '' : 'none';

  const filtrados = todosLosProductos.filter(p => {
    const matchCat = !catActual || p.categoria === catActual;
    if (!matchCat) return false;
    if (!palabras.length) return true;
    return palabras.every(palabra =>
      p.nombre.toLowerCase().includes(palabra) ||
      p.descripcion.toLowerCase().includes(palabra) ||
      p.categoria.toLowerCase().includes(palabra)
    );
  });

  const info = document.getElementById('resultadosInfo');
  if (palabras.length) {
    info.style.display = '';
    info.textContent = filtrados.length === 1
      ? '1 producto encontrado'
      : `${filtrados.length} productos encontrados`;
  } else {
    info.style.display = 'none';
  }

  renderProductos(filtrados, palabras);
}

function limpiarBusqueda() {
  document.getElementById('buscador').value = '';
  filtrar();
  document.getElementById('buscador').focus();
}

// ── Categorías ────────────────────────────────────────────────────────────────

function setCat(btn, cat) {
  catActual = cat;
  document.querySelectorAll('.category').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  filtrar();
}

// ── Carga inicial desde la API ────────────────────────────────────────────────

async function cargarProductos() {
  try {
    const res = await fetch('/api/productos');
    todosLosProductos = await res.json();
    filtrar();
  } catch (e) {
    document.getElementById('productGrid').innerHTML =
      '<p class="catalog-empty">Error al cargar los productos.</p>';
  }
}

cargarProductos();
