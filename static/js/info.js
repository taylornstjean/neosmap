"use strict";

window.onload = function() {
    initClock();
    document.getElementById("default-open").click();
};

function openContent(evt, contentName) {

    if (typeof document !== 'undefined') {

        let i, tabcontent, tablinks;


        tabcontent = document.getElementsByClassName("tab-content");
        for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
        }

        tablinks = document.getElementsByClassName("side-menu__tab-link");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" header__button--active", "");
        }

        evt.currentTarget.className += " header__button--active";
        contentName.style.display = "flex";
    }
}
