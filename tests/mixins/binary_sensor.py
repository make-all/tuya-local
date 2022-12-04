# Mixins for testing sensor entities
from homeassistant.components.binary_sensor import BinarySensorDeviceClass


class BasicBinarySensorTests:
    def setUpBasicBinarySensor(
        self,
        dps,
        subject,
        device_class=None,
        testdata=(True, False),
    ):
        self.basicBSensor = subject
        self.basicBSensorDps = dps
        try:
            self.basicBSensorDeviceClass = BinarySensorDeviceClass(device_class)
        except ValueError:
            self.basicBSensorDeviceClass = None

        self.basicBSensorTestData = testdata

    def test_basic_bsensor_device_class(self):
        self.assertEqual(self.basicBSensor.device_class, self.basicBSensorDeviceClass)

    def test_basic_bsensor_is_on(self):
        onval, offval = self.basicBSensorTestData
        self.dps[self.basicBSensorDps] = onval
        self.assertTrue(self.basicBSensor.is_on)
        self.dps[self.basicBSensorDps] = offval
        self.assertFalse(self.basicBSensor.is_on)

    def test_basic_bsensor_extra_state_attributes(self):
        self.assertEqual(self.basicBSensor.extra_state_attributes, {})


class MultiBinarySensorTests:
    def setUpMultiBinarySensors(self, sensors):
        self.multiBSensor = {}
        self.multiBSensorDps = {}
        self.multiBSensorDevClass = {}
        self.multiBSensorTestData = {}
        for s in sensors:
            name = s.get("name")
            subject = self.entities.get(name)
            if subject is None:
                raise AttributeError(f"No binary sensor for {name} found.")
            self.multiBSensor[name] = subject
            self.multiBSensorDps[name] = s.get("dps")
            try:
                self.multiBSensorDevClass[name] = BinarySensorDeviceClass(
                    s.get("device_class")
                )
            except ValueError:
                self.multiBSensorDevClass[name] = None

            self.multiBSensorTestData[name] = s.get("testdata", (True, False))

    def test_multi_bsensor_device_class(self):
        for key, subject in self.multiBSensor.items():
            self.assertEqual(
                subject.device_class,
                self.multiBSensorDevClass[key],
                f"device_class mismatch in {key}",
            )

    def test_multi_bsensor_is_on(self):
        for key, subject in self.multiBSensor.items():
            dps = self.multiBSensorDps[key]
            onval, offval = self.multiBSensorTestData[key]
            self.dps[dps] = onval
            self.assertTrue(subject.is_on, f"{key} fails in ON state")
            self.dps[dps] = offval
            self.assertFalse(subject.is_on, f"{key} fails in OFF state")

    def test_multi_bsensor_extra_state_attributes(self):
        for key, subject in self.multiBSensor.items():
            self.assertEqual(
                subject.extra_state_attributes,
                {},
                f"extra_state_attributes mismatch in {key}",
            )
