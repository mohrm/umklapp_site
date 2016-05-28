from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

class Teller(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    corresponding_story = models.ForeignKey('Story', on_delete=models.CASCADE)
    position = models.IntegerField()

class Story(models.Model):
    started_by = models.ForeignKey(User, related_name="started_by", on_delete=models.CASCADE)
    whose_turn = models.ForeignKey(Teller, on_delete=models.CASCADE)
    is_finished = models.BooleanField()
    tellers = models.ManyToManyField('Teller', related_name="tellers")

    def continue_story(self, text):
        myparts = StoryPart.objects.filter(owning_story=self)
        if (not myparts):
            nextPos = 0
        else:
            nextPos = max([part.position for part in myparts])
        newPart = StoryPart(author=self.whose_turn, owning_story=self,
                            position=nextPos,content=text)
        newPart.save()
        self.advance_teller()

    def advance_teller(self):
        self.whose_turn = Teller.get(corresponding_story=self, position=self.whose_turn.position % self.tellers.count())
        self.save()


class StoryPart(models.Model):
    teller = models.ForeignKey('Teller', on_delete=models.CASCADE)
    owning_story = models.ForeignKey(Story, on_delete=models.CASCADE)
    content = models.CharField(max_length=256)



