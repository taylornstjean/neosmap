from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from flask_login import LoginManager
login_manager = LoginManager()

# from flask_talisman import Talisman
# talisman provides CSP, tends to break inline styles so disabled for now

# ------------------------------ END OF FILE ------------------------------
