from neosmap.web_interface.extensions import db, login_manager
from flask_login import UserMixin, current_user
from astropy import units as u
from neosmap.core.data import NEOData, Observatory

from neosmap.web_interface.utils import get_current_time


class User(db.Model, UserMixin):

    __tablename__ = "user"

    id = db.Column(db.Integer, unique=True, primary_key=True)
    password = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(256), nullable=False, unique=True)
    created_on = db.Column(db.DateTime, nullable=False, default=get_current_time())

    color_mode = "dark"

    def save(self, password, email, **kwargs):

        self.password = password
        self.email = email
        self.created_on = kwargs.get("created_on", get_current_time())

        db.session.add(self)
        db.session.commit()

        self._init_config()

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the id to satisfy Flask-Login's requirements."""
        return self.id

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

    def _init_config(self):
        new_config = Config(user_id=self.id)
        new_config.commit()

    def _load_config(self):
        self._config = Config.query.filter(Config.owner == int(self.id)).first()

    @property
    def config(self):
        if not hasattr(self, "_config"):
            self._load_config()
        return self._config

    def _initialize_observatory_instance(self):
        self._observatory = Observatory(
            longitude=self.config.observatory_longitude * u.degree,
            latitude=self.config.observatory_latitude * u.degree,
            ts_mirror_diameter=self.config.primary_mirror_diameter * u.m,
            ts_focal_ratio=self.config.focal_ratio,
            min_altitude=self.config.minimum_altitude * u.degree
        )

    @property
    def observatory(self):
        if not hasattr(self, "_observatory"):
            self._initialize_observatory_instance()
        return self._observatory

    def _initialize_neodata_instance(self):
        self._neodata = NEOData(self.observatory)
        self._neodata.check_update(force_update=True)

    @property
    def neodata(self):
        if not hasattr(self, "_neodata"):
            self._initialize_neodata_instance()
        return self._neodata

    def wipe_instances(self):
        if hasattr(self, "_neodata"):
            del self._neodata
        if hasattr(self, "_observatory"):
            del self._observatory


class Config(db.Model):

    __tablename__ = "config"

    __default_observatory_latitude = 32.7795337
    __default_observatory_longitude = -105.8194667
    __default_minimum_altitude = 27
    __default_focal_ratio = 8
    __default_mirror_diameter = 0.5

    owner = db.Column(db.Integer, unique=True, primary_key=True)
    observatory_latitude = db.Column(db.Float, nullable=False, default=__default_observatory_latitude)
    observatory_longitude = db.Column(db.Float, nullable=False, default=__default_observatory_longitude)
    minimum_altitude = db.Column(db.Float, nullable=False, default=__default_minimum_altitude)
    primary_mirror_diameter = db.Column(db.Float, nullable=False, default=__default_mirror_diameter)
    focal_ratio = db.Column(db.Float, nullable=False, default=__default_focal_ratio)

    def __init__(self, user_id):
        self.owner = user_id

    def commit(self):
        db.session.add(self)
        db.session.commit()

    def save(self, **kwargs):
        self.observatory_latitude = kwargs.get("observatory_latitude", self.observatory_latitude)
        self.observatory_longitude = kwargs.get("observatory_longitude", self.observatory_longitude)
        self.minimum_altitude = kwargs.get("minimum_altitude", self.minimum_altitude)
        self.primary_mirror_diameter = kwargs.get("primary_mirror_diameter", self.primary_mirror_diameter)
        self.focal_ratio = kwargs.get("focal_ratio", self.focal_ratio)

        db.session.add(self)
        db.session.commit()

        current_user.wipe_instances()

    def get_owner(self):
        """Return the owner id."""
        return self.owner


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == int(user_id)).first()
