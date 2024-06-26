from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField
from wtforms.validators import InputRequired, NumberRange


###########################################################################
# FLASK FORMS

class ConfigForm(FlaskForm):
    """User settings change form."""
    longitude = FloatField(
        "Longitude",
        validators=[
            InputRequired(),
            NumberRange(min=-180, max=180, message="Longitude must be a value between -180 and 180 degrees.")
        ]
    )
    latitude = FloatField(
        "Latitude",
        validators=[
            InputRequired(),
            NumberRange(min=-90, max=90, message="Latitude must be a value between -90 and 90 degrees.")
        ]
    )

    min_altitude = FloatField(
        "Minimum Altitude (degrees)",
        validators=[
            InputRequired(),
            NumberRange(min=0, max=90, message="Altitude must be a value between 0 and 90 degrees.")
        ]
    )
    ts_primary_mirror_diameter = FloatField(
        "Primary Mirror Diameter",
        validators=[
            InputRequired(),
            NumberRange(min=0.01, max=20, message="Diameter must be a value between 0.01 and 20 meters.")
        ]
    )
    ts_focal_ratio = FloatField(
        "Focal Ratio",
        validators=[
            InputRequired(),
            NumberRange(min=0, max=100, message="Focal Ratio must be a value between 0.01 and 1000.")
        ]
    )
    submit = SubmitField("Save")

# ------------------------------ END OF FILE ------------------------------
