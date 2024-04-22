import numpy as np
from config import OBS_TIME, TEMP_SUBDIRS, EPH_TIME_INCR
from neosmap.core.exceptions import EphemerisParamsNotSetError, OutdatedParamsError
from datetime import datetime as dt
from datetime import timedelta
import os
from astropy import units as u
from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy.time import Time
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.feature.nightshade import Nightshade
import warnings
from flask_login import current_user
import plotly.graph_objects as go

import matplotlib

# Specify matplotlib agg backend
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Specify font size
matplotlib.rcParams.update({'font.size': 8})

# Suppress matplotlib UserWarning
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

# Set image parameters
PLOT_DPI = 100


def _text_color():
    try:
        if current_user.color_mode == "light":
            return "black"
    except AttributeError:
        pass
    return "white"


###########################################################################
# INTERNAL FUNCTIONS

def _get_greenwich_sidereal_time():
    observing_time = Time(dt.utcnow(), scale='utc', location=EarthLocation.from_geodetic(lat=0, lon=0))
    sidereal = observing_time.sidereal_time('mean')
    return sidereal


def _get_ephemerides(neo_data, tdes):
    ephemeris = neo_data.ephemerides(tdes)
    try:
        ephemeris_data = ephemeris.get_data()
    except (OutdatedParamsError, EphemerisParamsNotSetError):
        ephemeris.set_params(defaults=True)
        ephemeris_data = ephemeris.get_data()
    return ephemeris_data


def _get_plotly_layout():
    layout = go.Layout(
        font_family="Ubuntu",
        height=300,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        xaxis={
            "title": "Time [UTC]",
            "mirror": True,
            "ticks": "outside",
            "showline": True,
            "gridwidth": 0.5,
            "gridcolor": "#444"
        },
        yaxis={
            "mirror": True,
            "ticks": "outside",
            "showline": True,
            "gridwidth": 0.5,
            "gridcolor": "#444"
        },
        legend={
            "x": 0.75,
            "y": 0.95,
            "bgcolor": "rgba(0, 0, 0, 0.5)"
        }
    )

    return layout


###########################################################################
# GENERATE PLOTS WITH MATPLOTLIB AND PLOTLY

def generate_radec_plot(neo_data, observatory, tdes) -> bool:

    obj_desig = tdes
    df = neo_data.df(tdes=tdes)

    ascensions = [float(o) * u.hourangle for o in df["ra"].values]
    declinations = [float(o) * u.degree for o in df["dec"].values]

    neo = SkyCoord(ascensions, declinations, frame='icrs', unit=u.deg)
    obs = SkyCoord(observatory.longitude, observatory.latitude, frame="icrs", unit=u.deg)

    # plot using matplotlib

    fig_radec = plt.figure(figsize=(6, 5))

    ax_radec = fig_radec.add_axes(111, projection=ccrs.Mercator())

    ax_radec.set_global()

    ax_radec.set_title(f"{obj_desig} Zenith Location Plot", pad=10, color=_text_color())

    ax_radec.set_xlabel('RA [deg]')
    ax_radec.set_ylabel('DEC [deg]')

    neo_zenith_longitude = (neo.ra.degree * u.deg - _get_greenwich_sidereal_time())
    observation_radius_km = (90 - observatory.min_altitude.value) * 111000 / 1000

    ax_radec.tissot(
        rad_km=observation_radius_km,
        lons=[obs.ra.degree],
        lats=[obs.dec.degree],
        facecolor="green",
        alpha=0.5,
        label="Observable Area",
        zorder=5
    )

    ax_radec.scatter(
        neo_zenith_longitude,
        neo.dec.degree,
        transform=ccrs.PlateCarree(),
        label=obj_desig,
        alpha=1,
        color="red",
        zorder=10
    )

    ax_radec.scatter(
        obs.ra.degree,
        obs.dec.degree,
        transform=ccrs.PlateCarree(),
        marker=7,
        label="Observatory",
        alpha=1,
        color="#daa520",
        zorder=10
    )

    fig_radec.patch.set_alpha(0.0)

    ax_radec.legend()

    gl = ax_radec.gridlines(
        xlocs=np.arange(-180., 181., 60.),
        ylocs=np.arange(-90., 91., 30.),
        crs=ccrs.PlateCarree(),
        draw_labels=True,
        x_inline=False,
        y_inline=False,
        dms=True,
        zorder=0
    )

    gl.ylabel_style = {'size': 8, "color": _text_color()}
    gl.xlabel_style = {'size': 8, "color": _text_color()}

    gl.top_labels = False
    gl.right_labels = False

    ax_radec.coastlines(zorder=2)
    ax_radec.add_feature(cfeature.OCEAN)
    ax_radec.add_feature(Nightshade(alpha=0.4))

    ax_radec.xaxis.label.set_color(_text_color())
    ax_radec.yaxis.label.set_color(_text_color())
    ax_radec.tick_params(axis='y', colors=_text_color())

    fig_radec.tight_layout(pad=4)

    fig_radec.savefig(os.path.join(TEMP_SUBDIRS["plot"], f"radec-{tdes}.png"), bbox_inches="tight", dpi=PLOT_DPI)

    plt.close(fig_radec)

    return True


def generate_altaz_plot(neo_data, observatory, tdes) -> str:

    ephemeris_data = _get_ephemerides(neo_data, tdes)

    start_time = dt.strptime(ephemeris_data[0]["time"], "%Y-%m-%d %X")
    t0 = Time(start_time)

    eph_ra = [float(j["median"]["ra"]) * u.degree for j in ephemeris_data]
    eph_dec = [float(j["median"]["dec"]) * u.degree for j in ephemeris_data]

    altaz_median = []

    for i, (a, d) in enumerate(zip(eph_ra, eph_dec)):
        altaz = AltAz(location=observatory.location, obstime=Time(t0 + timedelta(minutes=EPH_TIME_INCR * i)))
        coord = SkyCoord(ra=a, dec=d, frame="icrs", unit=u.deg)
        altaz_median.append(coord.transform_to(altaz).alt.degree.T)

    # plot using plotly

    time_grid = [start_time + timedelta(minutes=EPH_TIME_INCR * i) for i, _ in enumerate(eph_ra)]

    layout = _get_plotly_layout()

    data = go.Scatter(
        x=time_grid,
        y=altaz_median,
        name="Median Orbit",
        mode="lines",
        line={
            "color": "dodgerblue"
        }
    )

    fig = go.Figure(
        data=data,
        layout=layout
    )

    fig.update_layout(font=dict(color=_text_color()), title="Altitude Viewed from Observatory")
    fig.update_yaxes(color=_text_color(), title="Altitude [deg]", range=[-90, 90])
    fig.update_legends(font_color=_text_color())

    fig.add_hline(y=observatory.min_altitude.value, line_width=1, line_dash="dash", line_color="red")
    fig.update_layout(margin=dict(l=0, r=0, b=0, t=30))

    plot_html = fig.to_html()

    return plot_html


def generate_airmass_plot(neo_data, observatory, tdes) -> str:

    ephemeris_data = _get_ephemerides(neo_data, tdes)

    start_time = dt.strptime(ephemeris_data[0]["time"], "%Y-%m-%d %X")
    t0 = Time(start_time)

    eph_ra = [float(j["median"]["ra"]) * u.degree for j in ephemeris_data]
    eph_dec = [float(j["median"]["dec"]) * u.degree for j in ephemeris_data]

    airmass_median = []

    for i, (a, d) in enumerate(zip(eph_ra, eph_dec)):
        altaz = AltAz(location=observatory.location, obstime=Time(t0 + timedelta(minutes=EPH_TIME_INCR * i)))
        coord = SkyCoord(ra=a, dec=d, frame="icrs", unit=u.deg)
        altitude = coord.transform_to(altaz).alt.degree.T
        if altitude <= 0:
            airmass_median.append(100)
        else:
            airmass_median.append(1 / np.cos((90 - altitude) * (np.pi / 180)))

    # plot using plotly

    time_grid = [start_time + timedelta(minutes=EPH_TIME_INCR * i) for i, _ in enumerate(eph_ra)]

    layout = _get_plotly_layout()

    data = go.Scatter(
        x=time_grid,
        y=airmass_median,
        name="Median Orbit",
        mode="lines",
        line={
            "color": "dodgerblue"
        }
    )

    fig = go.Figure(
        data=data,
        layout=layout
    )

    fig.update_layout(font=dict(color=_text_color()), title="Airmass Viewed from Observatory")
    fig.update_yaxes(color=_text_color(), title="Airmass", range=[0, 10])
    fig.update_legends(font_color=_text_color())

    fig.update_layout(margin=dict(l=0, r=0, b=0, t=30))

    plot_html = fig.to_html()

    return plot_html


def generate_sigmapos_plot(neo_data, tdes) -> str:

    ephemeris_data = _get_ephemerides(neo_data, tdes)

    start_time = dt.strptime(ephemeris_data[0]["time"], "%Y-%m-%d %X")

    sigmapos_median = [float(i["sigma-pos"]) for i in ephemeris_data]

    # plot using plotly

    time_grid = [start_time + timedelta(minutes=EPH_TIME_INCR * i) for i, _ in enumerate(ephemeris_data)]

    layout = _get_plotly_layout()

    data = go.Scatter(
        x=time_grid,
        y=sigmapos_median,
        name="Median Orbit",
        mode="lines",
        line={
            "color": "dodgerblue"
        }
    )

    fig = go.Figure(
        data=data,
        layout=layout
    )

    fig.update_layout(font=dict(color=_text_color()), title="1-Sigma Position Uncertainty")
    fig.update_yaxes(color=_text_color(), title="Uncertainty [arcmin]", range=[0, max(sigmapos_median) * 1.2])
    fig.update_legends(font_color=_text_color())

    fig.update_layout(margin=dict(l=0, r=0, b=0, t=30))

    plot_html = fig.to_html()

    return plot_html


# ------------------------------ END OF FILE ------------------------------
