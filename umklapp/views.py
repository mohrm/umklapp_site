# encoding: utf-8
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from .models import Story, MAXLEN_STORY_TITLE, MAXLEN_SENTENCE, necessary_skip_votes, NotEnoughActivePlayers
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.views.decorators.http import require_GET, require_POST
from django.forms import Form, CharField, TextInput, MultipleChoiceField
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from random import shuffle

class NewStoryForm(Form):
    title = CharField(
        label = "Wie soll die Geschichte heißen?",
        required = True,
        max_length = MAXLEN_STORY_TITLE,
        widget = TextInput(attrs={'placeholder': 'Das Märchen von der Fabel', 'autocomplete': 'off'}),
        help_text = "Der Titel ist immer sichtbar. Je besser der Titel einen Kontext vorgibt, desto eher bleibt eine Geschichte konsistent.",
        )
    firstSentence = CharField(
        label = "Wie soll die Geschichte losgehen?",
        required = True,
        max_length = MAXLEN_SENTENCE,
        widget = TextInput(attrs={'placeholder': 'Es war einmal…', 'autocomplete': 'off'}),
        help_text = "Das ist der erste Satz der Geschichte. Baue Spannung auf!",
        )
    mitspieler = MultipleChoiceField(
        label = "Wer soll alles noch mitspielen?",
        help_text = "Wähle deine Freunde aus oder füge auch ein paar Unbekannte hinzu.",
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


@require_GET
@login_required
def new_story(request):
    form = NewStoryForm()
    form.set_choices(request.user)

    context = {
        'form': form
    }
    return render(request, 'umklapp/start_story.html', context)

@require_POST
@login_required
def create_new_story(request):
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
        messages.success(request, u"Geschichte „{0!s}“ gestartet".format(s.title))
        return redirect('overview')
    else:
        context = {
            'form': form
        }
        return render(request, 'umklapp/start_story.html', context)

class ExtendStoryForm(Form):
    nextSentence = CharField(
        label = "Wie soll die Geschichte weitergehen?",
        widget = TextInput(attrs={'placeholder': 'und dann...', 'autocomplete': 'off'}),
        required=False,
        max_length = MAXLEN_SENTENCE,
        help_text = "Falls du die Geschichte beendest, musst du nicht unbedingt einen Satz eingaben."
        )

    def clean(self):
        cleaned_data = super(ExtendStoryForm, self).clean()

        finishing = 'finish' in self.data
        nextSentence = cleaned_data.get("nextSentence")

        if not finishing and not nextSentence:
            self.add_error('nextSentence', 'Irgendwas muss doch passieren...')

@login_required
@require_POST
def continue_story(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)

    if s.is_finished:
        return HttpResponseBadRequest("Story already finished")

    if not s.participates_in(request.user):
        raise PermissionDenied

    t = get_object_or_404(s.tellers, user=request.user)

    if s.whose_turn != t.position:
        return HttpResponseBadRequest("Not your turn")

    finish = 'finish' in request.POST
    form = ExtendStoryForm(request.POST)
    if form.is_valid():
        if 'finish' in form.data:
            if form.cleaned_data['nextSentence']:
                s.continue_story(form.cleaned_data['nextSentence'])
            s.finish()
            messages.success(request, u"Geschichte „{0!s}“ beendet".format(s.title))
            return redirect('overview')
        else:
            s.continue_story(form.cleaned_data['nextSentence'])
            messages.success(request, u"Geschichte „{0!s}“ weitergeführt".format(s.title))
            return redirect('overview')
    else:
        context = {
            'story': s,
            'part_number': s.latest_story_part().position + 1,
            'form': form
        }
        return render(request, 'umklapp/extend_story.html', context)

@login_required
@require_POST
def leave_story(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)
    u = request.user

    if s.is_finished:
        return HttpResponseBadRequest("Story already finished")
    if not s.participates_in(u):
        raise PermissionDenied

    if (s.numberOfActiveTellers() >= Story.MINIMUM_NUMBER_OF_ACTIVE_TELLERS + 1):
        messages.success(request, u"Du hast „{0!s}“ verlassen.".format(s.title))
        s.leave_story(u)
    else:
        messages.warning(request, u"Du kannst „{0!s}“ nicht verlassen, da sonst zu wenige Erzähler übrig blieben.".format(s.title))
    return redirect('overview')

@login_required
@require_POST
def skip_always(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)
    u = request.user

    if s.is_finished:
        return HttpResponseBadRequest("Story already finished")
    if not s.participates_in(u):
        raise PermissionDenied

    try:
        s.set_always_skip(u)
        messages.success(request, u"Du wirst nun automatisch übersprungen bei „{0!s}“.".format(s.title))
    except NotEnoughActivePlayers as e:
        messages.success(request, u"Zuwenig aktive Spieler, als dass du überspringen kannst bei „{0!s}“.".format(s.title))
    return redirect('overview')

@login_required
@require_POST
def unskip_always(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)
    u = request.user

    if s.is_finished:
        return HttpResponseBadRequest("Story already finished")
    if not s.participates_in(u):
        raise PermissionDenied

    messages.success(request, u"Du schreibst wieder aktiv mit bei „{0!s}“.".format(s.title))
    s.unset_always_skip(u)
    return redirect('overview')

@login_required
@require_POST
def skip_story(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)
    if not request.user.is_staff and s.waiting_for() != request.user:
        raise PermissionDenied
    s.advance_teller()
    return redirect('overview')

@login_required
@require_GET
def show_story(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)

    if s.is_finished:
        if not s.participates_in(request.user) and not s.is_public:
            raise PermissionDenied

        anonym = True
        for t in s.tellers.all():
            if t.user == request.user:
                anonym = False

        context = {
            'story': s,
            'anonymized' : anonym,
            'has_upvoted' : s.has_upvoted(request.user),
            'upvote_count' : s.upvote_count(),
        }
        return render(request, 'umklapp/show_story.html', context)
    else:
        # unfinished business
        assert not s.is_finished

        if not s.participates_in(request.user):
            raise PermissionDenied

        form = None
        t = get_object_or_404(s.tellers, user=request.user)

        if s.whose_turn == t.position:
            # only show form if its the user's turn
            form = ExtendStoryForm()

        context = {
            'story': s,
            'part_number': s.latest_story_part().position + 1,
            'form': form,
            'has_voted_skip' : s.has_voted_skip(request.user),
            'always_skip' : s.does_always_skip(request.user),
            'skipvote_count' : s.skipvote_count(),
            'skipvotes_necessary' : necessary_skip_votes(s.numberOfActiveTellers()),
        }
        return render(request, 'umklapp/extend_story.html', context)


@login_required
@require_POST
def upvote_story(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)

    if not s.is_finished:
        return HttpResponseBadRequest("Story not finished yet")

    s.upvote_story(request.user)

    return redirect('show_story', story_id=s.id)

@login_required
@require_POST
def downvote_story(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)

    if not s.is_finished:
        return HttpResponseBadRequest("Story not finished yet")

    s.downvote_story(request.user)

    return redirect('show_story', story_id=s.id)

@login_required
@require_POST
def story_vote_skip(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)

    if s.is_finished:
        return HttpResponseBadRequest("Story already finished")

    success = s.vote_skip(request.user)
    if success:
        messages.success(request, u"Abstimmung zum Überspringen erfolgreich")

    return redirect('show_story', story_id=s.id)

@login_required
@require_POST
def story_unvote_skip(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)

    if s.is_finished:
        return HttpResponseBadRequest("Story already finished")

    s.unvote_skip(request.user)

    return redirect('show_story', story_id=s.id)

@login_required
@require_POST
def publish_story(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)

    if not s.is_finished:
        return HttpResponseBadRequest("Story not finished yet")
    if not s.started_by == request.user:
        raise PermissionDenied

    s.public(True)

    return redirect('show_story', story_id=s.id)

@login_required
@require_POST
def unpublish_story(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)

    if not s.is_finished:
        return HttpResponseBadRequest("Story not finished yet")
    if not s.started_by == request.user:
        raise PermissionDenied

    s.public(False)

    return redirect('show_story', story_id=s.id)

@login_required
@require_GET
def overview(request):
    all_running_stories = Story.objects \
            .filter(is_finished = False) \
            .order_by('title', 'id') \
            .annotate(parts_count = Count('tellers__storyparts',distinct=True)) \
            .annotate(contrib_count = Count('tellers__storyparts__teller', distinct=True)) \
            .annotate(active_count = Count('always_skip', distinct=True)) \
            .select_related('started_by') \
            .prefetch_related('tellers') \
            .prefetch_related('always_skip') \
            .prefetch_related('tellers__user')
    all_finished_stories = Story.objects \
            .filter(is_finished = True) \
            .order_by('-finish_date', '-id') \
            .annotate(parts_count = Count('tellers__storyparts',distinct=True)) \
            .annotate(contrib_count = Count('tellers__storyparts__teller', distinct=True)) \
            .annotate(upvote_count = Count('upvotes',distinct=True)) \
            .select_related('started_by') \
            .prefetch_related('tellers') \
            .prefetch_related('tellers__user')
    if request.user.is_staff:
        running_stories = all_running_stories
        finished_stories = all_finished_stories
    else:
        running_stories = filter(lambda (s): s.participates_in(request.user) and
                                 not s.does_always_skip(request.user),
                             all_running_stories)
        finished_stories = filter(lambda (s): s.participates_in(request.user) or s.is_public,
                                      all_finished_stories)
    user_activity = User.objects \
            .filter(is_staff=False) \
            .annotate(parts_written=Count('teller__storyparts')) \
            .order_by('-parts_written', 'username')[:10]
    action_count = len([s for s in running_stories if s.waiting_for() == request.user])

    context = {
        'username': request.user.username,
        'specialpowers': request.user.is_staff,
        'running_stories': running_stories,
        'finished_stories': finished_stories,
	'user_activity': user_activity,
        'action_count': action_count,
    }
    return render(request, 'umklapp/overview.html', context)


