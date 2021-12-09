"""
Support for the Yandex.Weather with “Weather on your site” rate.
For more details about Yandex.Weather, please refer to the documentation at
https://tech.yandex.com/weather/

"""

import asyncio
import logging

from datetime import timedelta
import voluptuous as vol
import homeassistant.util.dt as dt_util

from homeassistant.const import (
    CONF_NAME, CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, TEMP_CELSIUS, STATE_UNKNOWN)
from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION, ATTR_FORECAST_TEMP, ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_TIME, ATTR_FORECAST_PRECIPITATION, ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_WIND_SPEED, ATTR_WEATHER_PRESSURE, ATTR_WEATHER_HUMIDITY, PLATFORM_SCHEMA, WeatherEntity)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle


import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

TIME_STR_FORMAT = '%H:%M %d.%m.%Y'
DEFAULT_NAME = 'Yandex Weather'
ATTRIBUTION = 'Data provided by Yandex.Weather'

ATTR_FEELS_LIKE = 'feels_like'
ATTR_WEATHER_ICON = 'weather_icon'
ATTR_PRESSURE_MM = 'pressure_mm'
ATTR_OBS_TIME = 'observation_time'
ATTR_WEATHER_CON = 'weather_condition'
ATTR_PRECIPITATION_PROB = 'precipitation_probability'
ATTR_WIND_SPEED_MS = 'wind_speed_ms'

CONDITION_CLASSES = {
    'sunny': ['clear'],
    'partlycloudy': ['partly-cloudy'],
    'cloudy': ['cloudy', 'overcast'],
    'pouring': ['heavy-rain', 'continuous-heavy-rain', 'showers', 'hail'],
    'rainy': ['drizzle', 'light-rain', 'rain', 'moderate-rain'],
    'lightning-rainy': ['thunderstorm', 'thunderstorm-with-rain', 'thunderstorm-with-hail'],
    'snowy-rainy': ['wet-snow'],
    'snowy': ['light-snow', 'snow', 'snow-showers'],
}

DESCRIPTION_DIC = {
    'clear': 'Ясно',
    'partly-cloudy': 'Малооблачно',
    'cloudy': 'Облачно с прояснениями',
    'overcast': 'Пасмурно',
    'heavy-rain': 'Сильный дождь',
    'continuous-heavy-rain': 'Длительный сильный дождь',
    'showers': 'Ливень',
    'hail': 'Град',
    'drizzle': 'Морось',
    'light-rain': 'Небольшой дождь',
    'rain': 'Дождь',
    'moderate-rain': 'Умеренно сильный дождь',
    'thunderstorm': 'Гроза',
    'thunderstorm-with-rain': 'Дождь с грозой',
    'thunderstorm-with-hail': 'Гроза с градом',
    'wet-snow': 'Дождь со снегом',
    'snow': 'Снег',
    'snow-showers': 'Снегопад',
    'light-snow': 'Небольшой снег',
}

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Optional(CONF_LATITUDE): cv.latitude,
    vol.Optional(CONF_LONGITUDE): cv.longitude,
})


async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):

    """Set up the Yandex.Weather weather platform."""
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    async_add_entities(
        [
            YandexWeather(
                config[CONF_NAME],
                latitude+longitude,
                YaWeather(
                    async_get_clientsession(hass),
                    f"https://api.weather.yandex.ru/v2/informers?lat={latitude}&lon={longitude}",
                    {'X-Yandex-API-Key': config[CONF_API_KEY]}
                )
            )
        ],
        True
    )


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    config = config_entry.data
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    async_add_devices(
        [
            YandexWeather(
                config[CONF_NAME],
                config_entry.entry_id,
                YaWeather(
                    async_get_clientsession(hass),
                    f"https://api.weather.yandex.ru/v2/informers?lat={latitude}&lon={longitude}",
                    {'X-Yandex-API-Key': config[CONF_API_KEY]}
                )
            )
        ],
        True
    )


class YandexWeather(WeatherEntity):
    """Representation of a weather entity."""

    def __init__(self, name: str, unique_id: str, client):
        self._name = name
        self._unique_id = unique_id
        self._weather_data = client

    @property
    def unique_id(self):
        return self._unique_id

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Get the latest weather information."""
        await self._weather_data.get_weather()

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def temperature(self) -> int:
        """Return the temperature."""
        if self._weather_data.current:
            return self._weather_data.current.get('temp')
        return None

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def humidity(self) -> int:
        """Return the humidity."""
        if self._weather_data.current:
            return self._weather_data.current.get('humidity')
        return None

    @property
    def wind_speed(self) -> float:
        """Return the wind speed."""
        if self._weather_data.current:
            # Convert from m/s to km/h
            return round(self._weather_data.current.get('wind_speed') * 18 / 5)
        return None

    @property
    def wind_bearing(self) -> str:
        """Return the wind speed."""
        if self._weather_data.current:
            # The current wind bearing
            return self._weather_data.current.get('wind_dir')
        return None

    @property
    def pressure(self) -> int:
        """Return the pressure."""
        if self._weather_data.current:
            return self._weather_data.current.get('pressure_pa')
        return None

    @property
    def condition(self) -> str:
        if self._weather_data.current:
            return next((
                k for k, v in CONDITION_CLASSES.items()
                if self._weather_data.current.get('condition') in v),
                None
            )
        return STATE_UNKNOWN

    @property
    def condition_icon(self) -> int:
        """Return the pressure."""
        if self._weather_data.current:
            return self._weather_data.current.get('icon')
        return None

    @property
    def forecast(self):
        """Return the forecast array."""
        if self._weather_data.forecast:
            def extract_attributes(ordinal, data):
                return {
                    ATTR_FORECAST_TIME: dt_util.utcnow() +
                    timedelta(minutes=ordinal*350),
                    ATTR_FORECAST_TEMP: data.get('temp_max'),
                    ATTR_FORECAST_TEMP_LOW: data.get('temp_min'),
                    ATTR_FORECAST_CONDITION: next((
                        k for k, v in CONDITION_CLASSES.items()
                        if data.get('condition') in v), None),
                    ATTR_PRESSURE_MM: data.get('pressure_mm'),
                    ATTR_WEATHER_ICON: data.get('icon'),
                    ATTR_FEELS_LIKE: data.get('feels_like'),
                    ATTR_FORECAST_WIND_SPEED: round(data.get(
                        'wind_speed') * 18 / 5) if 'wind_speed' in data else None,
                    ATTR_FORECAST_WIND_BEARING: data.get('wind_dir'),
                    ATTR_FORECAST_PRECIPITATION: data.get('prec_mm'),
                    ATTR_PRECIPITATION_PROB: data.get('prec_prob'),
                    ATTR_WEATHER_CON: DESCRIPTION_DIC[data.get(
                        'condition')],
                    ATTR_WEATHER_PRESSURE: data.get('pressure_pa'),
                    ATTR_WEATHER_HUMIDITY: data.get('humidity'),
                    ATTR_WIND_SPEED_MS: data.get('wind_speed'),
                    'part_of_day': data.get('part_name')
                }
            return [
                extract_attributes(n, item)
                for n, item in
                enumerate(self._weather_data.forecast, 1)
            ]

    @property
    def attribution(self) -> str:
        """Return the attribution."""
        return ATTRIBUTION

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        if self._weather_data.current:
            return {
                ATTR_FEELS_LIKE: self._weather_data.current.get('feels_like'),
                ATTR_PRESSURE_MM: self._weather_data.current.get('pressure_mm'),
                ATTR_WIND_SPEED_MS: self._weather_data.current.get('wind_speed'),
                ATTR_WEATHER_ICON: self._weather_data.current.get('icon'),
                ATTR_OBS_TIME: dt_util.as_local(dt_util.utc_from_timestamp(
                    self._weather_data.current.get('obs_time')
                )).strftime(TIME_STR_FORMAT),
                ATTR_WEATHER_CON: DESCRIPTION_DIC[self._weather_data.current.get(
                    'condition')]
            }


class YaWeather(object):
    """A class for returning Yandex Weather data."""

    def __init__(self, session, base_url, headers):
        """Initialize the class."""
        self._session = session
        self._base_url = base_url
        self._headers = headers
        self.current = None
        self.forecast = None

    async def get_weather(self):
        try:
            data = await (await self._session.get(
                self._base_url,
                headers=self._headers,
                timeout=5
            )).json()
            if ('status' not in data):
                self.current = data.get('fact')
                self.forecast = data.get('forecast', {}).get('parts', [])
                _LOGGER.debug(f"Current data: {self.current}")
                _LOGGER.debug(f"Forecast data: {self.forecast}")
            else:
                _LOGGER.error(
                    'Error fetching data from Yandex.Weather: %s, %s', data['status'], data['message'])
        except asyncio.TimeoutError as te:
            _LOGGER.error(
                'Error fetching data from Yandex.Weather: %s', str(te))
