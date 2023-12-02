"use strict";

window.onload = function() {
    initMonitor();
    initClock();
}

function initMonitor() {
    _fetchUpdate()
    setInterval(_fetchUpdate, 60000)
    function _fetchUpdate() {
        const xhrMonitor = new XMLHttpRequest();

        xhrMonitor.onreadystatechange = function() {
            if (this.readyState === 4 && this.status === 200) {
                document.getElementById("monitor-data").innerHTML = this.responseText;
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

    xhrClearUpdates.open("POST", "/monitor?clear=" + ids.join(), true);
    xhrClearUpdates.send();
}

function audioWarning(type) {
    const src = "/static/sound/";
    const notification = new Audio(src + 'alert.mp3');
    notification.play();

    let audioSpeech;
    if (type === "added") {
        audioSpeech = new Audio(src + "object_added.wav");
    } else if (type === "removed") {
        audioSpeech = new Audio(src + "object_removed.wav");
    } else if (type === "added_low_moid") {
        audioSpeech = new Audio(src + "object_added_low_moid.wav");
    } else if (type === "multiple") {
        audioSpeech = new Audio(src + "multiple_updates.wav");
    } else {
        audioSpeech = null;
    }

    if (audioSpeech) {
        audioSpeech.play();
    }
}
