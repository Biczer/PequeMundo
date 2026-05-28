function toggleUserMenu() {
  document.getElementById('navDropdown').classList.toggle('open');
}

document.addEventListener('click', function (e) {
  const menu = document.querySelector('.nav-user-menu');
  if (menu && !menu.contains(e.target)) {
    const d = document.getElementById('navDropdown');
    if (d) d.classList.remove('open');
  }
});
