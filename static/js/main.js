"use strict";

function openContent(evt, contentName) {

    if (typeof document !== 'undefined') {

        let i, tabcontent, tablinks;


        tabcontent = document.getElementsByClassName("tabcontent");
        for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
        }

        tablinks = document.getElementsByClassName("tablinks");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }

        evt.currentTarget.className += " active";
        contentName.style.display = "flex";
    }
}