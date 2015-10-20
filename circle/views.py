from itertools import groupby
import json

from account.mixins import LoginRequiredMixin
from braces.views import FormValidMessageMixin
from django.core.urlresolvers import reverse_lazy, reverse


# Create your views here.
from django.views.defaults import bad_request
from django.views.generic import FormView, CreateView, UpdateView
from django.views.generic.detail import SingleObjectTemplateResponseMixin, SingleObjectMixin
from circle.forms import EmailListForm, UserConnectionForm, TagUserForm, CircleForm, MembershipForm
from circle.models import Membership, Circle, ParentCircle, UserConnection
from circle.tasks import circle_send_invitation
from puser.models import PUser
from p2.utils import UserOnboardRequiredMixin, ControlledFormValidMessageMixin


class BaseCircleView(LoginRequiredMixin, UserOnboardRequiredMixin, ControlledFormValidMessageMixin, FormView):
    form_class = EmailListForm
    default_approved = None

    def get_old_email_qs(self):
        circle = self.get_circle()
        return Membership.objects.filter(circle=circle, active=True).exclude(member=self.request.puser).order_by('updated').values_list('member__email', flat=True).distinct()

    def form_valid(self, form):
        if form.has_changed() or form.cleaned_data.get('force_save', False):
            circle = self.get_circle()
            old_set = set(self.get_old_email_qs())
            # we get: dedup, valid email
            new_set = set(form.get_favorite_email_list())

            # remove old users from list if not exists
            for email in old_set - new_set:
                self.show_message = True
                target_puser = PUser.get_by_email(email)
                circle.deactivate_membership(target_puser)

            # add new user
            for email in new_set - old_set:
                self.show_message = True
                try:
                    target_puser = PUser.get_by_email(email)
                except PUser.DoesNotExist:
                    target_puser = PUser.create(email, dummy=True, area=circle.area)
                # this behaves differently for different circle type (Proxy subclass)
                circle.activate_membership(target_puser, approved=self.default_approved)
                if form.cleaned_data.get('send', False):
                    # send notification
                    # if the user is a dummy user, send invitation code instead.
                    current_user = self.request.user.to_puser()     # this is to make a separate copy of the user to prevent "change dict" error at runtime
                    circle_send_invitation.delay(circle, target_puser, current_user)

        return super().form_valid(form)

    def get_initial(self):
        initial = super().get_initial()
        email_qs = self.get_old_email_qs()
        initial['favorite'] = '\n'.join(list(email_qs))
        return initial


class ParentCircleView(BaseCircleView):
    template_name = 'circle/parent.html'
    success_url = reverse_lazy('circle:parent')
    form_valid_message = 'Parent connections successfully updated.'
    # we always set "approved" to be true here.
    default_approved = True

    def get_circle(self):
        circle = self.request.puser.my_circle(Circle.Type.PARENT)
        assert isinstance(circle, ParentCircle)
        return circle


class SitterCircleView(BaseCircleView):
    template_name = 'circle/sitter.html'
    success_url = reverse_lazy('circle:sitter')
    form_valid_message = 'Successfully updated your paid babysitter connections.'
    # we always set "approved" to be true here.
    default_approved = True

    def get_circle(self):
        circle = self.request.puser.my_circle(Circle.Type.SITTER)
        return circle

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # find babysitter pool
        me = self.request.puser
        my_parent_circle = me.my_circle(Circle.Type.PARENT)
        my_parent_list = my_parent_circle.members.filter(membership__active=True, membership__approved=True).exclude(membership__member=me)
        other_parent_sitter_circle_list = Circle.objects.filter(owner__in=my_parent_list, type=Circle.Type.SITTER.value, area=my_parent_circle.area)
        # need to sort by member in order to use groupby.
        sitter_membership_pool = Membership.objects.filter(active=True, approved=True, circle__in=other_parent_sitter_circle_list).exclude(member=me).order_by('member')
        pool_list = []
        for member, membership_list in groupby(sitter_membership_pool, lambda m: m.member):
            pool_list.append(UserConnection(me, member, list(membership_list)))
        context['pool_list'] = pool_list
        return context


class TagCircleUserView(LoginRequiredMixin, UserOnboardRequiredMixin, ControlledFormValidMessageMixin, FormView):
    form_class = TagUserForm
    template_name = 'circle/tag.html'
    success_url = reverse_lazy('circle:tag')
    form_valid_message = 'Successfully updated.'

    def form_valid(self, form):
        if form.has_changed():
            new_tags = set(form.cleaned_data['tags'])
            old_tags = set(form.initial['tags'])
            user = self.request.puser
            self.show_message = True

            for tag_circle in old_tags - new_tags:
                tag_circle.deactivate_membership(user)

            for tag_circle in new_tags - old_tags:
                tag_circle.activate_membership(user, approved=True)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_form'] = CircleForm()
        context['join_form'] = MembershipForm(initial={
            'member': self.request.puser,
            'active': True,
            'approved': True,
            'type': Membership.Type .NORMAL.value,
            'redirect': reverse('circle:tag'),
        })

        area = self.request.puser.get_area()
        mapping = {m.circle: m for m in Membership.objects.filter(circle__type=Circle.Type.TAG.value, member=self.request.puser, active=True, approved=True, circle__area=area)}
        context['all_tags'] = []
        for circle in Circle.objects.filter(type=Circle.Type.TAG.value, area=area):
            if circle in mapping:
                circle.user_membership = mapping[circle]
            context['all_tags'].append(circle)
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['target_user'] = self.request.puser
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        tags = self.request.puser.get_tag_circle_set()
        if len(tags) > 0:
            initial['tags'] = list(tags)
        return initial


class TagAddView(LoginRequiredMixin, UserOnboardRequiredMixin, CreateView):
    model = Circle
    form_class = CircleForm
    template_name = 'pages/basic_form.html'
    success_url = reverse_lazy('circle:tag')

    def form_valid(self, form):
        circle = form.instance
        circle.type = Circle.Type.TAG.value
        circle.owner = self.request.puser
        circle.area = self.request.puser.get_area()
        return super().form_valid(form)


class TagEditView(LoginRequiredMixin, UserOnboardRequiredMixin, UpdateView):
    model = Circle
    form_class = CircleForm
    template_name = 'pages/basic_form.html'

    def get_success_url(self):
        return reverse('circle:tag_view', kwargs={'pk': self.object.id})

    # def form_valid(self, form):
    #     circle = form.instance
    #     circle.type = Circle.Type.TAG.value
    #     circle.owner = self.request.puser
    #     circle.area = self.request.puser.get_area()
    #     return super().form_valid(form)


class CircleDetails(SingleObjectTemplateResponseMixin, SingleObjectMixin, BaseCircleView):
    type_constraint = None
    model = Circle
    template_name = 'circle/view.html'
    context_object_name = 'circle'

    form_valid_message = 'Added successfully.'
    # we always set "approved" to be true here.
    default_approved = True

    # we want to use DetailsView, but instead we used BaseCircleView. Therefore, here we override a little of DetailsView.get()
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if self.type_constraint is None or not isinstance(self.type_constraint, Circle.Type):
            return super().get_queryset()
        else:
            return Circle.objects.filter(type=self.type_constraint.value)

    # todo: this should move to BaseCircleView?
    def get_circle(self):
        return self.get_object()

    def get_old_email_qs(self):
        circle = self.get_circle()
        return Membership.objects.filter(circle=circle, active=True).order_by('updated').values_list('member__email', flat=True).distinct()

    def get_success_url(self):
        return reverse('circle:tag_view', kwargs={'pk': self.get_object().id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        circle = self.get_object()
        current_membership = None
        if circle.is_valid_member(self.request.puser):
            current_membership = circle.get_membership(self.request.puser)
            context['current_membership'] = current_membership

        join_form = MembershipForm(initial={
            'circle': circle,
            'member': self.request.puser,
            'active': True,
            'approved': True,
            'type': Membership.Type.NORMAL.value,
            # 'note': None if current_membership is None else current_membership.note,
        }, instance=current_membership)

        context['join_form'] = join_form
        context['edit_form'] = CircleForm(instance=circle)
        return context


class UserConnectionView(LoginRequiredMixin, FormValidMessageMixin, FormView):
    template_name = 'pages/basic_form.html'
    form_class = UserConnectionForm
    form_valid_message = 'Updated successfully.'

    def dispatch(self, request, *args, **kwargs):
        self.initiate_user = request.puser
        self.target_user = None
        try:
            self.target_user = PUser.objects.get(pk=kwargs.get('uid', None))
        except:
            pass

        if request.method.lower() == 'get' and self.target_user is None:
            return bad_request(request)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initiate_user'] = self.initiate_user
        kwargs['target_user'] = self.target_user
        return kwargs

    # def get_initial(self):
    #     initial = super().get_initial()
    #     # this is area aware.
    #     area = self.initiate_user.get_area()
    #     initial['parent_circle'] = Membership.objects.filter(member=self.target_user, circle__owner=self.initiate_user, circle__type=Circle.Type.PARENT.value, circle__area=area, active=True, approved=True).exists()
    #     initial['sitter_circle'] = Membership.objects.filter(member=self.target_user, circle__owner=self.initiate_user, circle__type=Circle.Type.SITTER.value, circle__area=area, active=True, approved=True).exists()
    #     return initial

    def form_valid(self, form):
        for field_name, circle_type in (('parent_circle', Circle.Type.PARENT), ('sitter_circle', Circle.Type.SITTER)):
            my_circle = self.initiate_user.my_circle(circle_type)
            new_value = form.cleaned_data[field_name]
            old_value = form.initial[field_name]
            if new_value != old_value:
                if new_value:
                    # todo: here we just approve.
                    my_circle.activate_membership(self.target_user, approved=True)
                else:
                    my_circle.deactivate_membership(self.target_user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('account_view', kwargs={'pk': self.target_user.id})


class MembershipUpdateView(LoginRequiredMixin, UserOnboardRequiredMixin, CreateView):
    model = Membership
    form_class = MembershipForm
    template_name = 'pages/basic_form.html'

    default_active = True
    default_approved = True
    default_type = Membership.Type.NORMAL.value

    def dispatch(self, request, *args, **kwargs):
        self.current_user = request.puser
        self.circle = None
        self.existing_membership = None

        try:
            self.circle = Circle.objects.get(pk=kwargs.get('circle_id', None))
        except:
            pass
        if self.circle is None:
            return bad_request(request)

        try:
            # set existing_memberhip if any.
            self.existing_membership = Membership.objects.get(circle=self.circle, member=self.current_user)
        except:
            pass

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # if self.existing_membership is not None:
        #     self.existing_membership.active = form.cleaned_data['active']
        #     self.existing_membership.approved = form.cleaned_data['approved']
        #     self.existing_membership.note = form.cleaned_data['note']
        #     self.existing_membership.save()
        #     # this is called by CreateView.form_valid().
        #     return super(ModelFormMixin, self).form_valid(form)
        # else:
        #     return super().form_valid(form)
        self.redirect_url = form.cleaned_data['redirect']
        if 'leave' in form.data:
            form.instance.active = False
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {
            'circle': self.circle,
            'member': self.current_user,
            'active': self.default_active,
            'approved': self.default_approved,
            'type': self.default_type,
        }
        # this will make it a "Update", not "Create".
        if self.existing_membership is not None:
            kwargs['instance'] = self.existing_membership
        return kwargs

    def get_success_url(self):
        if self.redirect_url:
            return self.redirect_url
        else:
            return reverse('circle:tag_view', kwargs={'pk': self.circle.id})