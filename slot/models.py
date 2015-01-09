from django.db import models
from django.contrib.auth.models import User
from location.models import Location
import calendar


class Slot(models.Model):
    """
    Any class that has the start_time and end_time will be subclass of this.
    """
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta():
        abstract = True


class DayOfWeek(object):
    @staticmethod
    def get_tuple():
        return (calendar.MONDAY, calendar.TUESDAY, calendar.WEDNESDAY, calendar.THURSDAY, calendar.FRIDAY, calendar.SATURDAY, calendar.SUNDAY)

    @staticmethod
    def get_choices():
        return tuple((d, calendar.day_name[d]) for d in DayOfWeek.get_tuple())

    @staticmethod
    def get_set():
        return set(DayOfWeek.get_tuple())

    @staticmethod
    def get_name(dow):
        return calendar.day_name[dow]

    def __init__(self, dow):
        assert dow in DayOfWeek.get_set()
        self.dow = dow

    def prev(self):
        return DayOfWeek(DayOfWeek.get_tuple()[self.dow - 1])

    def next(self):
        return DayOfWeek(DayOfWeek.get_tuple()[(self.dow + 1) % 7])

    @property
    def name(self):
        return DayOfWeek.get_name(self.dow)


class RegularSlot(Slot):
    # todo: use python calendar.MONDAY, calendar.day_name[0] and calendar.iterweekdays() instead.
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6
    DAY_OF_WEEK = (
        (MONDAY, 'Monday'),
        (TUESDAY, 'Tuesday'),
        (WEDNESDAY, 'Wednesday'),
        (THURSDAY, 'Thursday'),
        (FRIDAY, 'Friday'),
        (SATURDAY, 'Saturday'),
        (SUNDAY, 'Sunday')
    )

    DAY_OF_WEEK_SET = set([t[0] for t in DAY_OF_WEEK])

    start_dow = models.PositiveSmallIntegerField(choices=DAY_OF_WEEK)
    # end_dow = models.PositiveSmallIntegerField(choices=DAY_OF_WEEK, blank=True, null=True)

    class Meta():
        abstract = True


class DateSlot(Slot):
    start_date = models.DateField()
    # end_date = models.DateField(blank=True, null=True)

    class Meta():
        abstract = True


class OfferInfo(models.Model):
    user = models.ForeignKey(User)

    class Meta():
        abstract = True


class NeedInfo(models.Model):
    location = models.ForeignKey(Location)

    class Meta():
        abstract = True


class OfferRegular(OfferInfo, RegularSlot):
    """
    Real class for offer on the regular schedule
    """
    pass


class OfferDate(OfferInfo, DateSlot):
    """
    Real class for offer on particular date.
    """
    pass


class NeedRegular(NeedInfo, RegularSlot):
    """
    Real class for offer on particular date.
    """
    pass


class NeedDate(NeedInfo, DateSlot):
    """
    Real class for need on particular date.
    """
    pass


class MeetInfo(models.Model):
    INACTIVE = 0
    ACTIVE = 1      # only 1 meet could be "active" that associate the same "offer" and "need".
    BACKUP = 20
    MEET_STATUS = (
        (INACTIVE, 'inactive'),
        (ACTIVE, 'active'),
        (BACKUP, 'backup'),
    )
    status = models.PositiveSmallIntegerField(choices=MEET_STATUS, default=INACTIVE)


class MeetRegular(RegularSlot):
    """
    Class that associate an offer with a need.
    Start/end time must match exactly. Or else need to break up big chunk into smaller chunks.
    """
    offer = models.ForeignKey(OfferRegular)
    need = models.ForeignKey(NeedRegular)


class MeetDate(DateSlot):
    offer = models.ForeignKey(OfferDate)
    need = models.ForeignKey(NeedDate)