"use strict";

window.onload = function() {
    document.getElementById("table-generator").click();
    initClock();
};

function addFilter() {
    const filter = document.getElementById("filter-selector").value;

    if (filter === "none") {
        alert("Please select a filter to add.");
        abort();
    }

    const checkForId = document.getElementById(filter + "_filterItem");

    if (checkForId) {
        abort();
    }

    const content = `
    <div id=${filter + "_filterBox"} style="margin-bottom: 15px; border: 1px solid black; border-bottom: 2px solid black; border-top: 2px solid black;">
        <div class="container-row" style="border-bottom: 1px solid black; flex-grow: 1; margin-bottom: 10px;">
            <h5 style="align-self: stretch; margin: 10px 15px; flex-grow: 1;" class="filter-label">${filter}</h5>
            <a onclick="removeFilter(${filter})" class="filter-remove">&#8212;</a>
        </div>
        <div class="container-row filter-item" id=${filter + "_filterItem"} style="margin: auto; flex-grow: 1; padding: 5px 10px 10px;">
            <div class="container-row" style="align-self: center;">
                <label for=${"min_" + filter}>Min&nbsp</label>
                <input class="filter-input" type="text" id=${"min_" + filter}>
            </div>
            <div class="container-row" style="align-self: center; margin-left: 20px;">
                <label for=${"max_" + filter}>Max&nbsp</label>
                <input class="filter-input" type="text" id=${"max_" + filter}>
            </div>
        </div>
    </div>
    `;

    document.getElementById("filter-box").innerHTML += content;
}

function removeFilter(filter) {
    const filterBox = document.getElementById(filter.value + "_filterBox");
    filterBox.remove()
}

function getFormData(response) {

    const filterList = JSON.parse(response.responseText)["filterable"];
    const filterValues = {};
    for (let filterItem of Object.keys(filterList)) {

        const filterBox = document.getElementById(filterItem + "_filterBox");
        if (! filterBox) { continue; }

        const minVal = document.getElementById("min_" + filterItem).value;
        const maxVal = document.getElementById("max_" + filterItem).value;
        if ((maxVal > filterList[filterItem]["max"] && maxVal !== "") || (minVal < filterList[filterItem]["min"] && minVal !== "")) {
            alert("Value for column " + filterItem + " must be between " + filterList[filterItem]["min"] + " and " + filterList[filterItem]["max"] + ".");
            document.getElementById("table-loader").style.display = "none";
            abort();
        }
        filterValues[filterItem] = {"ge": minVal, "le": maxVal};
    }

    const colList = JSON.parse(response.responseText)["cols"];
    const colsToDisplay = {};
    for (let col of colList) {
        colsToDisplay[col] = document.getElementById(col).checked;
    }
    const colSort = document.getElementById("sort-selector").value;
    const visible = document.getElementById("visible-selector").checked;
    const forceUpdate = document.getElementById("force-update-selector").checked;

    return {
        "colFilters": colsToDisplay,
        "valueFilters": filterValues,
        "colSort": colSort,
        "visible": visible,
        "forceUpdate": forceUpdate
    };
}


function loadDoc() {

    const loader = document.getElementById("table-loader");

    const xhrCols = new XMLHttpRequest();
    const xhrTable = new XMLHttpRequest();

    xhrTable.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            loader.style.display = "none";
            document.getElementById("data-display").innerHTML = this.responseText;
        }
    };

    xhrCols.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            const data = getFormData(this);
            xhrTable.open("POST", "/table", true);
            xhrTable.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
            xhrTable.send(JSON.stringify(data));
        }
    };

    xhrCols.open("GET", "/get-column-data", true);
    xhrCols.send();
}


function exportFile(fileType) {

    const xhrCols = new XMLHttpRequest();
    const xhrFile = new XMLHttpRequest();

    xhrFile.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            document.getElementById("table-loader").style.display = "none";
            if (fileType === "csv") {
                const blob = new Blob([this.responseText], {type: "text/csv"});
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.setAttribute("href", url);
                a.setAttribute('download', 'export.csv')
                a.click();
            }
            if (fileType === "json") {
                const blob = new Blob([this.responseText], {type: "text/json"});
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.setAttribute("href", url);
                a.setAttribute('download', 'export.json')
                a.click();
            }
        }
    };

    xhrCols.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            const data = getFormData(this);
            xhrFile.open("POST", "/download-table?file=" + fileType, true);
            xhrFile.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
            xhrFile.send(JSON.stringify(data));
        }
    };

    xhrCols.open("GET", "/get-column-data", true);
    xhrCols.send();
}
