# Mixins for testing sensor entities


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
        self.basicBSensorDeviceClass = device_class
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
            self.multiBSensorDevClass[name] = s.get("device_class")
            self.multiBSensorTestData[name] = s.get("testdata", (True, False))

    def test_multi_bsensor_device_class(self):
        for key, subject in self.multiBSensor.items():
            with self.subTest(key):
                self.assertEqual(subject.device_class, self.multiBSensorDevClass[key])

    def test_multi_bsensor_is_on(self):
        for key, subject in self.multiBSensor.items():
            with self.subTest(key):
                dps = self.multiBSensorDps[key]
                onval, offval = self.multiBSensorTestData[key]
                self.dps[dps] = onval
                self.assertTrue(subject.is_on)
                self.dps[dps] = offval
                self.assertFalse(subject.is_on)

    def test_multi_bsensor_extra_state_attributes(self):
        for key, subject in self.multiBSensor.items():
            with self.subTest(key):
                self.assertEqual(subject.extra_state_attributes, {})
