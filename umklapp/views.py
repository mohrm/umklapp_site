# encoding: utf-8
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import Story
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.forms import Form, CharField, TextInput, MultipleChoiceField
from django.contrib.auth.models import User


def index(request):
    return HttpResponse("Hello World.")



class NewStoryForm(Form):
    firstSentence = CharField(
        label = "Wie soll die Geschichte losgehen?",
        widget = TextInput(attrs={'placeholder': 'Es war einmal…'}),
        )
    mitspieler = MultipleChoiceField(
        label = "Wer soll alles noch mitspielen?",
        )

    def set_choices(self,user):
        """ Sets the mitspieler selection to all other users"""
        choices = []
        initial = []
        for u in User.objects.all():
            if u != user:
                initial.append(u.pk)
                choices.append((u.pk, str(u)))
        self.fields['mitspieler'].choices = choices
        self.fields['mitspieler'].initial = initial


def start_new_story(request):
    if request.method == 'POST':
        form = NewStoryForm(request.POST)
        form.set_choices(request.user)
        if form.is_valid():
            Story.create_new_story(
                startUser = request.user,
                first_sentence = form.cleaned_data['firstSentence'],
                participating_users = form.cleaned_data['mitspieler'],
                )
            messages.success(request, u"Spiel gestartet")
            return redirect('overview')
    else:
        form = NewStoryForm()
        form.set_choices(request.user)

    context = {
        'form': form
    }
    return render(request, 'umklapp/start_story.html', context)

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


