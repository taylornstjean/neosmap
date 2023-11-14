import numpy as np
from astropy import units as u
from astropy.time import Time


###########################################################################
# DEFINE IMAGE CLASS

class Image:

    def __init__(self, observatory, imaging_area, observe_time, image_center_coord=(0, 0), image_overlap=0) -> None:

        self._observatory = observatory
        self._imaging_area = imaging_area
        self._observe_time = observe_time
        self._image_center_coord = image_center_coord
        self._overlap = image_overlap

        self._image_coord_map = []

    def get_imaging_coords(self) -> list:
        """Calculates and returns coordinates for imaging locations."""

        # Initial calculations
        afov = self._observatory.afov.to(u.deg).value
        square_afov_side = afov * np.sqrt(2)
        square_afov_side_overlap = square_afov_side - (square_afov_side * self._overlap)

        origin_coord = (
            self._image_center_coord[0] - (self._imaging_area[0] / 2),
            self._image_center_coord[1] - (self._imaging_area[1] / 2)
        )

        # Calculate node counts and offsets
        node_count_x = int(np.ceil(self._imaging_area[0] / square_afov_side_overlap))
        node_count_y = int(np.ceil(self._imaging_area[1] / square_afov_side_overlap))

        x_offset = (square_afov_side_overlap - ((square_afov_side_overlap * node_count_x) - self._imaging_area[0])) / 2
        y_offset = (square_afov_side_overlap - ((square_afov_side_overlap * node_count_y) - self._imaging_area[1])) / 2

        x_offset += origin_coord[0]
        y_offset += origin_coord[1]

        # Generate node coordinate lists
        node_coords_x = [round((n * square_afov_side_overlap) + x_offset, 3) for n in range(node_count_x)]
        node_coords_y = [round((n * square_afov_side_overlap) + y_offset, 3) for n in range(node_count_y)]

        # Combine coord lists

        for x_index in range(node_count_x):
            for y_index in range(node_count_y):
                x_coord = node_coords_x[x_index]
                y_coord = node_coords_y[y_index]
                coordinate = [x_coord, y_coord]
                self._image_coord_map.append(coordinate)

        self._coordinate_wrap()
        self._check_coordinate_visibility()

        return self._image_coord_map

    def _coordinate_wrap(self) -> None:
        """Wraps coordinate values to the intervals ``0<=RA<360`` and ``-90<=DEC<=90``."""

        modified_coord_map = []
        for coord in self._image_coord_map:
            ra = coord[0]
            dec = coord[1]

            if dec < -90:
                dec = -180 - dec
                ra += 180
            if dec > 90:
                dec = 180 - dec
                ra += 180

            while ra < 0:
                ra += 360
            while ra >= 360:
                ra -= 360

            modified_coord_map.append([ra, dec])
        self._image_coord_map = modified_coord_map

    def _check_coordinate_visibility(self) -> None:
        """Checks each calculated coordinate pair for visibility at the specified observation time."""

        modified_coord_map = []
        for coord in self._image_coord_map:
            if self._observatory.check_visibility(
                    coord[0] * u.deg, coord[1] * u.deg, Time(self._observe_time)
            ):
                modified_coord_map.append(coord)
        self._image_coord_map = modified_coord_map


# ------------------------------ END OF FILE ------------------------------
