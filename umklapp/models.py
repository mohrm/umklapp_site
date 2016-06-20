from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.utils.functional import cached_property
from django.conf import settings
import django.utils.timezone


MAXLEN_STORY_TITLE = 200
MAXLEN_SENTENCE = 2000

def necessary_skip_votes(total):
    "Computes the number of skipvotes necessary from total number of tellers"
    r = {
      0: 0,
      1: 0,
      2: 0,
      3: 2,
      4: 3,
      5: 3,
      6: 4,
    }.get(total, -1)
    if r != -1:
        return r
    return int(round(total * 0.6))

class Teller(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    corresponding_story = models.ForeignKey('Story', on_delete=models.CASCADE,
                                            related_name="tellers")
    position = models.IntegerField()

class Story(models.Model):
    MINIMUM_NUMBER_OF_ACTIVE_TELLERS = 2
    started_by = models.ForeignKey(User, related_name="started_by", on_delete=models.CASCADE)
    title = models.CharField(max_length=MAXLEN_STORY_TITLE)
    rules = models.CharField(max_length=MAXLEN_SENTENCE,null=True, blank=True)
    whose_turn = models.IntegerField()
    is_finished = models.BooleanField()
    is_public = models.BooleanField(default=False,blank=False)
    finish_date = models.DateTimeField(null=True, blank=True)
    upvotes = models.ManyToManyField(User, blank=True)
    skipvote = models.ManyToManyField(User, related_name="skipvoted", blank=True)
    always_skip = models.ManyToManyField(User, related_name="skippers", blank=True)
    read_by = models.ManyToManyField(User, related_name="stories_read", blank=True)
    last_action = models.DateTimeField(default=django.utils.timezone.now)

    def __unicode__(self):
        return self.title

    @staticmethod
    def create_new_story(startUser, participating_users, title, rules, first_sentence):
        s = Story(
            started_by=startUser,
            is_finished=False,
            title=title,
            rules=rules,
            whose_turn=1,
            last_action = django.utils.timezone.now(),
            )
        s.save()
        t0 = Teller(user=startUser, corresponding_story=s, position=0)
        t0.save()
        firstPart = StoryPart(teller=t0, position=0, content=first_sentence)
        firstPart.save()

        positions = range(1, len(participating_users)+1)
        for (u,p) in zip(participating_users, positions):
            t = Teller(user=u, corresponding_story=s, position=p)
            t.save()
        return s

    def waiting_for_teller(self):
        if not self.is_finished:
            # do not use .get() here, as this will incur additional database
            # queries, even if self.tellers is prefetched already
            return [t for t in list(self.tellers.all()) if t.position == self.whose_turn][0]
        else:
            return None

    def waiting_for(self):
        teller = self.waiting_for_teller()
        if teller:
            return teller.user
        else:
            return None

    def continue_story(self, text):
        last_part = self.latest_story_part()
        nextPos = last_part.position + 1
        newPart = StoryPart(teller=self.waiting_for_teller(), content=text, position=nextPos)
        newPart.save()
        self.advance_teller()

    def numberOfActiveTellers(self):
        skippers = self.always_skip.all()
        # do not use filter and count here, as this will incur additional database
        # queries, even if self.tellers is prefetched already
        return len([t for t in self.tellers.all() if t.user.is_active and not t.user in skippers])

    # the view actually uses a Count aggreagation for performance.
    def _numberOfContributors(self):
        return len(set([p.teller.user for p in self.parts()]))
    numberOfContributors = property(_numberOfContributors)

    def finish(self):
        self.is_finished = True
        self.finish_date = django.utils.timezone.now()
        self.last_action = django.utils.timezone.now()
        self.save()

    def public(self, state = True):
        self.is_public = state
        self.save()

    def parts(self):
        return StoryPart.objects.filter(teller__corresponding_story=self)

    def advance_teller(self):
        cnt = self.tellers.count()
        for i in range(cnt):
            self.whose_turn = (self.whose_turn + 1) % cnt
            if not self.waiting_for().is_active:
                continue
            if self.does_always_skip(self.waiting_for()):
                continue
            break
        assert i != cnt - 1
        self.last_action = django.utils.timezone.now()
        self.save()
        self.skipvote.clear()

    def latest_story_part(self):
        return self.parts().last()

    def participates_in(self, user):
        return self.tellers.filter(user=user).count() > 0

    def upvote_story(self, user):
        assert(self.is_finished)
        self.upvotes.add(user)

    def downvote_story(self, user):
        """Undo an upvote"""
        assert(self.is_finished)
        self.upvotes.remove(user)

    def upvote_count(self):
        return self.upvotes.count()

    def has_upvoted(self, user):
        return self.upvotes.filter(id=user.id).exists()

    def vote_skip(self, user):
        """Returns if vote succeeded"""
        assert(not self.is_finished)
        self.skipvote.add(user)
        if self.get_skipvote_count() >= self.necessary_skip_votes and self.necessary_skip_votes > 0:
            self.advance_teller()
            return True
        else: # not enough votes yet
            return False

    def unvote_skip(self, user):
        assert(not self.is_finished)
        self.skipvote.remove(user)

    @cached_property
    def necessary_skip_votes(self):
        return necessary_skip_votes(self.numberOfActiveTellers())

    def get_skipvote_count(self):
        return self.skipvote.count()
    skipvote_count= cached_property(get_skipvote_count, name='skipvote_count')

    def has_voted_skip(self, user):
        return user in self.skipvote.all()

    def set_always_skip(self, user):
        if self.numberOfActiveTellers() <= 2:
            raise NotEnoughActivePlayers()
        self.always_skip.add(user)
        if user == self.waiting_for():
            self.advance_teller()

    def unset_always_skip(self, user):
        self.always_skip.remove(user)

    def does_always_skip(self, user):
        return user in self.always_skip.all()

    def try_autoskip(self):
        """ This method checks whether we need to autoskip this story, and does so. """
        if settings.AUTOSKIP and django.utils.timezone.now() - self.last_action > settings.AUTOSKIP:
            self.advance_teller()
            return True
        else:
            return False


class StoryPart(models.Model):
    teller = models.ForeignKey('Teller', on_delete=models.CASCADE, related_name = 'storyparts')
    position = models.IntegerField()
    content = models.CharField(max_length=MAXLEN_SENTENCE)

    class Meta:
        ordering = ['position']


class NotEnoughActivePlayers(Exception):
    pass
