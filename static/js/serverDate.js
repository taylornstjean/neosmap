"use strict";

let xmlHttp;

let hidden, visibilityChange;
if (typeof document.hidden !== "undefined") {
    hidden = "hidden";
    visibilityChange = "visibilitychange";
} else if (typeof document.mozHidden !== "undefined") {
    hidden = "mozHidden";
    visibilityChange = "mozvisibilitychange";
} else if (typeof document.msHidden !== "undefined") {
    hidden = "msHidden";
    visibilityChange = "msvisibilitychange";
} else if (typeof document.webkitHidden !== "undefined") {
    hidden = "webkitHidden";
    visibilityChange = "webkitvisibilitychange";
}

function srvTime(){
    try {
        //FF, Opera, Safari, Chrome
        xmlHttp = new XMLHttpRequest();
    }
    catch (err1) {
        //IE
        try {
            xmlHttp = new ActiveXObject('Msxml2.XMLHTTP');
        }
        catch (err2) {
            try {
                xmlHttp = new ActiveXObject('Microsoft.XMLHTTP');
            }
            catch (eerr3) {
                //AJAX not supported, use CPU time.
                alert("AJAX not supported");
            }
        }
    }
    xmlHttp.open('HEAD',"/info",false);
    xmlHttp.setRequestHeader("Content-Type", "text/html");
    xmlHttp.send('');
    return xmlHttp.getResponseHeader("Date");
}

function initClock() {
    const st = srvTime();
    let date = new Date(st);
    updateClock(date)
}

function updateClock(date) {
    const clock = document.getElementById("clock");
    setClock()

    const incrementer = function() {
        incrementClock()
        const timer = setInterval(incrementClock, 1000);
        document.addEventListener(visibilityChange, function() {
            handleVisibilityHidden(timer);
        }, false);
    }

    const delay = 500;
    setTimeout(incrementer, delay);

    function incrementClock() {
        date = new Date(date.getTime() + 1000);
        setClock()
    }

    function setClock() {
        let timeArray = [date.getUTCHours(), date.getUTCMinutes(), date.getUTCSeconds()];
        let dateArray = [date.getUTCFullYear(), date.getUTCMonth() + 1, date.getUTCDate()];

        for (let i of [0, 1, 2]) {
            timeArray[i] = timeArray[i] < 10 ? "0" + timeArray[i] : timeArray[i];
            dateArray[i] = dateArray[i] < 10 ? "0" + dateArray[i] : dateArray[i];
        }

        clock.innerHTML = timeArray[0] + ":" + timeArray[1] + ":" + timeArray[2] +
            "<br><span style='font-size: 14pt;'>" + dateArray[0] + "-" + dateArray[1] + "-" + dateArray[2] + "</span>";
    }
}

function handleVisibilityVisible() {
    if (!document[hidden]) {
        initClock();
    }
}

function handleVisibilityHidden(timer) {
    if (document[hidden]) {
        clearInterval(timer);
    }
}

document.addEventListener(visibilityChange, handleVisibilityVisible, false);
