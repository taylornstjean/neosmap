from flask import Blueprint, render_template, request, redirect, send_from_directory
from flask_login import login_required, current_user
from .exceptions import InvalidFilterError, InvalidDatetimeError, NotAPositiveIntegerError
from .utils import verify_script_args
from neosmap.core.observation.scripting import Script
from neosmap.web_interface.models import DaemonUser
from neosmap.web_interface.main.forms import ConfigForm
from neosmap.core.exceptions import OutdatedParamsError, EphemerisParamsNotSetError
from neosmap.core.graphics import (
    generate_altaz_plot,
    generate_radec_plot,
    generate_airmass_plot,
    generate_sigmapos_plot
)
from config import (
    SCORE_COLUMNS,
    FILTERABLE_COLS,
    TEMP_SUBDIRS,
    BASE_DIR,
    MAIN_DISPLAYED_COLS,
    OVERVIEW_TABLE_COLS
)
import os

###########################################################################
# INITIALIZE BLUEPRINT

mod_main = Blueprint("main", __name__, url_prefix="/", template_folder="./templates")

###########################################################################
# DEFINE ROUTES


def _color_mode():
    if not current_user.is_authenticated:
        return "dark"
    return current_user.color_mode


@mod_main.route('/', methods=["GET"])
@login_required
def landing():
    return redirect("/data"), 308


@mod_main.route('/data', methods=["GET", "POST"])
@login_required
def data():
    cols = [col for col in MAIN_DISPLAYED_COLS if col != "objectName"]
    return render_template(
        "data.html", columns=cols, filt_cols=FILTERABLE_COLS, mode=_color_mode()
    ), 200


@mod_main.route('/settings', methods=["GET", "POST"])
@login_required
def settings():
    form = ConfigForm()
    if form.validate_on_submit():
        latitude = float(request.form["latitude"])
        longitude = float(request.form["longitude"])
        min_altitude = float(request.form["min_altitude"])
        ts_primary_mirror_diameter = float(request.form["ts_primary_mirror_diameter"])
        ts_focal_ratio = float(request.form["ts_focal_ratio"])
        current_user.config.save(
            observatory_latitude=latitude,
            observatory_longitude=longitude,
            minimum_altitude=min_altitude,
            primary_mirror_diameter=ts_primary_mirror_diameter,
            focal_ratio=ts_focal_ratio
        )
    return render_template(
        "settings.html", form=form, conf=current_user.config, mode=_color_mode()
    ), 200


@mod_main.route('/info', methods=["GET"])
@login_required
def info():
    return render_template("info.html", mode=_color_mode()), 200


@mod_main.route('/monitor', methods=["GET", "POST"])
@login_required
def monitor():
    if request.method == "POST":
        clear_update_ids = request.get_json()

        current_user.neomonitor.save_ignore_ids(clear_update_ids)

        return {"message": "Success."}, 200

    return render_template("monitor.html", mode=_color_mode()), 200


@mod_main.route('/monitor/fetch', methods=["GET"])
@login_required
def monitor_check():
    data_refresh = current_user.neomonitor.data

    updated = current_user.monitor_ping
    if updated:
        current_user.deactivate_ping()

    df = data_refresh["df"]
    table_data = df[["objectName", "nObs", "ra", "dec"]]

    updates = data_refresh["updates"]
    filtered_updates = current_user.neomonitor.sort_by_ignored(updates)

    return render_template("monitor/table.html", data=table_data, updates=filtered_updates, updated=updated), 200


@mod_main.route('/monitor/update', methods=["GET"])
def monitor_update():
    neomonitor = DaemonUser.get_neomonitor()
    neomonitor.check_update()
    return "Success", 200


@mod_main.route('/table', methods=["POST"])
@login_required
def table():
    request_json = request.get_json()
    table_data = _retrieve_table(request_json)
    return render_template("tables/table.html", data=table_data), 200


@mod_main.route('/get-column-data', methods=["GET"])
@login_required
def columns():
    payload = {"cols": [col for col in MAIN_DISPLAYED_COLS if col != "objectName"], "filterable": FILTERABLE_COLS}
    return payload, 200


@mod_main.route('/neo', methods=["GET"])
@login_required
def neoview():
    desig = request.args.to_dict().get("tdes")
    table_data = current_user.neodata.df(tdes=desig)
    return render_template(
        "neo.html", desig=desig, score_cols=SCORE_COLUMNS, data=table_data.to_dict(), mode=_color_mode()
    ), 200


@mod_main.route('/download-table', methods=["POST"])
@login_required
def download_table():
    request_json = request.get_json()
    file_type = request.args.to_dict().get("file")

    table_data = _retrieve_table(request_json)

    if file_type == "csv":
        table_data.to_csv(os.path.join(TEMP_SUBDIRS["export"], "export.csv"))
        return send_from_directory(TEMP_SUBDIRS["export"], "export.csv"), 200
    elif file_type == "json":
        table_data.to_json(os.path.join(TEMP_SUBDIRS["export"], "export.json"), orient="records")
        return send_from_directory(TEMP_SUBDIRS["export"], "export.json"), 200
    else:
        return "Bad_request", 400


@mod_main.route('/altaz-plot', methods=["GET"])
@login_required
def get_altaz_plot():
    desig = request.args.to_dict().get("tdes")
    if generate_altaz_plot(current_user.neodata, current_user.observatory, desig):
        return send_from_directory(TEMP_SUBDIRS["plot"], f"altaz-{desig}.png"), 200


@mod_main.route('/radec-plot', methods=["GET"])
@login_required
def get_radec_plot():
    desig = request.args.to_dict().get("tdes")
    if generate_radec_plot(current_user.neodata, current_user.observatory, desig):
        return send_from_directory(TEMP_SUBDIRS["plot"], f"radec-{desig}.png"), 200


@mod_main.route('/airmass-plot', methods=["GET"])
@login_required
def get_airmass_plot():
    desig = request.args.to_dict().get("tdes")
    if generate_airmass_plot(current_user.neodata, current_user.observatory, desig):
        return send_from_directory(TEMP_SUBDIRS["plot"], f"airmass-{desig}.png"), 200


@mod_main.route('/sigmapos-plot', methods=["GET"])
@login_required
def get_sigmapos_plot():
    desig = request.args.to_dict().get("tdes")
    if generate_sigmapos_plot(current_user.neodata, desig):
        return send_from_directory(TEMP_SUBDIRS["plot"], f"sigmapos-{desig}.png"), 200


@mod_main.route('/load-ephemerides', methods=["POST"])
@login_required
def load_ephemerides():
    desig = request.args.to_dict().get("tdes")

    try:
        eph_init_data = current_user.neodata.ephemerides(desig).get_data()[0]
    except (OutdatedParamsError, EphemerisParamsNotSetError):
        current_user.neodata.ephemerides(desig).set_params(defaults=True)
        eph_init_data = current_user.neodata.ephemerides(desig).get_data()[0]

    return eph_init_data, 200


@mod_main.route('/overview-table-content', methods=["POST"])
@login_required
def overview_table():
    return OVERVIEW_TABLE_COLS, 200


@mod_main.route('/get-ephemerides', methods=["POST"])
@login_required
def get_ephemerides():
    desig = request.args.to_dict().get("tdes")
    ephemeris_data = current_user.neodata.ephemerides(desig).get_data()
    return render_template("tables/eph-table.html", data=ephemeris_data), 200


@mod_main.route('/observation-script', methods=["GET"])
@login_required
def observation_script():
    request_args = request.args.to_dict()

    try:
        verify_script_args(**request_args)
    except (InvalidDatetimeError, InvalidFilterError, NotAPositiveIntegerError) as e:
        return e.message, 400

    script = Script(neo_data=current_user.neodata, observatory=current_user.observatory, **request_args, autofocus=True)
    script.generate_script()

    try:
        return send_from_directory(TEMP_SUBDIRS["script"], request_args.get("tdes") + "-observation.txt"), 200
    except FileNotFoundError:
        return "Script file not found.", 400


# Serve favicon
@mod_main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(BASE_DIR, 'static/img'),
        'comet.png',
        mimetype='image/vnd.microsoft.icon'
    ), 200


def _retrieve_table(request_args):
    cols = [col for col in request_args["colFilters"].keys() if request_args["colFilters"][col]]
    conditions = request_args["valueFilters"]
    sort_by_column = request_args["colSort"]
    visible = request_args["visible"]

    return current_user.neodata.df(
        cols=cols,
        conditions=conditions,
        sort_by_column=sort_by_column,
        visible=visible
    )

# ------------------------------ END OF FILE ------------------------------
