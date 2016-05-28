from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

class Teller(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    corresponding_story = models.ForeignKey('Story', on_delete=models.CASCADE,
                                            related_name="tellers")
    position = models.IntegerField()

class Story(models.Model):
    started_by = models.ForeignKey(User, related_name="started_by", on_delete=models.CASCADE)
    whose_turn = models.IntegerField()
    is_finished = models.BooleanField()

    @staticmethod
    def create_new_story(startUser, participating_users, first_sentence):
        s = Story(started_by=startUser, is_finished=False, whose_turn=1)
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

    def waiting_for(self):
        if not self.is_finished:
            return Teller.objects.get(corresponding_story=self,position=self.whose_turn).user
        else:
            return None

    def continue_story(self, text):
        myparts = StoryPart.objects.filter(teller__corresponding_story=self)
        if (not myparts):
            nextPos = 0
        else:
            nextPos = max([part.teller.position for part in myparts]) + 1
        nextTeller = Teller.objects.get(corresponding_story=self,
                                        position=nextPos % self.tellers.count())
        newPart = StoryPart(teller=nextTeller, content=text, position=nextPos)
        newPart.save()
        self.advance_teller()

    def finish(self):
        self.is_finished = True
        self.save()

    def advance_teller(self):
        self.whose_turn = (self.whose_turn + 1) % self.tellers.count()
        self.save()

    def latest_story_part(self):
        myparts = StoryPart.objects.filter(teller__corresponding_story=self).order_by('position').reverse()
        return myparts[0]



class StoryPart(models.Model):
    teller = models.ForeignKey('Teller', on_delete=models.CASCADE)
    position = models.IntegerField()
    content = models.CharField(max_length=256)



