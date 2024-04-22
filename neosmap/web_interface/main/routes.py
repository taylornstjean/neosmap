from flask import Blueprint, render_template, request, redirect, send_from_directory, logging
from flask_login import login_required, current_user
from .exceptions import InvalidFilterError, InvalidDatetimeError, NotAPositiveIntegerError
from .utils import verify_script_args
from neosmap.core.observation.scripting import Script
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
from neosmap.logger import logger

###########################################################################
# INITIALIZE BLUEPRINT

mod_main = Blueprint("main", __name__, url_prefix="/", template_folder="./templates")


###########################################################################
# DEFINE ROUTES

def _color_mode():
    """Retrieve the color setting for the user. Defaults to `"dark"` if the user is not logged in."""
    if not current_user.is_authenticated:
        return "dark"
    return current_user.color_mode


def _log_request(path) -> None:
    """Log a request to a site resource. Alternative to the Werkzeug default logger, and
    includes which user made the request."""

    logger.debug(f"User {current_user.id} made HTTP request to {path}")


@mod_main.route('/', methods=["GET"])
@login_required
def landing():
    """Handles requests to /, redirects to /data if the user is logged in."""

    return redirect("/data"), 308


@mod_main.route('/data', methods=["GET"])
@login_required
def data():
    """Handles requests to /data."""

    _log_request('/data')

    cols = [col for col in MAIN_DISPLAYED_COLS if col != "objectName"]
    return render_template(
        "data.html", columns=cols, filt_cols=FILTERABLE_COLS, mode=_color_mode()
    ), 200


@mod_main.route('/settings', methods=["GET", "POST"])
@login_required
def settings():
    """Handles requests to /settings. Accepts POST to change user settings."""

    _log_request('/settings')

    form = ConfigForm()
    if form.validate_on_submit():

        logger.debug(f"Form validated, saving config data for user {current_user.id}")

        def _request(field):
            return float(request.form[field])

        current_user.config.save(
            observatory_latitude=_request("latitude"),
            observatory_longitude=_request("longitude"),
            minimum_altitude=_request("min_altitude"),
            primary_mirror_diameter=_request("ts_primary_mirror_diameter"),
            focal_ratio=_request("ts_focal_ratio")
        )

    return render_template(
        "settings.html", form=form, conf=current_user.config, mode=_color_mode()
    ), 200


@mod_main.route('/info', methods=["GET"])
@login_required
def info():
    """Handles requests to /info."""

    _log_request('/info')

    return render_template("info.html", mode=_color_mode()), 200


@mod_main.route('/monitor', methods=["GET", "POST"])
@login_required
def monitor():
    """Handles requests to /monitor. Accepts POST for page operations (clearing update ids)."""

    _log_request('/monitor')

    if request.method == "POST":
        operation = request.args.to_dict().get("op")

        if operation == "clear-ids":
            logger.debug(f"Clearing updates on monitor page for user {current_user.id}")

            clear_update_ids = request.get_json()
            current_user.neomonitor.save_ignore_ids(clear_update_ids)
            return {"message": "Success."}, 200

        if operation == "restore-ids":
            logger.debug(f"Restoring updates on monitor page for user {current_user.id}")

            restore_update_ids = request.get_json()
            current_user.neomonitor.remove_ignore_ids(restore_update_ids)
            return {"message": "Success."}, 200

    return render_template("monitor.html", mode=_color_mode()), 200


@mod_main.route('/table', methods=["POST"])
@login_required
def table():
    """Handles requests to /table. Only accepts POST."""

    _log_request('/table')

    request_json = request.get_json()
    table_data = _retrieve_table(request_json)
    return render_template("tables/table.html", data=table_data), 200


@mod_main.route('/data/columns', methods=["GET"])
@login_required
def columns():
    """Handles requests to /data/columns."""

    _log_request('/data/columns')

    cols = {"cols": [col for col in MAIN_DISPLAYED_COLS if col != "objectName"], "filterable": FILTERABLE_COLS}
    return cols, 200


@mod_main.route('/neo', methods=["GET"])
@login_required
def neoview():
    """Handles requests to /neo. Accepts URL parameters: ``tdes`` (object temp designation)."""

    _log_request('/neo')

    desig = request.args.to_dict().get("tdes")
    table_data = current_user.neodata.df(tdes=desig)
    return render_template(
        "neo.html", desig=desig, score_cols=SCORE_COLUMNS, data=table_data.to_dict(), mode=_color_mode()
    ), 200


@mod_main.route('/data/download', methods=["POST"])
@login_required
def download_table():
    """Handles download requests to /data/download. Accepts URL parameters: ``file`` (requested file type).
    Only accepts POST."""

    _log_request('/data/download')

    request_json = request.get_json()
    file_type = request.args.to_dict().get("file")
    table_data = _retrieve_table(request_json)

    if file_type == "csv":
        logger.debug(f"User {current_user.id} requested CSV format data file")

        table_data.to_csv(os.path.join(TEMP_SUBDIRS["export"], "export.csv"))
        return send_from_directory(TEMP_SUBDIRS["export"], "export.csv"), 200

    elif file_type == "json":
        logger.debug(f"User {current_user.id} requested JSON format data file")

        table_data.to_json(os.path.join(TEMP_SUBDIRS["export"], "export.json"), orient="records")
        return send_from_directory(TEMP_SUBDIRS["export"], "export.json"), 200

    else:
        logger.debug(f"User {current_user.id} requested invalid format file")
        return "Bad_request", 400


@mod_main.route('/plot', methods=["GET"])
@login_required
def get_plot():
    """Handles requests to /plot. Accepts URL parameters: ``type`` (one of ``['altaz', 'airmass', 'sigmapos', 'radec']``)
    and ``tdes`` (object temp designation)."""

    _log_request('/plot')

    plot_type = request.args.to_dict().get("type")
    desig = request.args.to_dict().get("tdes")

    if plot_type == "altaz":
        return generate_altaz_plot(current_user.neodata, current_user.observatory, desig), 200

    elif plot_type == "radec":
        if generate_radec_plot(current_user.neodata, current_user.observatory, desig):
            return send_from_directory(TEMP_SUBDIRS["plot"], f"radec-{desig}.png"), 200

    elif plot_type == "airmass":
        return generate_airmass_plot(current_user.neodata, current_user.observatory, desig), 200

    elif plot_type == "sigmapos":
        return generate_sigmapos_plot(current_user.neodata, desig), 200

    else:
        return "Invalid plot type", 400


@mod_main.route('/ephemerides/load', methods=["POST"])
@login_required
def load_ephemerides():
    """Handles requests to /ephemerides/load. Accepts URL parameters: ``tdes`` (object temp designation).
    This is a special route used to preload ephemerides before serving content. Only accepts POST."""

    _log_request('/ephemerides/load')

    desig = request.args.to_dict().get("tdes")

    try:
        eph_init_data = current_user.neodata.ephemerides(desig).get_data()[0]
    except (OutdatedParamsError, EphemerisParamsNotSetError):
        current_user.neodata.ephemerides(desig).set_params(defaults=True)
        eph_init_data = current_user.neodata.ephemerides(desig).get_data()[0]

    logger.debug(f"Loaded ephemerides successfully")

    return eph_init_data, 200


@mod_main.route('/neo/overview-table', methods=["POST"])
@login_required
def overview_table():
    """Handles requests to /neo/overview-table. Only accepts POST."""

    _log_request('/neo/overview-table')

    return OVERVIEW_TABLE_COLS, 200


@mod_main.route('/ephemerides/fetch', methods=["POST"])
@login_required
def get_ephemerides():
    """Handles requests to /ephemerides/fetch. Accepts URL parameters: ``tdes`` (object temp designation).
    Only accepts POST."""

    _log_request('/ephemerides/fetch')

    desig = request.args.to_dict().get("tdes")

    try:
        ephemeris_data = current_user.neodata.ephemerides(desig).get_data()
    except Exception as e:
        logger.error(e)
        return "Failed to retrieve ephemeris data", 500

    return render_template("tables/eph-table.html", data=ephemeris_data), 200


@mod_main.route('/monitor/fetch', methods=["GET"])
@login_required
def monitor_fetch():
    """Handles requests to /monitor/fetch. Accepts URL parameters: ``content`` (one of ``['updates', 'table']``)."""

    _log_request('/monitor/fetch')

    content = request.args.to_dict().get("content")

    try:
        data_refresh = current_user.neomonitor.data
    except Exception as e:
        logger.error(e)
        return "Failed to retrieve neo monitor data", 500

    if content == "updates":

        updated = current_user.monitor_ping
        if updated:
            current_user.deactivate_ping()

        updates = data_refresh["updates"]
        filtered_updates = current_user.neomonitor.sort_by_ignored(updates)

        return render_template("monitor/updates.html", updates=filtered_updates, updated=updated), 200

    elif content == "table":

        df = data_refresh["df"]
        table_data = df[["objectName", "nObs", "ra", "dec"]]

        return render_template("monitor/table.html", data=table_data), 200


@mod_main.route('/observation-script', methods=["GET"])
@login_required
def observation_script():
    """Currently not in use. Handles requests to /observation-script. Accepts URL parameters:
    ``tdes`` (object temp designation)."""

    _log_request('/observation-script')

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
    """Handles requests to /favicon.ico. Used to serve favicon."""

    return send_from_directory(
        os.path.join(BASE_DIR, 'static/img'),
        'comet.png',
        mimetype='image/vnd.microsoft.icon'
    ), 200


def _retrieve_table(request_args):
    """Retrieve data from a set of request arguments."""

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
