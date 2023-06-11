# encoding: utf-8
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from .models import Story, StoryPart, Teller, MAXLEN_STORY_TITLE, MAXLEN_SENTENCE, NotEnoughActivePlayers
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.views.decorators.http import require_GET, require_POST
from django.forms import Form, ModelForm, CharField, TextInput, Textarea, MultipleChoiceField
from django.forms.widgets import SelectMultiple
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Q, Max
from random import shuffle

class NewStoryForm(Form):
    title = CharField(
        label = "Wie soll die Geschichte heißen?",
        required = True,
        max_length = MAXLEN_STORY_TITLE,
        widget = TextInput(attrs={'placeholder': 'Das Märchen von der Fabel', 'autocomplete': 'off'}),
        help_text = "Der Titel ist immer sichtbar. Je besser der Titel einen Kontext vorgibt, desto eher bleibt eine Geschichte konsistent.",
        )
    rules = CharField(
            label = "Bei Bedarf: Besondere Regeln",
        required = False,
        max_length = MAXLEN_SENTENCE,
        widget = TextInput(attrs={'placeholder': '', 'autocomplete': 'off'}),
        help_text = "Du kannst zusätzliche Regeln für die Geschichte definieren, z.B. „Nur Sätze mit drei Worten“ oder „Bitte nur Reinform“. Diese Regeln werden den Erzählern dann angezeigt – überprüft werden sie allerdings nicht automatisch!",
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
        widget = SelectMultiple(attrs = {"id": "user-select"}),
        )

    def set_choices(self,user):
        """ Sets the mitspieler choices to all other non-admin users"""
        choices = []
        initial = []
        users = User.objects\
            .annotate(lastpart=Max('teller__storyparts__creation'))\
            .filter(is_superuser=False, is_active=True)\
            .exclude(id=user.id).all()
        for u in users:
            if u.lastpart:
                last_storypart_date = u.lastpart.strftime("%Y-%m-%d")
            else:
                last_storypart_date = "never"
            assert u != user and not u.is_superuser and u.is_active
            initial.append(u.pk)
            choices.append((u.pk, "%s   (last active: %s)" % (str(u), last_storypart_date)))
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
            rules = form.cleaned_data['rules'],
            startUser = request.user,
            first_sentence = form.cleaned_data['firstSentence'],
            participating_users = users
            )
        messages.success(request, "Geschichte „%s“ gestartet" % s.title)
        return redirect('overview')
    else:
        context = {
            'form': form
        }
        return render(request, 'umklapp/start_story.html', context)

class ExtendStoryForm(Form):
    nextSentence = CharField(
        label = "Wie soll die Geschichte weitergehen?",
        widget = Textarea(attrs={
                'placeholder': 'und dann...', 'autocomplete': 'off',
                'rows': 2
            }),
        required=False,
        max_length = MAXLEN_SENTENCE,
        help_text = "Falls du die Geschichte beendest, musst du nicht unbedingt einen Satz eingeben."
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
            return redirect('show_story', story_id=s.id)
        else:
            s.continue_story(form.cleaned_data['nextSentence'])
            messages.success(request, "Geschichte „%s“ weitergeführt" % s.title)
            return redirect('overview')
    else:
        context = {
            'story': s,
            'form': form
        }
        return render(request, 'umklapp/extend_story.html', context)

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
        messages.success(request, "Du wirst nun automatisch übersprungen bei „%s“." % s.title)
    except NotEnoughActivePlayers as e:
        messages.success(request, "Zuwenig aktive Spieler, als dass du überspringen kannst bei „%s“." % s.title)
    return redirect('overview')

@login_required
@require_POST
def unskip_always(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)
    u = request.user

    if not s.participates_in(u):
        raise PermissionDenied
    if s.is_finished:
        return HttpResponseBadRequest("Story already finished")

    messages.success(request, "Du schreibst wieder aktiv mit bei „%s“." % s.title)
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

# Nota bene: This view is available without logging in!
@require_GET
def show_story(request, story_id):
    s = get_object_or_404(Story.objects, id=story_id)

    if s.is_finished:
        if not s.participates_in(request.user) and not s.is_public:
            raise PermissionDenied

        anonym = not s.participates_in(request.user)

        if request.user.is_authenticated() and not request.user in s.read_by.all():
            s.read_by.add(request.user)

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
            'form': form,
            'always_skip' : s.does_always_skip(request.user),
        }
        return render(request, 'umklapp/extend_story.html', context)

class UserUpdateForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email',]

@login_required
@require_GET
def user_profile(request):
    form = UserUpdateForm(instance=request.user)
    context = {
        'form': form,
        'sentences_written': StoryPart.objects.filter(teller__user=request.user).count(),
        'participated_in': Teller.objects.filter(user=request.user).count(),
        'stories_started': Story.objects.filter(started_by=request.user).count(),
        'funny_parts': StoryPart.objects.select_related('teller__user') \
                .select_related('teller__corresponding_story') \
                .filter(teller__user=request.user) \
                .annotate(Count('upvotes')) \
                .filter(upvotes__count__gt=0) \
                .order_by('-upvotes__count','-teller__corresponding_story__id') \
                [:10]
    }
    return render(request, 'umklapp/profile.html', context)

@login_required
@require_POST
def update_profile(request):
    form = UserUpdateForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Daten gespeichert")
        return redirect('user_profile')
    else:
        context = {
            'form': form,
            'sentences_written': StoryPart.objects.filter(teller__user=request.user).count(),
            'participated_in': Teller.objects.filter(user=request.user).count(),
            'stories_started': Story.objects.filter(started_by=request.user).count(),
        }
        return render(request, 'umklapp/profile.html', context)


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
def upvote_storypart(request, storypart_id):
    s = get_object_or_404(StoryPart.objects, id=storypart_id)

    if request.user == s.teller.user:
        messages.warning(request, "Du kannst deine eigenen Beiträge nicht upvoten.")
        return redirect('show_story', story_id=s.teller.corresponding_story.id)

    s.upvote(request.user)

    return redirect('show_story', story_id=s.teller.corresponding_story.id)

@login_required
@require_POST
def downvote_storypart(request, storypart_id):
    s = get_object_or_404(StoryPart.objects, id=storypart_id)

    s.downvote(request.user)

    return redirect('show_story', story_id=s.teller.corresponding_story.id)

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
    my_running_stories = Story.objects \
            .filter(is_finished = False) \
            .order_by('title', 'id') \
            .annotate(parts_count = Count('tellers__storyparts',distinct=True)) \
            .annotate(active_count = Count('tellers', distinct=True)) \
            .filter(tellers__user=request.user, tellers__position=F('whose_turn'))

    my_new_finished_stories = Story.objects \
            .filter(is_finished = True) \
            .exclude(read_by = request.user) \
            .annotate(parts_count = Count('tellers__storyparts',distinct=True)) \
            .annotate(contrib_count = Count('tellers__storyparts__teller', distinct=True)) \
            .annotate(upvote_count = Count('upvotes',distinct=True)) \
            .order_by('-upvote_count', '-finish_date', '-id') \
            .select_related('started_by') \
            .filter(Q(tellers__user=request.user) | Q(is_public=True)) 

    user_activity = User.objects \
            .filter(is_staff=False) \
            .annotate(parts_written=Count('teller__storyparts')) \
            .order_by('-parts_written', 'username')[:10]
    action_count = len(my_running_stories)

    funny_users = User.objects \
            .filter(is_staff=False) \
            .annotate(funny_parts=Count('teller__storyparts__upvotes')) \
            .filter(funny_parts__gt=0) \
            .order_by('-funny_parts', 'username')[:10]

    story_starters = User.objects \
            .filter(is_staff=False) \
            .annotate(stories_started=Count('stories_created')) \
            .order_by('-stories_started', 'username')[:10]
            
    action_count = len(my_running_stories)

    context = {
        'username': request.user.username,
        'specialpowers': request.user.is_staff,
        'my_running_stories': my_running_stories,
        'my_new_finished_stories': my_new_finished_stories,
	'user_activity': user_activity,
        'funny_users': funny_users,
        'story_starters': story_starters,
        'action_count': action_count,
    }
    return render(request, 'umklapp/overview.html', context)


@login_required
@require_GET
def running_stories(request):
    all_running_stories = Story.objects \
            .filter(is_finished = False) \
            .order_by('title', 'id') \
            .annotate(parts_count = Count('tellers__storyparts',distinct=True)) \
            .annotate(contrib_count = Count('tellers__storyparts__teller', distinct=True)) \
            .annotate(active_count = Count('tellers', distinct=True)) \
            .select_related('started_by') \
            .prefetch_related('always_skip') \
            .prefetch_related('tellers__user') \

    if request.user.is_staff:
        running_stories = all_running_stories
    else:
        running_stories = all_running_stories.filter(tellers__user=request.user)

    user_activity = User.objects \
            .filter(is_staff=False) \
            .annotate(parts_written=Count('teller__storyparts')) \
            .order_by('-parts_written', 'username')[:10]

    context = {
        'username': request.user.username,
        'specialpowers': request.user.is_staff,
        'running_stories': running_stories,
        'finished_stories': finished_stories,
        'user_activity': user_activity,
    }
    return render(request, 'umklapp/running.html', context)

@login_required
@require_GET
def finished_stories(request):
    all_finished_stories = Story.objects \
            .filter(is_finished = True) \
            .annotate(parts_count = Count('tellers__storyparts',distinct=True)) \
            .annotate(contrib_count = Count('tellers__storyparts__teller', distinct=True)) \
            .annotate(upvote_count = Count('upvotes',distinct=True)) \
            .order_by('-upvote_count', '-finish_date', '-id') \
            .select_related('started_by') \
            .prefetch_related('tellers__user')
    all_new_stories = Story.objects \
            .filter(is_finished = True) \
            .exclude(read_by=request.user) \
            .only('id')

    if request.user.is_staff:
        finished_stories = all_finished_stories
        new_stories = all_new_stories
    else:
        finished_stories = all_finished_stories.filter( \
                Q(tellers__user=request.user) \
                | Q(is_public=True))
        new_stories = all_new_stories.filter( \
                Q(tellers__user=request.user) \
                | Q(is_public=True))

    user_activity = User.objects \
            .filter(is_staff=False) \
            .annotate(parts_written=Count('teller__storyparts')) \
            .order_by('-parts_written', 'username')[:10]

    context = {
        'username': request.user.username,
        'specialpowers': request.user.is_staff,
        'finished_stories': finished_stories,
        'user_activity': user_activity,
        'new_stories': new_stories,
    }
    return render(request, 'umklapp/finished.html', context)

