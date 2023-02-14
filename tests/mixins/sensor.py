# Mixins for testing sensor entities
from homeassistant.components.sensor import SensorDeviceClass


class BasicSensorTests:
    def setUpBasicSensor(
        self,
        dps,
        subject,
        unit=None,
        state_class=None,
        device_class=None,
        testdata=(30, 30),
    ):
        self.basicSensor = subject
        self.basicSensorDps = dps
        self.basicSensorUnit = unit
        self.basicSensorStateClass = state_class
        try:
            self.basicSensorDeviceClass = SensorDeviceClass(device_class)
        except ValueError:
            self.basicSensorDeviceClass = None

        self.basicSensorTestData = testdata

    def test_basic_sensor_units(self):
        self.assertEqual(
            self.basicSensor.native_unit_of_measurement, self.basicSensorUnit
        )

    def test_basic_sensor_device_class(self):
        self.assertEqual(self.basicSensor.device_class, self.basicSensorDeviceClass)

    def test_basic_sensor_state_class(self):
        self.assertEqual(self.basicSensor.state_class, self.basicSensorStateClass)

    def test_basic_sensor_value(self):
        dpval, val = self.basicSensorTestData
        self.dps[self.basicSensorDps] = dpval
        self.assertEqual(self.basicSensor.native_value, val)


class MultiSensorTests:
    def setUpMultiSensors(self, sensors):
        self.multiSensor = {}
        self.multiSensorDps = {}
        self.multiSensorUnit = {}
        self.multiSensorDevClass = {}
        self.multiSensorStateClass = {}
        self.multiSensorTestData = {}
        self.multiSensorOptions = {}
        for s in sensors:
            name = s.get("name")
            subject = self.entities.get(name)
            if subject is None:
                raise AttributeError(f"No sensor for {name} found.")
            self.multiSensor[name] = subject
            self.multiSensorDps[name] = s.get("dps")
            self.multiSensorUnit[name] = s.get("unit")
            self.multiSensorStateClass[name] = s.get("state_class")
            try:
                self.multiSensorDevClass[name] = SensorDeviceClass(
                    s.get("device_class")
                )
            except ValueError:
                self.multiSensorDevClass[name] = None

            self.multiSensorTestData[name] = s.get("testdata", (30, 30))
            self.multiSensorOptions[name] = s.get("options")

    def test_multi_sensor_units(self):
        for key, subject in self.multiSensor.items():
            self.assertEqual(
                subject.native_unit_of_measurement,
                self.multiSensorUnit[key],
                f"{key} unit mismatch",
            )

    def test_multi_sensor_device_class(self):
        for key, subject in self.multiSensor.items():
            self.assertEqual(
                subject.device_class,
                self.multiSensorDevClass[key],
                f"{key} device_class mismatch",
            )

    def test_multi_sensor_state_class(self):
        for key, subject in self.multiSensor.items():
            self.assertEqual(
                subject.state_class,
                self.multiSensorStateClass[key],
                f"{key} state_class mismatch",
            )

    def test_multi_sensor_value(self):
        for key, subject in self.multiSensor.items():
            dpsval, val = self.multiSensorTestData[key]
            self.dps[self.multiSensorDps[key]] = dpsval
            self.assertEqual(
                subject.native_value,
                val,
                f"{key} value mapping not as expected",
            )

    def test_multi_sensor_extra_state_attributes(self):
        for key, subject in self.multiSensor.items():
            self.assertEqual(
                subject.extra_state_attributes,
                {},
                f"{key} extra_state_attributes mismatch",
            )

    def test_multi_sensor_options(self):
        for key, subject in self.multiSensor.items():
            if self.multiSensorOptions[key]:
                self.assertCountEqual(
                    subject.options,
                    self.multiSensorOptions[key],
                    f"{key} options not as expected",
                )
            else:
                self.assertIsNone(subject.options)
