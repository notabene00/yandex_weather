DOMAIN = "yandex_weather"


async def async_setup_entry(hass, entry):
    entry.async_on_unload(entry.add_update_listener(update_listener))
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "weather")
    )
    return True


async def async_remove_entry(hass, entry):
    """Unload a config entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(entry, "weather")
    except ValueError:
        pass


async def update_listener(hass, entry):
    """Update listener."""
    entry.data = entry.options
    await hass.config_entries.async_forward_entry_unload(entry, "weather")
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(entry, "weather"))
