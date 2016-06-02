from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    url(r'^(?:ajax)?$', views.overview, name='overview'),
    url(r'^start_new_story/', views.start_new_story, name='new_story'),
    url(r'^continue_story/(?P<story_id>[0-9]+)', views.continue_story,
        name='continue_story'),
    url(r'^story_continued/(?P<story_id>[0-9]+)', views.story_continued),
    url(r'^show_story/(?P<story_id>[0-9]+)', views.show_story, name='show_story'),
    url(r'^publish_story/(?P<story_id>[0-9]+)', views.publish_story, name='publish_story'),
    url(r'^unpublish_story/(?P<story_id>[0-9]+)', views.unpublish_story, name='unpublish_story'),
    url(r'^skip', views.skip, name='skip'),
    url(r'^leave_story', views.leave_story, name='leave_story')

]

