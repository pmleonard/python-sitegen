function toggleMenu() {
  const hamburger = document.querySelector(".hamburger");
  const menu = document.getElementById("hmbgr_menu");

  hamburger.classList.toggle("change");
  menu.classList.toggle("menu-visible");
  menu.classList.toggle("menu-hidden");
}