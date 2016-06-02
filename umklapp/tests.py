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

    def stdStory(self):
        return Story.create_new_story(startUser=self.users[0],
                                      participating_users=self.users[1:],
                                      first_sentence="first",
                                      title="foo")


class NewStoryTest(UmklappTestCase):
    def setUp(self):
        self.addUsers()

    def testNewStory(self):
        self.stdStory()

    def testParticipating(self):
        s = Story.create_new_story(startUser=self.users[0],
                                      participating_users=self.users[1:3],
                                      first_sentence="first",
                                      title="foo")
        self.assertTrue(s.participates_in(self.users[0]))
        self.assertTrue(s.participates_in(self.users[1]))
        self.assertTrue(s.participates_in(self.users[2]))
        self.assertFalse(s.participates_in(self.users[3]))
        self.assertFalse(s.participates_in(self.users[4]))
        self.assertFalse(s.participates_in(self.users[5]))
        self.assertFalse(s.participates_in(self.users[6]))


class ContinueStoryTest(UmklappTestCase):
    def setUp(self):
        self.addUsers()

    def testContinueStory(self):
        s = self.stdStory()
        self.assertEquals(1, s.whose_turn)
        self.assertEquals(self.users[1], s.waiting_for())
        s.continue_story("second")
        self.assertEquals(2, s.whose_turn)
        self.assertEquals(self.users[2], s.waiting_for())

    def testLatestStoryPart1(self):
        s = self.stdStory()
        latest = s.latest_story_part()
        self.assertEquals(0, latest.position)

    def testLatestStoryPart2(self):
        s = self.stdStory()
        s.continue_story("second")
        latest = s.latest_story_part()
        self.assertEquals(1, latest.position)

    def testLatestStoryPart3(self):
        s = self.stdStory()
        s.continue_story("second")
        latest = s.latest_story_part()
        self.assertEquals(self.users[1], latest.teller.user)

    def testWaitingFor(self):
        s = self.stdStory()
        self.assertEquals(s.waiting_for(), self.users[1])

    def testContinueWaitingFor(self):
        s = self.stdStory()
        s.continue_story("second")
        self.assertEquals(s.waiting_for(), self.users[2])

    def testFinish(self):
        s = self.stdStory()
        s.finish()
        self.assertTrue(s.is_finished)

    # A.) A non-current teller leaves
    def testLeaveStory1(self):
        s = self.stdStory()
        self.assertEquals(s.numberOfActiveTellers(), 7)
        s.leave_story(self.users[1])
        self.assertEquals(s.numberOfActiveTellers(), 6)

    # B.) The current teller leaves
    def testLeaveStory2(self):
        s = self.stdStory()
        self.assertEquals(s.numberOfActiveTellers(), 7)
        s.advance_teller() # 1
        self.assertEquals(s.waiting_for(), self.users[2])
        s.leave_story(self.users[2])
        self.assertEquals(s.waiting_for(), self.users[3])
        self.assertEquals(s.numberOfActiveTellers(), 6)

    # C.) A teller leaves twice
    def testLeaveStory3(self):
        s = self.stdStory()
        self.assertEquals(s.numberOfActiveTellers(), 7)
        s.leave_story(self.users[2])
        s.leave_story(self.users[2])
        self.assertEquals(s.numberOfActiveTellers(), 6)

    # D.) Too many tellers leave
    def testLeaveStory4(self):
        s = self.stdStory()
        self.assertEquals(s.numberOfActiveTellers(), 7)
        s.leave_story(self.users[0])
        self.assertEquals(s.numberOfActiveTellers(), 6)
        s.leave_story(self.users[1])
        self.assertEquals(s.numberOfActiveTellers(), 5)
        s.leave_story(self.users[2])
        self.assertEquals(s.numberOfActiveTellers(), 4)
        s.leave_story(self.users[3])
        self.assertEquals(s.numberOfActiveTellers(), 3)
        s.leave_story(self.users[4])
        self.assertEquals(s.numberOfActiveTellers(), 2)
        self.assertRaises(NotEnoughActivePlayers, s.leave_story, self.users[5])
