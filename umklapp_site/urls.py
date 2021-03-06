from django.conf.urls import patterns, include, url
from django.conf import settings

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView, TemplateView
from registration.backends.simple.views import RegistrationView

admin.autodiscover()

urlpatterns = [
# http://www.voidynullness.net/blog/2014/01/15/raiders-of-the-lost-django-registration-templates/
    url(r'^accounts/login/$',
                    auth_views.login,
                    {'template_name': 'umklapp/login.html'},
                    name='auth_login'),
    url(r'^accounts/logout/$',
                    auth_views.logout,
                    {'template_name': 'umklapp/logout.html'},
                    name='auth_logout'),
    url(r'^accounts/password/change/$',
                    auth_views.password_change,
                    {'template_name': 'umklapp/password_change_form.html'},
                    name='password_change'),
    url(r'^accounts/password/change/done/$',
                    auth_views.password_change_done,
                    {'template_name': 'umklapp/password_change_done.html'},
                    name='password_change_done'),

    url(r'^accounts/password/reset/$',
                    auth_views.password_reset,
                    name='password_reset'),
    url(r'^accounts/password/reset/done/$',
                    auth_views.password_reset_done,
                    name='password_reset_done'),
    url(r'^accounts/password/reset/complete/$',
                    auth_views.password_reset_complete,
                    name='password_reset_complete'),
    url(r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
                    auth_views.password_reset_confirm,
                    name='password_reset_confirm'),

    #url(r'^accounts/', include('registration.backends.simple.urls')),
    url(r'^accounts/register/$',
                    RegistrationView.as_view(template_name='umklapp/registration_form.html'),
                    name='registration_register'),
    url(r'^accounts/register/closed/$',
                    TemplateView.as_view(template_name='umklapp/registration_closed.html'),
                    name='registration_disallowed'),

    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('umklapp.urls')),
]
