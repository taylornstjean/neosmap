from flask import Flask, render_template

from neosmap.web_interface.config import DefaultConfig

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

verify_cache()

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


# http://flask.pocoo.org/docs/latest/errorhandling/
@app.errorhandler(404)
def page_not_found(error):
    return render_template("errors/404.html"), 404

# ------------------------------ END OF FILE ------------------------------
