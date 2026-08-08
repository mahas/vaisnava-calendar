from .GCLocation import GCLocation

class TLocation(GCLocation):
    """
    Location class wrapper for Vaishnava Calendar engine calculations.
    Accepts latitude, longitude, timezone keyword arguments.
    """
    def __init__(self, latitude=None, longitude=None, timezone=None, tzname=None, name=None, **kwargs):
        tz = timezone or tzname
        super().__init__(latitude=latitude, longitude=longitude, tzname=tz, name=name, **kwargs)
