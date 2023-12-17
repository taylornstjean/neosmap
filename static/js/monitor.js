"use strict";

window.onload = function() {
    initMonitor();
    initClock();
}

function initMonitor() {
    _fetchUpdate()
    setInterval(_fetchUpdate, 60000);
    function _fetchUpdate() {
        const xhrMonitor = new XMLHttpRequest();

        xhrMonitor.onreadystatechange = function() {
            if (this.readyState === 4 && this.status === 200) {
                document.getElementById("monitor-data").innerHTML = this.responseText;
                const updated = document.querySelector('meta[name="updated"]').content;
                if (updated === "True") {
                    audioWarning();
                } else if (this.readyState === 4 && this.status === 302) {
                    window.location.href = "/auth/login"
                }
            }
        }

        xhrMonitor.open("GET", "/monitor-check", true);
        xhrMonitor.send();
    }
}

function toggleOldUpdateSection() {
    $("#old-monitor-data-section").toggleClass("invisible");
}

function clearUpdates() {
    const ids = $(".current-update").map(function() {
        return this.id;
    }).get();

    const xhrClearUpdates = new XMLHttpRequest();

    xhrClearUpdates.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            location.reload();
        }
    }

    xhrClearUpdates.open("POST", "/monitor", true);
    xhrClearUpdates.setRequestHeader("Content-Type", "application/json");
    xhrClearUpdates.send(JSON.stringify(ids));
}

function audioWarning() {
    const src = "/static/sound/";
    const notification = new Audio(src + 'alert.mp3');
    notification.play();
}
