"""
Interface for the Sonnen api
- Sonnen api delivers consuming and producing data which are processed separately
- delivers consumption and production !!! from the previous day two hours behinde !!!
- constructor takes the site_id as parameter
- !!! Access by hardcoded api key !!!
"""

import requests
import datetime
from datetime import timezone
from core.abstract.input import EnergyData, Device, EnergyDataSource


# producing asset
class Sonnen(EnergyDataSource):

    def __init__(self, site_id: str, keyword: str, api_key: str, api_url: str):

        self.site = site_id
        self.api_url = api_url
        self.api_key = api_key
        self.keyword = keyword

    def read_state(self) -> EnergyData:

        raw, accumulated_power = self._get_daily_data()

        # build the device object
        device_meta = {
            'manufacturer': 'Unknown',
            'model': 'Unknown',
            'serial_number': 'Unknown',
            'geolocation': (0, 0)
        }
        device = Device(**device_meta)

        # build access_epoch
        now = datetime.datetime.now().astimezone()
        access_timestamp = now.isoformat()

        # build measurement_epoch
        measurement_timestamp = now - datetime.timedelta(hours=12)
        measurement_timestamp = measurement_timestamp.isoformat()

        return EnergyData(device, access_timestamp, raw, accumulated_power, measurement_timestamp)

    def _get_daily_data(self, days_ago=1) -> tuple:
        raw = []
        accumulated_power = 0
        for hour in range(24):
            ans, power = self._get_hourly_data(days_ago, hour)
            raw.append(ans)
            accumulated_power += power
        return raw, accumulated_power

    def _get_hourly_data(self, days_ago: int, hour: int) -> tuple:
        """
            {
                "message": "Query executed sucessfully.",
                "data": {
                    "asset_id": 101,
                    "sum_charge_kWh": 22.101,
                    "utc_offset": "01:00",
                    "sum_discharge_kWh": 11.101,
                    "requested_hour": 11,
                    "requested_date": "2018-03-27"
                }
            }
        """
        # calculate the current time and one hour back from there
        d = datetime.datetime.now(timezone.utc).astimezone()
        utc_offset = d.utcoffset()

        now = datetime.datetime.now(timezone.utc)
        start_date = now - datetime.timedelta(days=days_ago)

        marginal_query = {
            'date': str(start_date.date()),  # expects year-month-day
            'hour': hour,  # the hour of day
            'utc_offset': utc_offset,
            'asset_id': self.site
        }

        provisional_header = {"x-api-key": self.api_key}
        endpoint = self.api_url + 'charge_discharge'

        r = requests.get(endpoint, params=marginal_query, headers=provisional_header)
        ans = r.json()
        if len(ans['message']) < 1:
            raise AttributeError('Empty response from api.')
        if ans['message'] == 'Forbidden':
            raise AttributeError('Wrong auth')

        # get produced energy anc convert kWh to Watt
        power = ans['data'][self.keyword] * pow(10, 3)
        return ans, power


# consuming asset
class Sonnen_consume(Sonnen):

    def __init__(self, site_id: str, api_key: str, api_url: str):
        super().__init__(site_id=site_id, keyword='sum_charge_kWh', api_key=api_key, api_url=api_url)


# producing asset
class Sonnen_produce(Sonnen):

    def __init__(self, site_id: str, api_key: str, api_url: str):
        super().__init__(site_id=site_id, keyword='sum_discharge_kWh', api_key=api_key, api_url=api_url)


# sonne 101 consume
class Sonnen_101_c(Sonnen_consume):

    def __init__(self, api_key: str, api_url: str):
        super().__init__(site_id='101', api_key=api_key, api_url=api_url)


# sonne 101 produce
class Sonnen_101_p(Sonnen_produce):

    def __init__(self, api_key: str, api_url: str):
        super().__init__(site_id='101', api_key=api_key, api_url=api_url)


# sonne 102 consume
class Sonnen_102_c(Sonnen_consume):

    def __init__(self, api_key: str, api_url: str):
        super().__init__(site_id='102', api_key=api_key, api_url=api_url)


# sonne 102 produce
class Sonnen_102_p(Sonnen_produce):

    def __init__(self, api_key: str, api_url: str):
        super().__init__(site_id='102', api_key=api_key, api_url=api_url)


if __name__ == '__main__':
    sp1 = Sonnen_102_c()
    sp1.read_state()
    sp2 = Sonnen_102_p()
    sp2.read_state()
