from flask import Flask, render_template
from flask_login import current_user

from neosmap.web_interface.config import DefaultConfig
from werkzeug.exceptions import HTTPException

# For import *
__all__ = ['app']


###########################################################################
# APP FACTORY

app_name = DefaultConfig.PROJECT

app = Flask(app_name, instance_relative_config=True,
            template_folder="neosmap/web_interface/main_templates")

# http://flask.pocoo.org/docs/api/#configuration
app.config.from_object(DefaultConfig)

from .extensions import db, login_manager

for ext in [db, login_manager]:
    ext.init_app(app)

# filesystem preparation/verification
from neosmap.filesystem.verify import verify_cache
from neosmap.core.caching import APICache

verify_cache()
APICache.load_instances()

from neosmap.web_interface.main import mod_main
from neosmap.web_interface.auth import mod_auth

for bp in [mod_main, mod_auth]:
    app.register_blueprint(bp)

login_manager.login_view = 'auth.login'


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

    return render_template("errors/error.html", mode=_color_mode(), error=str(code), message=name), code

# ------------------------------ END OF FILE ------------------------------
