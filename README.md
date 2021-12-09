# Yandex Weather custom component for Home-assistant
This is custom component for Home-assistant. 
Component work with Home-assistant starting 0.92 or later.

# Installation

## Copying files

Create a directory called `yandex_weather` in the `<config directory>/custom_components/` directory on your Home Assistant instance.
Install this component by copying the files in [`/custom_components/yandex_weather/`] from this repo into the new `<config directory>/custom_components/yandex_weather/` directory you just created.

## HACS

Add this repository to custom repositories, then install like usually do.

# CONFIGURATION

## YAML

Add this to your `configuration.yaml`

```yaml
weather:
  - platform: yandex_weather
    api_key: <yandex_api_key>
    latitude: 53
    longitude: 38
```

Latitude and longitude are optional. 
If not defined, HAssIO home zone coordinates will be used.

## UI Config flow
This component supports configuration via Home Assistant UI.

Go to `Settings` -> `Integrations` -> `Add`.
Search for `Yandex Weather`, select it and fill all the fields.