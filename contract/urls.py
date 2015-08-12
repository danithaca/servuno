from django.conf.urls import patterns, url
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from contract import views, forms

urlpatterns = patterns(
    "",
    url(r'^(?P<pk>\d+)/$', login_required(views.ContractDetail.as_view()), name='view'),
    url(r'^(?P<pk>\d+)/status$', views.ContractChangeStatus.as_view(), name='change_status'),

    url(r"^list/$", views.EngagementList.as_view(), name="engagement_list"),
    url(r"^add/$", views.ContractCreate.as_view(), name="add"),
    # url(r"^add/$", views.ContractCreatePreview(forms.ContractForm), name="add"),
    url(r"^(?P<pk>\d+)/edit/$", views.ContractEdit.as_view(), name="edit"),

    # only available for staff members to see all contracts.
    url(r"^$", staff_member_required(views.ContractList.as_view(), login_url=reverse_lazy('account_login')), name="list"),

    url(r'^match/(?P<pk>\d+)/$', login_required(views.MatchDetail.as_view()), name='match_view'),

    # here we use braces mixins.
    url(r'^match/(?P<pk>\d+)/accept/$', views.MatchStatusChange.as_view(switch=True), name='match_accept'),
    url(r'^match/(?P<pk>\d+)/decline/$', views.MatchStatusChange.as_view(switch=False), name='match_decline'),

    url(r'^api/my_list/$', views.APIMyEngagementList.as_view(), name='my_list'),
    url(r'^api/preview_query/$', views.ContractPreviewQuery.as_view(), name='preview_query'),
)
