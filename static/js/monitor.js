"use strict";

window.onload = function() {
    initMonitor();
    initClock();
}

function fetchUpdate() {
        const xhrMonitorTable = new XMLHttpRequest();

        xhrMonitorTable.onreadystatechange = function() {
            if (this.readyState === 4 && this.status === 200) {
                document.getElementById("m-table-section").innerHTML = this.responseText;
            } else if (this.readyState === 4 && this.status === 302) {
                    window.location.href = "/auth/login";
            }
        }

        xhrMonitorTable.open("GET", "/monitor/fetch?content=table", true);

        const clearData = document.getElementById("m-clear-data");
        let expanded = false;

        if (clearData !== null) {
            if (clearData.classList.contains("invisible") === false) {
                expanded = true;
            }
        }

        const dropdownIds = $(".m-widget-dd").map(function() {
            return this.id;
        }).get();

        let idExpanded = [];

        if (dropdownIds !== null) {
            for (let i in dropdownIds) {
                let dropdown = document.getElementById(dropdownIds[i]);
                if (dropdown.classList.contains("active-dropdown")) {
                    idExpanded.push(dropdownIds[i]);
                }
            }
        }

        const xhrMonitorUpdate = new XMLHttpRequest();

        xhrMonitorUpdate.onreadystatechange = function() {
            if (this.readyState === 4 && this.status === 200) {
                document.getElementById("m-update-section").innerHTML = this.responseText;

                if (expanded === true) {
                    toggleClearedUpdates();
                }

                for (let i in idExpanded) {
                    toggleWidgetDropdown(idExpanded[i]);
                }

                const updated = document.querySelector('meta[name="update-flag"]').content;
                if (updated === "True") {
                    audioWarning();
                }

            } else if (this.readyState === 4 && this.status === 302) {
                    window.location.href = "/auth/login";
            }
        }

        xhrMonitorUpdate.open("GET", `/monitor/fetch?content=updates`, true);

        xhrMonitorUpdate.send();
        xhrMonitorTable.send();
    }

function initMonitor() {
    fetchUpdate()
    setInterval(fetchUpdate, 60000);
}

function toggleClearedUpdates() {
    const expand = document.getElementById("monitor-expand");
    if (expand.innerHTML === "Close") {
        expand.innerHTML = "Expand";
    } else {
        expand.innerHTML = "Close";
    }

    $("#m-clear-data").toggleClass("invisible");
    $("#monitor-expand").toggleClass("selected");
}

function clearAllUpdates() {
    const ids = $(".m-widget-current").map(function() {
        return this.id;
    }).get();

    const xhrClearUpdates = new XMLHttpRequest();

    xhrClearUpdates.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            fetchUpdate();
        }
    }

    xhrClearUpdates.open("POST", "/monitor?op=clear-ids", true);
    xhrClearUpdates.setRequestHeader("Content-Type", "application/json");
    xhrClearUpdates.send(JSON.stringify(ids));
}

function clearUpdates(_id) {

    const xhrClearUpdates = new XMLHttpRequest();

    xhrClearUpdates.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            fetchUpdate();
        }
    }

    xhrClearUpdates.open("POST", "/monitor?op=clear-ids", true);
    xhrClearUpdates.setRequestHeader("Content-Type", "application/json");
    xhrClearUpdates.send(JSON.stringify([_id]));
}

function restoreUpdates(_id) {

    const xhrRestoreUpdates = new XMLHttpRequest();

    xhrRestoreUpdates.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            fetchUpdate();
        }
    }

    xhrRestoreUpdates.open("POST", "/monitor?op=restore-ids", true);
    xhrRestoreUpdates.setRequestHeader("Content-Type", "application/json");
    xhrRestoreUpdates.send(JSON.stringify([_id]));
}

function toggleWidgetDropdown(_id) {
    $(`#${_id}`).toggleClass("m-dd-active");
}

function audioWarning() {
    const src = "/static/sound/";
    const notification = new Audio(src + 'alert.mp3');
    notification.play();
}
