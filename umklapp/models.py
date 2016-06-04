from __future__ import unicode_literals

from datetime import datetime

from django.db import models
from django.contrib.auth.models import User

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
    hasLeft = models.BooleanField()

class Story(models.Model):
    MINIMUM_NUMBER_OF_ACTIVE_TELLERS = 2
    started_by = models.ForeignKey(User, related_name="started_by", on_delete=models.CASCADE)
    title = models.CharField(max_length=MAXLEN_STORY_TITLE)
    whose_turn = models.IntegerField()
    is_finished = models.BooleanField()
    is_public = models.BooleanField(default=False,blank=False)
    finish_date = models.DateTimeField(null=True)
    upvotes = models.ManyToManyField(User)
    skipvote = models.ManyToManyField(User, related_name="skipvoted")

    def __unicode__(self):
        return self.title

    @staticmethod
    def create_new_story(startUser, participating_users, title, first_sentence):
        s = Story(started_by=startUser, is_finished=False, title=title, whose_turn=1)
        s.save()
        t0 = Teller(user=startUser, corresponding_story=s, position=0,
                    hasLeft=False)
        t0.save()
        firstPart = StoryPart(teller=t0, position=0, content=first_sentence)
        firstPart.save()

        positions = range(1, len(participating_users)+1)
        for (u,p) in zip(participating_users, positions):
            t = Teller(user=u, corresponding_story=s, position=p, hasLeft=False)
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
        self.skipvote.clear()

    def numberOfActiveTellers(self):
        # do not use filter and count here, as this will incur additional database
        # queries, even if self.tellers is prefetched already
        return len([t for t in self.tellers.all() if t.user.is_active and not t.hasLeft])

    def leave_story(self, user):
        # capture the case that the teller leaves behind only one active person
        if (self.numberOfActiveTellers() <= Story.MINIMUM_NUMBER_OF_ACTIVE_TELLERS):
            raise NotEnoughActivePlayers

        # mark corresponding teller as 'has left'
        t0 = Teller.objects.get(corresponding_story=self, user=user)
        t0.hasLeft = True
        t0.save()

        # if it was the leaving teller's turn, fast forward to the next active
        # teller - note that there are at least two active tellers, so that
        # advance_teller will terminate
        if self.waiting_for() == user:
            self.advance_teller()

    def finish(self):
        self.is_finished = True
        self.finish_date = datetime.now()
        self.save()

    def public(self, state = True):
        self.is_public = state
        self.save()

    def parts(self):
        return StoryPart.objects.filter(teller__corresponding_story=self)

    def advance_teller(self):
        self.whose_turn = (self.whose_turn + 1) % self.tellers.count()
        while (not self.waiting_for().is_active or self.hasLeft(self.waiting_for())):
            self.whose_turn = (self.whose_turn + 1) % self.tellers.count()
        self.save()
        self.skipvote.clear()

    def hasLeft(self, user):
        return [t.hasLeft for t in list(self.tellers.all()) if t.user == user][0]

    def latest_story_part(self):
        return self.parts().last()

    def participates_in(self, user):
        return bool([t for t in list(self.tellers.all()) if t.user == user])

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
        return user in self.upvotes.all()

    def vote_skip(self, user):
        """Returns if vote succeeded"""
        assert(not self.is_finished)
        self.skipvote.add(user)
        necessary = necessary_skip_votes(self.numberOfActiveTellers())
        if self.skipvote_count() >= necessary and necessary > 0:
            self.advance_teller()
            return True
        else: # not enough votes yet
            return False

    def unvote_skip(self, user):
        assert(not self.is_finished)
        self.skipvote.remove(user)

    def skipvote_count(self):
        return self.skipvote.count()

    def has_voted_skip(self, user):
        return user in self.skipvote.all()

class StoryPart(models.Model):
    teller = models.ForeignKey('Teller', on_delete=models.CASCADE, related_name = 'storyparts')
    position = models.IntegerField()
    content = models.CharField(max_length=MAXLEN_SENTENCE)

    class Meta:
        ordering = ['position']


class NotEnoughActivePlayers(Exception):
    pass
