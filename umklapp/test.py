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
        s = Story.create_new_story(self.users[0], self.users, "first")
        s.continue_story("second")

