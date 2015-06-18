from datetime import datetime
from django.test import TestCase
from contract.models import Contract
from location.models import Area
from puser.models import PUser


class ContractTest(TestCase):

    def test_basic(self):
        u1 = PUser.get_or_create('mrzhou@umich.edu')
        area, created = Area.objects.get_or_create(name='Ann Arbor', state='MI')
        contract = Contract(buyer=u1, event_start=datetime(2015, 1, 1, 13, 0, 0), event_end=datetime(2015, 1, 1, 14, 30, 0), price=30, area=area)
        contract.save()
        self.assertEqual(20, contract.hourly_rate())
