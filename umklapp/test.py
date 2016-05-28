from django.test import TestCase
from django.test.utils import override_settings

from umklapp.models import *

class UmklappTestCase(TestCase):
    def addUsers(self):
        self.users = []
        for i in range(0,7):
            u = User.objects.create_user(
                "user%d" % i,
                "test@example.com",
                "p455w0rd"
            )
            self.users.append(u)

class NewStoryTest(UmklappTestCase):
    def setUp(self):
        self.addUsers()

    def testNewStory(self):
        Story.create_new_story(self.users[0], self.users, "first")

class ContinueStoryTest(UmklappTestCase):
    def setUp(self):
        self.addUsers()

    def testContinueStory(self):
        s = Story.create_new_story(self.users[0], self.users[1:], "first")
        self.assertEquals(1, s.whose_turn)
        s.continue_story("second")
        self.assertEquals(2, s.whose_turn)

    def testLatestStoryPart1(self):
        s = Story.create_new_story(self.users[0], self.users[1:], "first")
        latest = s.latest_story_part()
        self.assertEquals(0, latest.position)

    def testLatestStoryPart2(self):
        s = Story.create_new_story(self.users[0], self.users[1:], "first")
        s.continue_story("second")
        latest = s.latest_story_part()
        self.assertEquals(1, latest.position)

    def testWaitingFor(self):
        s = Story.create_new_story(self.users[0], self.users[1:], "first")
        self.assertEquals(s.waiting_for(), self.users[1])

    def testFinish(self):
        s = Story.create_new_story(self.users[0], self.users[1:], "first")
        s.finish()
        self.assertTrue(s.is_finished)
