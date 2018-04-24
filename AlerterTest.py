import time, unittest
from unittest.mock import patch

from Alerter import Alerter


class AlerterTest(unittest.TestCase):

    def setUp(self):
        self.alerter = Alerter(3, 4)


    def tearDown(self):
        pass


    @patch.object(time, 'time', return_value = 8)
    def testNotEnoughEvents(self, timeMock):
        self.alerter.genAlert()
        self.assertEqual([], self.alerter.getAlerts())

        self.alerter.addEvent(6)
        self.alerter.genAlert()
        self.assertEqual([], self.alerter.getAlerts())

        self.alerter.addEvent(7)
        self.alerter.genAlert()
        self.assertEqual([], self.alerter.getAlerts())


    @patch.object(time, 'time', return_value = 8)
    def testHighAlertNotTriggered(self, timeMock):
        self.alerter.addEvent(3)  # 8 - 3 > 4 (sliding window length == 4)
        self.alerter.addEvent(4)
        self.alerter.addEvent(6)
        self.alerter.genAlert()
        self.assertEqual([], self.alerter.getAlerts())


    @patch.object(time, 'time', return_value = 8)
    def testHighAlertTriggeredAfterThreeEvents(self, timeMock):
        self.alerter.addEvent(4)
        self.alerter.addEvent(5)
        self.alerter.addEvent(7)
        self.alerter.genAlert()
        self.assertEqual([('EnterHigh', 8)], self.alerter.getAlerts())
        self.assertEqual([], self.alerter.getAlerts())  # Alerts should be cleared with each call.

        # Adding another "qualifying" event should not generate another alert.
        self.alerter.addEvent(8)
        self.alerter.genAlert()
        self.assertEqual([], self.alerter.getAlerts())

        # Recover alert.
        timeMock.return_value = 10
        self.alerter.genAlert()
        self.assertEqual([('EnterLow', 10)], self.alerter.getAlerts())

        # New alert.
        self.alerter.addEvent(9)
        self.alerter.genAlert()
        self.assertEqual([('EnterHigh', 10)], self.alerter.getAlerts())


    @patch.object(time, 'time', return_value = 8)
    def testMultipleAlerts(self, timeMock):
        self.alerter.addEvent(4)
        self.alerter.addEvent(5)
        self.alerter.addEvent(7)
        self.alerter.genAlert()  # Low -> High

        timeMock.return_value = 10
        self.alerter.addEvent(8)
        self.alerter.genAlert()  # High -> Low

        timeMock.return_value = 11
        self.alerter.addEvent(9)
        self.alerter.genAlert()  # Low -> High

        self.assertEqual([('EnterHigh', 8), ('EnterLow', 10), ('EnterHigh', 11)], self.alerter.getAlerts())


if __name__ == '__main__':
    unittest.main()
