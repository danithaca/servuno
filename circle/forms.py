import re

from django import forms

from circle.models import Circle, SupersetRel
from location.models import Area
from s2c2.utils import is_valid_email, get_int


class ManagePersonalForm(forms.Form):
    # favorite = forms.CharField(label='Favorite', widget=forms.Textarea, required=False, help_text='One email per line.')
    favorite = forms.CharField(label='Favorite', widget=forms.HiddenInput, required=False, help_text='One email per line.')

    def clean(self):
        cleaned_data = super().clean()
        favorite = cleaned_data.get('favorite')
        cleaned_data['favorite_list'] = [e.strip() for e in re.split(r'[\s,;]+', favorite) if is_valid_email(e.strip())]
        # we don't validate for now
        # raise forms.ValidationError('')
        return cleaned_data

    def get_favorite_email_list(self):
        l = list(set(self.cleaned_data['favorite_list']))
        assert isinstance(l, list), 'Favorite email list is not initialized. Call only after cleaned form.'
        return l


# this is duplidate code to ManagePersonalForm
class SignupFavoriteForm(forms.Form):
    favorite = forms.CharField(label='Favorite', widget=forms.Textarea, required=False, help_text='One email per line.')

    def clean(self):
        cleaned_data = super(SignupFavoriteForm, self).clean()
        favorite = cleaned_data.get('favorite')
        cleaned_data['favorite_list'] = [e.strip() for e in re.split(r'[\s,;]+', favorite) if is_valid_email(e.strip())]
        # we don't validate for now
        # raise forms.ValidationError('')
        return cleaned_data


# todo: remove puser from 'init', use area instead.
class ManagePublicForm(forms.Form):
    circle = forms.CharField(widget=forms.HiddenInput, label='Circle', required=False, help_text='Separate the circle ID by commas.')

    def clean(self):
        cleaned_data = super().clean()
        circle = cleaned_data.get('circle')
        cleaned_data['circle_list'] = [int(s) for s in re.split(r'[\s,;]+', circle) if get_int(s)]
        return cleaned_data

    def get_circle_id_list(self):
        return self.cleaned_data['circle_list']

    def __init__(self, puser, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.puser = puser

        # build circle options
        self.circle_options = self.build_circle_options(puser.get_area())

    def build_circle_options(self, area):
        membership = {m.circle_id: m for m in self.puser.membership_set.filter(circle__type=Circle.Type.PUBLIC.value, active=True)}
        options = []
        for superset in Circle.objects.filter(type=Circle.Type.SUPERSET.value, area=area):
            d = {
                'title': superset.name,
                'description': superset.description,
                'list': []
            }
            for rel in SupersetRel.objects.filter(parent=superset, child__type=Circle.Type.PUBLIC.value, child__area=area):
                c = rel.child
                cd = {
                    'title': c.name,
                    'description': c.description,
                    'id': c.pk,
                }
                if c.id in membership:
                    m = membership[c.id]
                    cd['active'] = m.active
                    cd['approved'] = m.approved
                d['list'].append(cd)
            options.append(d)
        return options


# todo: this is very similar to ManageCircleForm
class SignupCircleForm(forms.Form):
    circle = forms.CharField(label='Circle', required=False, help_text='Separate the circle ID by commas.')

    def clean(self):
        cleaned_data = super(SignupCircleForm, self).clean()
        circle = cleaned_data.get('circle')
        cleaned_data['circle_list'] = [int(s) for s in re.split(r'[\s,;]+', circle) if get_int(s)]
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super(SignupCircleForm, self).__init__(*args, **kwargs)

        # build circle options
        area = Area.objects.get(pk=1)  # this is ann arbor
        self.circle_options = self.build_circle_options(area)

    def build_circle_options(self, area):
        options = []
        for superset in Circle.objects.filter(type=Circle.Type.SUPERSET.value, area=area):
            d = {
                'title': superset.name,
                'description': superset.description,
                'list': []
            }
            for rel in SupersetRel.objects.filter(parent=superset, child__type=Circle.Type.PUBLIC.value, child__area=area):
                d['list'].append({
                    'title': rel.child.name,
                    'description': rel.child.description,
                    'id': rel.child.pk,
                })
            options.append(d)
        return options

