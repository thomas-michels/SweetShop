from typing import Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from app.crud.addresses.schemas import AddressInDB
from app.core.configs import get_logger

_logger = get_logger(__name__)


class Coordinator:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="pedidoz-api")

    def get_coordinates(self, address: AddressInDB) -> Tuple[float, float]:
        try:
            location = self.geolocator.geocode(
                {
                    "street": address.line_1,
                    "city": address.city,
                    "state": address.state,
                },
                timeout=10
            )

            if location:
                return (location.latitude, location.longitude)

            else:
                return None
        except (GeocoderTimedOut, GeocoderUnavailable) as error:
            _logger.error(f"Error on get coordinates: {error}")
            return None
