from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    url(r'^$', views.overview, name='overview'),
    url(r'^start_new_story/', views.start_new_story, name='new_story'),
    url(r'^continue_story/(?P<story_id>[0-9]+)', views.continue_story,
        name='continue_story'),
    url(r'^story_continued/(?P<story_id>[0-9]+)', views.story_continued),
    url(r'^finish_story/(?P<story_id>[0-9]+)', views.finish_story,
        name='finish_story'),
    url(r'^show_story/(?P<story_id>[0-9]+)', views.show_story, name='show_story')
]

