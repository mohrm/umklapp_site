from django.urls import include, re_path
from django.conf import settings

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView, TemplateView
from django_registration.backends.one_step.views import RegistrationView

admin.autodiscover()

urlpatterns = [
# http://www.voidynullness.net/blog/2014/01/15/raiders-of-the-lost-django-registration-templates/
    re_path(r'^accounts/', include('django_registration.backends.one_step.urls')),
    re_path(r'^accounts/login/$',
                    auth_views.LoginView.as_view(
                    template_name = 'umklapp/login.html'),
                    name='auth_login'),
    re_path(r'^accounts/logout/$',
                    auth_views.LogoutView.as_view(
                    template_name = 'umklapp/logout.html'),
                    name='auth_logout'),
    re_path(r'^accounts/password/change/$',
                    auth_views.PasswordChangeView.as_view(
                    template_name = 'umklapp/password_change_form.html'),
                    name='password_change'),
    re_path(r'^accounts/password/change/done/$',
                    auth_views.PasswordChangeDoneView.as_view(
                    template_name = 'umklapp/password_change_done.html'),
                    name='password_change_done'),

    re_path(r'^accounts/password/reset/$',
                    auth_views.PasswordResetView.as_view(),
                    name='password_reset'),
    re_path(r'^accounts/password/reset/done/$',
                    auth_views.PasswordResetDoneView.as_view(),
                    name='password_reset_done'),
    re_path(r'^accounts/password/reset/complete/$',
                    auth_views.PasswordResetCompleteView.as_view(),
                    name='password_reset_complete'),
    re_path(r'^accounts/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
                    auth_views.PasswordResetConfirmView.as_view(),
                    name='password_reset_confirm'),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'', include('umklapp.urls')),
]
