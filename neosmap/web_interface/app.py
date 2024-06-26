from flask import Flask, render_template
from flask_login import current_user
from neosmap.web_interface.config import DefaultConfig
from werkzeug.exceptions import HTTPException

# For import *
__all__ = ['app']


###########################################################################
# VERIFY SYSTEM DIRECTORY STRUCTURE

from neosmap.filesystem.verify import verify_dirs

verify_dirs()

###########################################################################
# INITIALIZE MAIN APPLICATION

app_name = DefaultConfig.PROJECT

app = Flask(app_name, instance_relative_config=True,
            template_folder="neosmap/web_interface/main_templates")

from neosmap.logger import logger

# http://flask.pocoo.org/docs/api/#configuration
app.config.from_object(DefaultConfig)

###########################################################################
# REGISTER EXTENSIONS

from .extensions import db, login_manager

for ext in [db, login_manager]:
    ext.init_app(app)

###########################################################################
# LOAD API CACHE INSTANCES

from neosmap.core.caching import APICache

APICache.load_instances()

###########################################################################
# REGISTER BLUEPRINTS

from neosmap.web_interface.main import mod_main
from neosmap.web_interface.auth import mod_auth

for bp in [mod_main, mod_auth]:
    app.register_blueprint(bp)

login_manager.login_view = 'auth.login'


###########################################################################
# CONFIGURE HANDLERS

@app.before_request
def before_request():
    with app.app_context():
        db.create_all()


@app.after_request
def apply_caching(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["HTTP-HEADER"] = "VALUE"
    return response


def _color_mode():
    if not current_user.is_authenticated:
        return "dark"
    return current_user.color_mode


# http://flask.pocoo.org/docs/latest/errorhandling/

@app.errorhandler(Exception)
def error_page(error):
    code = 500
    if isinstance(error, HTTPException):
        code = error.code

    try:
        name = error.name
    except AttributeError:
        name = error.__class__.__name__

    logger.warning(f"Code {code}; {name}")

    return render_template("errors/error.html", mode=_color_mode(), error=str(code), message=name), code


###########################################################################
# DEFINE ENTRY POINT FOR BACKGROUND JOBS

from .models import User, NEOMonitorDaemon


# cli command for backend cron job, updates monitor data via a daemon user
@app.cli.command("run-monitor")
def run_monitor() -> None:
    neomonitor = NEOMonitorDaemon(app, User)
    neomonitor.check_update()

# ------------------------------ END OF FILE ------------------------------
