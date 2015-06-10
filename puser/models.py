from django.contrib.auth.models import User
from django.db import models
from image_cropping import ImageCropField, ImageRatioField
from localflavor.us.models import PhoneNumberField
from django.core import checks


@checks.register()
def email_duplicate_check(app_configs, **kwargs):
    errors = []
    if app_configs is None or 'puser' in [a.label for a in app_configs]:
        from django.contrib.auth.models import User
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute('SELECT email, COUNT(*) FROM ' + User._meta.db_table + ' GROUP BY email HAVING COUNT(*) > 1')
        rows = cursor.fetchall()
        if len(rows) > 0:
            errors.append(checks.Warning('Duplicate user email exits: %s' % len(rows)))
    return errors


class Info(models.Model):
    """
    The extended field for p2 Users.
    Authentication/authorization would be handled by user_account.
    """

    user = models.OneToOneField(User, primary_key=True)
    address = models.CharField(max_length=200, blank=True)
    phone = PhoneNumberField(blank=True)
    note = models.TextField(blank=True)

    picture_original = ImageCropField(upload_to='picture', blank=True, null=True)
    picture_cropping = ImageRatioField('picture_original', '200x200')

    from location.models import Area
    # user's home area. it doesn't necessarily mean the user will request/respond to this area only.
    area = models.ForeignKey(Area)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
