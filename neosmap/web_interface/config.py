import os
from config import BASE_DIR
from sys import platform


###########################################################################
# DEFINE APP CONFIGURATION OBJECTS

class BaseConfig(object):

    PROJECT = "NEOSMAP WI"

    # Get app root path, also can use flask.root_path.
    # ../../config.py
    PROJECT_ROOT = BASE_DIR

    DEBUG = True
    TESTING = False


class DefaultConfig(BaseConfig):

    # update to TRUE in production
    PRODUCTION = False

    if not PRODUCTION:
        SECRET_KEY = os.urandom(100)
        SQLALCHEMY_DATABASE_URI = "sqlite:///neosmap.db"
        FLASK_RUN_PORT = 5200 if platform == "darwin" else 5000
    else:
        from decouple import Config, RepositoryIni

        # setup decouple
        DOTINI_PATH = os.path.join(BASE_DIR, "..", "settings.ini")
        decouple_config = Config(RepositoryIni(DOTINI_PATH))

        SECRET_KEY = decouple_config("SECRET_KEY")
        SQLALCHEMY_DATABASE_URI = "mysql+pymysql://{user}:{password}@{host}/{database}".format(
            user=decouple_config("DB_USER"),
            password=decouple_config("DB_PASSWORD"),
            host=decouple_config("DB_HOST"),
            database=decouple_config("DB_NAME")
        )

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# ------------------------------ END OF FILE ------------------------------
