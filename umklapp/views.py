# encoding: utf-8
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Story
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.forms import Form, CharField, TextInput, MultipleChoiceField
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from random import shuffle

class NewStoryForm(Form):
    title = CharField(
        label = "Wie soll die Geschichte heißen?",
        widget = TextInput(attrs={'placeholder': 'Das Märchen von der Fabel'}),
        )
    firstSentence = CharField(
        label = "Wie soll die Geschichte losgehen?",
        widget = TextInput(attrs={'placeholder': 'Es war einmal…'}),
        )
    mitspieler = MultipleChoiceField(
        label = "Wer soll alles noch mitspielen?",
        )

    def set_choices(self,user):
        """ Sets the mitspieler choices to all other non-admin users"""
        choices = []
        initial = []
        for u in User.objects.all():
            if u != user and not u.is_superuser and u.is_active:
                initial.append(u.pk)
                choices.append((u.pk, str(u)))
        self.fields['mitspieler'].choices = choices
        self.fields['mitspieler'].initial = []


def start_new_story(request):
    if request.method == 'POST':
        form = NewStoryForm(request.POST)
        form.set_choices(request.user)
        if form.is_valid():
            users = [ User.objects.get(pk=uid) for uid in form.cleaned_data['mitspieler'] ]
            shuffle(users)
            s = Story.create_new_story(
                title = form.cleaned_data['title'],
                startUser = request.user,
                first_sentence = form.cleaned_data['firstSentence'],
                participating_users = users
                )
            messages.success(request, u"Geschichte „%s“ gestartet" % s.title)
            return redirect('overview')
    else:
        form = NewStoryForm()
        form.set_choices(request.user)

    context = {
        'form': form
    }
    return render(request, 'umklapp/start_story.html', context)

class ExtendStoryForm(Form):
    nextSentence = CharField(
        label = "Wie soll die Geschichte weitergehen?",
        widget = TextInput(attrs={'placeholder': 'und dann...'}),
        required=False,
        )

    def clean(self):
        cleaned_data = super(ExtendStoryForm, self).clean()

        finishing = 'finish' in self.data
        nextSentence = cleaned_data.get("nextSentence")

        if not finishing and not nextSentence:
            self.add_error('nextSentence', 'Irgendwas muss doch passieren...')

class NotYourTurnException(Exception):
    pass


def continue_story(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)
    t = get_object_or_404(s.tellers, user=request.user)

    if s.is_finished:
        raise PermissionDenied

    if s.whose_turn != t.position:
        raise NotYourTurnException

    if request.method == 'POST':
        finish = 'finish' in request.POST
        form = ExtendStoryForm(request.POST)
        if form.is_valid():
            if 'finish' in form.data:
                if form.cleaned_data['nextSentence']:
                    s.continue_story(form.cleaned_data['nextSentence'])
                s.finish()
                messages.success(request, u"Geschichte „%s“ beendet" % s.title)
                return redirect('overview')
            else:
                s.continue_story(form.cleaned_data['nextSentence'])
                messages.success(request, u"Geschichte „%s“ weitergeführt" % s.title)
                return redirect('overview')
    else:
        form = ExtendStoryForm()
    context = {
        'story': s,
        'form': form
    }
    return render(request, 'umklapp/extend_story.html', context)

def skip(request):
    story_id = request.POST['story_id']
    s = get_object_or_404(Story.objects, id=story_id)
    s.advance_teller()
    return redirect('overview')

def story_continued(request, story_id):
    s = Story.objects.get(id=story_id)
    s.continue_story("text")

def show_story(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)

    if not s.is_finished:
        raise PermissionDenied

    context = {
        'story': s,
    }
    return render(request, 'umklapp/show_story.html', context)

@login_required
def overview(request):
    all_running_stories = Story.objects.filter(is_finished = False)
    finished_stories = Story.objects.filter(is_finished = True)
    if request.user.is_staff:
        running_stories = all_running_stories
    else:
        running_stories = filter(lambda (s): s.participates_in(request.user),
                             all_running_stories)
    context = {
        'username': request.user.username,
        'specialpowers': request.user.is_staff,
        'running_stories': running_stories,
        'finished_stories': finished_stories,
    }
    return render(request, 'umklapp/overview.html', context)


