from django.conf.urls import include, url
from django.conf import settings

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView, TemplateView
from django_registration.backends.one_step.views import RegistrationView

admin.autodiscover()

urlpatterns = [
# http://www.voidynullness.net/blog/2014/01/15/raiders-of-the-lost-django-registration-templates/
    url(r'^accounts/', include('django_registration.backends.one_step.urls')),
    url(r'^accounts/login/$',
                    auth_views.LoginView.as_view(
                    template_name = 'umklapp/login.html'),
                    name='auth_login'),
    url(r'^accounts/logout/$',
                    auth_views.LogoutView.as_view(
                    template_name = 'umklapp/logout.html'),
                    name='auth_logout'),
    url(r'^accounts/password/change/$',
                    auth_views.PasswordChangeView,
                    {'template_name': 'umklapp/password_change_form.html'},
                    name='password_change'),
    url(r'^accounts/password/change/done/$',
                    auth_views.PasswordChangeDoneView,
                    {'template_name': 'umklapp/password_change_done.html'},
                    name='password_change_done'),

    url(r'^accounts/password/reset/$',
                    auth_views.PasswordResetView,
                    name='password_reset'),
    url(r'^accounts/password/reset/done/$',
                    auth_views.PasswordResetDoneView,
                    name='password_reset_done'),
    url(r'^accounts/password/reset/complete/$',
                    auth_views.PasswordResetCompleteView,
                    name='password_reset_complete'),
    url(r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
                    auth_views.PasswordResetConfirmView,
                    name='password_reset_confirm'),
    url(r'^admin/', admin.site.urls),
    url(r'', include('umklapp.urls')),
]
