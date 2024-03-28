from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfTemperature

from ..const import IR_REMOTE_SENSORS_PAYLOAD
from ..mixins.sensor import MultiSensorTests
from .base_device_tests import TuyaDeviceTestCase

TEMP_DP = "101"
HUMID_DP = "102"
IRSEND_DP = "201"
IRRECV_DP = "202"


class TestIRRemoteSensors(MultiSensorTests, TuyaDeviceTestCase):
    __test__ = True

    def setUp(self):
        self.setUpForConfig("ir_remote_sensors.yaml", IR_REMOTE_SENSORS_PAYLOAD)
        self.subject = self.entities.get("remote")
        self.setUpMultiSensors(
            [
                {
                    "dps": TEMP_DP,
                    "name": "sensor_temperature",
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit": UnitOfTemperature.CELSIUS,
                    "state_class": "measurement",
                    "testdata": (198, 19.8),
                },
                {
                    "dps": HUMID_DP,
                    "name": "sensor_humidity",
                    "device_class": SensorDeviceClass.HUMIDITY,
                    "unit": PERCENTAGE,
                    "state_class": "measurement",
                },
            ]
        )

    # TODO: overcome issues with the HA Store in unit tests.
    # async def test_send_command(self):
    #     async with assert_device_properties_set(
    #         self.subject._device,
    #         {IRSEND_DP: '{"control": "send_ir", "head": "", "key1": "1testbutton", "type": 0, "delay": 300}'},
    #     ):
    #         await self.subject.async_send_command("b64:testbutton")
