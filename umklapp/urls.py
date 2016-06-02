from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # GET URLs (nothing happens)
    url(r'^(?:ajax)?$', views.overview, name='overview'),
    url(r'^story/(?P<story_id>[0-9]+)$', views.show_story, name='show_story'),
    url(r'^new_story$', views.new_story, name='new_story'),

    # POST URLs (something happens, always ends with a redirecT)
    url(r'^new_story/create$', views.create_new_story, name='create_new_story'),
    url(r'^story/(?P<story_id>[0-9]+)/continue$', views.continue_story, name='continue_story'),
    url(r'^story/(?P<story_id>[0-9]+)/publish$', views.publish_story, name='publish_story'),
    url(r'^story/(?P<story_id>[0-9]+)/unpublish$', views.unpublish_story, name='unpublish_story'),
    url(r'^story/(?P<story_id>[0-9]+)/skip$', views.skip_story, name='skip_story'),
    url(r'^story/(?P<story_id>[0-9]+)/leave$', views.leave_story, name='leave_story'),
]

