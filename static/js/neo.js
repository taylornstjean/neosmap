"use strict";

window.onload = function() {
    initClock();
    document.getElementById("default-open").click();
    const desig = document.querySelector('meta[name="designation"]').content;
    loadEphemerides(desig);
};

function closePopup() {
    const popup = document.getElementById("script-popup");
    const alertBox = document.getElementById("popup-alert-box");
    popup.style.display = "none";
    alertBox.innerText = "";
}

function openPopup() {
    const popup = document.getElementById("script-popup");
    popup.style.display = "flex";
}

function loadEphemerides(desig) {
    document.body.style.cursor = "wait";
    document.getElementById("eph-loader").style.display = "flex";
    const xhr = new XMLHttpRequest();

    xhr.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            document.body.style.cursor = "auto";
            document.getElementById("eph-loader").style.display = "none";

            let i, wait_for_eph;

            wait_for_eph = document.getElementsByClassName("await-ephemerides");
            for (i = 0; i < wait_for_eph.length; i++) {
                wait_for_eph[i].style.display = "flex";
            }

            const data = JSON.parse(this.response)

            loadRadec(desig);
            loadPlots(desig);
            loadEphemerisTable(desig);
            loadVisData(desig, data);
        }
    };
    xhr.open("POST", "/ephemerides/load?tdes=" + desig, true);
    xhr.send();
}


function loadVisData(desig, data) {
    const xhr = new XMLHttpRequest();

    xhr.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            let columns = JSON.parse(this.response);

            const table = document.getElementById("vis-table");

            for (let [key, value] of Object.entries(columns)) {
                let rowCount = table.rows.length;
                let row = table.insertRow(rowCount);

                let rowTitle = row.insertCell(0);
                rowTitle.classList.add('white-text', 'table-left');

                let rowContent = row.insertCell(1);
                rowContent.classList.add('white-text');

                rowTitle.innerHTML = value;
                rowContent.innerHTML = parseFloat(data["median"][key]).toFixed(2);
            }
        }
    };

    xhr.open("POST", "/neo/overview-table?tdes=" + desig, true);
    xhr.send();

}


function loadRadec(desig) {
    document.getElementById("radec-loader").style.display = "flex";

    const container = document.getElementById("radec-box");

    const radec_img = new Image();
    radec_img.style.width = '100%';
    const radec_url = "/plot?type=radec&tdes=" + desig;

    radec_img.onload = function () {
        document.getElementById("radec-loader").style.display = "none";
        container.appendChild(radec_img);
    };

    radec_img.src = radec_url;
}


function loadPlots(desig) {
    document.getElementById("altaz-loader").style.display = "flex";
    document.getElementById("sigmapos-loader").style.display = "flex";
    document.getElementById("airmass-loader").style.display = "flex";

    const altaz_container = document.getElementById("altaz-box");
    const altaz_url = "/plot?type=altaz&tdes=" + desig;

    const xhrAltaz = new XMLHttpRequest();

    xhrAltaz.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            document.getElementById("altaz-loader").style.display = "none";
            let plot = document.createRange().createContextualFragment(this.responseText);
            altaz_container.appendChild(plot);
        }
    }

    xhrAltaz.open("GET", altaz_url, true);
    xhrAltaz.responseType = "text";
    xhrAltaz.send();

    const airmass_container = document.getElementById("airmass-box");
    const airmass_url = "/plot?type=airmass&tdes=" + desig;

    const xhrAirmass = new XMLHttpRequest();

    xhrAirmass.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            document.getElementById("airmass-loader").style.display = "none";
            let plot = document.createRange().createContextualFragment(this.responseText);
            airmass_container.appendChild(plot);
        }
    }

    xhrAirmass.open("GET", airmass_url, true);
    xhrAirmass.responseType = "text";
    xhrAirmass.send();

    const sp_container = document.getElementById("sigmapos-box");
    const sp_url = "/plot?type=sigmapos&tdes=" + desig;

    const xhrSigmapos = new XMLHttpRequest();

    xhrSigmapos.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            document.getElementById("sigmapos-loader").style.display = "none";
            let plot = document.createRange().createContextualFragment(this.responseText);
            sp_container.appendChild(plot);
        }
    }

    xhrSigmapos.open("GET", sp_url, true);
    xhrSigmapos.responseType = "text";
    xhrSigmapos.send();
}


function loadEphemerisTable(desig) {

    const xhrTable = new XMLHttpRequest();

    xhrTable.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            document.getElementById("eph-table").innerHTML = this.responseText;
        }
    };

    xhrTable.open("POST", "/ephemerides/fetch?tdes=" + desig, true);
    xhrTable.send();
}

function generateScript() {

    const desig = document.querySelector('meta[name="designation"]').content;

    const xhrScript = new XMLHttpRequest();

    const alertBox = document.getElementById("popup-alert-box")

    xhrScript.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            const blob = new Blob([this.responseText], {type: "text/txt"});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.setAttribute("href", url);
            a.setAttribute('download', desig + '_observation.acp')
            a.click();
        } else if (this.readyState === 4 && this.status === 400) {
            alertBox.innerText = this.responseText;
            openPopup()
            abort();
        }
    };

    let scriptURL = new URL("http://127.0.0.1:5257/observation-script");
    scriptURL.searchParams.set("tdes", desig);

    let filter = document.getElementById("script-filter-selector").value;
    let binning = document.getElementById("script-binning").value;
    let exposure_time = document.getElementById("script-interval").value;
    let image_delay = document.getElementById("script-imaging-interval").value;
    let blink_count = document.getElementById("script-image-count").value;
    let observe_start = document.getElementById("script-start-time").value;

    scriptURL.searchParams.set("filter", filter);
    scriptURL.searchParams.set("binning", binning);
    scriptURL.searchParams.set("exposure_time", exposure_time);
    scriptURL.searchParams.set("image_delay", image_delay);
    scriptURL.searchParams.set("blink_count", blink_count);
    scriptURL.searchParams.set("observe_start", observe_start);

    xhrScript.open("GET", scriptURL, true);
    xhrScript.send();

    closePopup();
}


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
