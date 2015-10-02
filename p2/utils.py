from datetime import date, time, datetime
import functools
import sys
import warnings
from braces.views import FormValidMessageMixin
from django.contrib import messages

from django.contrib.messages import get_messages
from django.contrib.sites.models import Site
from django.shortcuts import redirect

from django.template.loader import render_to_string
from django.utils import timezone


def get_site_url():
    current_site = Site.objects.get_current()
    return 'http://%s' % current_site.domain


def get_class(class_name):
    """
    This function gets the class from a string "class_name".
    See: http://stackoverflow.com/questions/452969/does-python-have-an-equivalent-to-java-class-forname
    :param class_name: the string of the class name
    :return: the "class" object so you can instantiate it.
    """
    parts = class_name.split('.')
    if len(parts) > 1:
        # that is, we need to import the module first.
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m
    else:
        # assuming the class is already in scope
        return getattr(sys.modules['__main__'], class_name)


def get_now():
    return timezone.now()


def process_messages(request):
    """ If messages exist, return the rendered messages string. Otherwise return none. """
    storage = get_messages(request)
    if storage:
        return '\n'.join([render_to_string('includes/message.html', {'message': message}) for message in storage])
    else:
        return None


def is_valid_email(email):
    from django.core.validators import validate_email
    try:
        validate_email(email)
        return True
    except:
        return False


def get_int(s):
    try:
        return int(s)
    except ValueError:
        return 0


def auto_user_name(email):
    """
    Given an email address, generate a random username
    """
    name = email.split('@')[0]
    from django.contrib.auth.models import User
    existing = set(User.objects.filter(username__startswith=name).values_list('username', flat=True))
    if name not in existing:
        return name
    for i in range(1000):
        new_name = '%s%d' % (name, i)
        if new_name not in existing:
            return new_name
    # last resort is to use UUID
    import uuid
    return str(uuid.uuid4())


def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""
    def new_func(*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


################# mixin ####################


class UserOnboardRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not request.puser.has_area():
            return redirect('onboard_start')
        return super().dispatch(request, *args, **kwargs)


class ControlledFormValidMessageMixin(FormValidMessageMixin):
    show_message = False

    def form_valid(self, form):
        response = super(FormValidMessageMixin, self).form_valid(form)
        if self.show_message:
            messages.success(self.request, self.get_form_valid_message(), fail_silently=True)
        return response
