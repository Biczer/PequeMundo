function formatPrecio(n) {
  return n.toLocaleString('es-CL');
}

function escaparHTML(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function resaltar(texto, palabras) {
  if (!palabras.length) return escaparHTML(texto);
  const regex = new RegExp(
    '(' + palabras.map(p => p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|') + ')',
    'gi'
  );
  return escaparHTML(texto).replace(regex, '<mark>$1</mark>');
}
