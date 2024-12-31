"""The Honeywell Lyric integration."""

from __future__ import annotations
import logging

from aiolyric import Lyric
from aiolyric.objects.device import LyricDevice
from aiolyric.objects.location import LyricLocation
from aiolyric.objects.priority import LyricAccessory, LyricRoom

from .const import (
    DOMAIN,
)

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

class LyricEntity(CoordinatorEntity[DataUpdateCoordinator[Lyric]]):
    """Defines a base Honeywell Lyric entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[Lyric],
        location: LyricLocation,
        device: LyricDevice,
        key: str,
    ) -> None:
        """Initialize the Honeywell Lyric entity."""
        super().__init__(coordinator)
        self._key = key
        self._location = location
        self._mac_id = device.mac_id
        self._update_thermostat = coordinator.data.update_thermostat
        self._update_fan = coordinator.data.update_fan

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this entity."""
        return self._key

    @property
    def location(self) -> LyricLocation:
        """Get the Lyric Location."""
        return self.coordinator.data.locations_dict[self._location.location_id]

    @property
    def device(self) -> LyricDevice:
        """Get the Lyric Device."""
        return self.location.devices_dict[self._mac_id]


class LyricDeviceEntity(LyricEntity):
    """Defines a Honeywell Lyric device entity."""

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Honeywell Lyric instance."""
        return DeviceInfo(
            identifiers={(dr.CONNECTION_NETWORK_MAC, self._mac_id)},
            connections={(dr.CONNECTION_NETWORK_MAC, self._mac_id)},
            manufacturer="Honeywell",
            model=self.device.device_model,
            name=f"{self.device.name} Thermostat",
        )


class LyricAccessoryEntity(LyricDeviceEntity):
    """Defines a Honeywell Lyric accessory entity, a sub-device of a thermostat."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[Lyric],
        location: LyricLocation,
        device: LyricDevice,
        room: LyricRoom,
        accessory: LyricAccessory,
        key: str,
    ) -> None:
        """Initialize the Honeywell Lyric accessory entity."""
        super().__init__(coordinator, location, device, key)
        self._room_id = room.id
        self._accessory_id = accessory.id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Honeywell Lyric instance."""
        return DeviceInfo(
            identifiers={
                (
                    f"{dr.CONNECTION_NETWORK_MAC}_room_accessory",
                    f"{self._mac_id}_room{self._room_id}_accessory{self._accessory_id}",
                )
            },
            manufacturer="Honeywell",
            model="RCHTSENSOR",
            name=f"{self.room.room_name} Sensor",
            via_device=(dr.CONNECTION_NETWORK_MAC, self._mac_id),
        )

    @property
    def room(self) -> LyricRoom:
        """Get the Lyric Device."""
        return self.coordinator.data.rooms_dict[self._mac_id][self._room_id]

    @property
    def accessory(self) -> LyricAccessory:
        """Get the Lyric Device."""
        return next(
            accessory
            for accessory in self.room.accessories
            if accessory.id == self._accessory_id
        )


class LyricLeakEntity(CoordinatorEntity[DataUpdateCoordinator[Lyric]]):
    """Defines a Honeywell Lyric water leak entity."""

    _attr_has_entity_name = True
    has_entity_name = True  # sensor name is Softener property name ... because device exists by default
    use_device_name = False # sensor name is property name ... because device name is turned off by this flag

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[Lyric],
        location: LyricLocation,
        device: LyricDevice,
        key: str,
    ) -> None:
        """Initialize the Honeywell Lyric entity."""
        super().__init__(coordinator)
        self._key = key
        self._location = location
        self._device_id = device.device_id  # attempt to use device_id since leak doesn't have mac_id

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this entity."""
        return self._key

    @property
    def location(self) -> LyricLocation:
        """Get the Lyric Location."""
        return self.coordinator.data.locations_dict[self._location.location_id]

    @property
    def device(self) -> LyricDevice:
        """Get the Lyric Device."""
        lookup = self.location.devices_dict.get(self._device_id)
        if lookup:
            return self.location.devices_dict[self._device_id]
        else:
            _LOGGER.debug("Number of location.devices: %i", len(self.location.devices))
            for dev in self.location.devices:
                _LOGGER.debug("Comparing between: %s to %s", dev.device_id, self._device_id)
                if dev.device_id == self._device_id:
                    return dev
                else:
                    _LOGGER.debug("dev had no attribute device_id %s of len %i or didn't equal dev_id %s of len %i:", dev.device_id, len(dev.device_id), self._device_id, len(self._device_id))
                    _LOGGER.debug(dev)
                    _LOGGER.debug(dev.attributes.keys())

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Honeywell Lyric instance."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            # connections={(dr.CONNECTION_NETWORK_MAC, self._mac_id)},
            manufacturer="Honeywell",
            model=self.device.device_type,
            name=f"{self.device.attributes.get("deviceSettings", None)["userDefinedName"]} {self.device.device_type}", 
        )
