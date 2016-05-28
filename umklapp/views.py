from django.http import HttpResponse
from django.shortcuts import render
from .models import Story
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

def index(request):
    return HttpResponse("Hello World.")

def start_new_story(request):
    return HttpResponse('Hier wird eine neue Geschichte gestartet')

def continue_story(request, story_id):
    return HttpResponse('Geschichte Nr. ' + story_id + ' fortsetzen')

def story_continued(request, story_id):
    s = Story.objects.get(id=story_id)
    s.continue_story("text")


def finish_story(request, story_id):
    return HttpResponse('Geschichte Nr. ' + story_id + ' beenden')

def show_story(request, story_id):
    return HttpResponse('Fertige Geschichte Nr. ' + story_id + ' anzeigen')

@login_required
def overview(request):
    my_stories = Story.objects.all()
    context = {
        'username': request.user.username,
        'my_stories': my_stories
    }
    return render(request, 'umklapp/overview.html', context)


