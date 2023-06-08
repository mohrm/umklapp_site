from django.conf.urls import include, url
from . import views

urlpatterns = [
    # GET URLs (nothing happens)
    url(r'^(?:ajax)?$', views.overview, name='overview'),
    url(r'^story/(?P<story_id>[0-9]+)$', views.show_story, name='show_story'),
    url(r'^new_story$', views.new_story, name='new_story'),
    url(r'^profile$', views.user_profile, name='user_profile'),
    url(r'^running(?:_ajax)?$', views.running_stories, name='running'),
    url(r'^finished(?:_ajax)?$', views.finished_stories, name='finished'),

    # POST URLs (something happens, always ends with a redirect)
    url(r'^new_story/create$', views.create_new_story, name='create_new_story'),
    url(r'^update_profile$', views.update_profile, name='update_profile'),
    url(r'^story/(?P<story_id>[0-9]+)/continue$', views.continue_story, name='continue_story'),
    url(r'^story/(?P<story_id>[0-9]+)/publish$', views.publish_story, name='publish_story'),
    url(r'^story/(?P<story_id>[0-9]+)/unpublish$', views.unpublish_story, name='unpublish_story'),
    url(r'^story/(?P<story_id>[0-9]+)/upvote$', views.upvote_story, name='upvote_story'),
    url(r'^story/(?P<story_id>[0-9]+)/downvote$', views.downvote_story, name='downvote_story'),
    url(r'^story/(?P<story_id>[0-9]+)/set_skip$', views.skip_always, name='skip_always'),
    url(r'^story/(?P<story_id>[0-9]+)/unset_skip$', views.unskip_always, name='unskip_always'),
    url(r'^story/(?P<story_id>[0-9]+)/skip$', views.skip_story, name='skip_story'),
    url(r'^storypart/(?P<storypart_id>[0-9]+)/upvote$', views.upvote_storypart, name='upvote_storypart'),
    url(r'^storypart/(?P<storypart_id>[0-9]+)/downvote$', views.downvote_storypart, name='downvote_storypart'),
]

