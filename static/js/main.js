"use strict";

function toggleHeaderMenuDropdown() {
    const selector = document.getElementById("header-dropdown");
    selector.classList.toggle("header__menu-dropdown-content--inactive");
    selector.classList.toggle("header__menu-dropdown-content--active");
}
