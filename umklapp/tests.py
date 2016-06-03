# -*- coding: utf-8 -*-

from django.test import TestCase, Client
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from umklapp.models import *
from umklapp.templatetags import git_revision

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

    def testContinueStory2(self):
        s = self.stdStory()
        s.continue_story(u"\U0001F303")
        latest = s.latest_story_part()
        self.assertEquals(latest.content, u"\U0001F303")

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

class ViewTests(UmklappTestCase):
    def setUp(self):
        self.addUsers()
        self.stdStory()

    def testLogin(self):
        c = Client()
        r1 = c.get("/", follow=True)
        self.assertEquals(r1.status_code, 200)
        assert(r1.context['form'].fields.has_key("username"))
        assert(r1.context['form'].fields.has_key("password"))
        r2 = c.post(reverse('django.contrib.auth.views.login'),
            dict(username="user1", password="p455w0rd"), follow=True)
        self.assertEquals(r2.status_code, 200)
        assert("finished_stories" in r2.context.keys())
        assert("running_stories" in r2.context.keys())
        # Login successful

    def testFullCycle(self):
        c1 = Client()
        c2 = Client()
        c1.login(username="user1", password="p455w0rd")
        c2.login(username="user2", password="p455w0rd")

        r1 = c1.get(reverse("new_story"))
        self.assertEquals(r1.status_code, 200)
        assert(r1.context['form'].fields.has_key("title"))
        assert(r1.context['form'].fields.has_key("firstSentence"))
        assert(r1.context['form'].fields.has_key("mitspieler"))
        vals = list(v for (k,v) in r1.context['form'].fields["mitspieler"].choices)
        for i in range(2,7):
            assert("user%d" % i in vals), i

        # invalid post
        r2 = c1.post(reverse("create_new_story"),
            dict(title="test title", firstSentence="", mitspieler=("3",)))
        self.assertEquals(r2.status_code, 200) # no redirection means an error happend

        # valid post
        r2 = c1.post(reverse("create_new_story"),
            dict(title="test title", firstSentence="it begins", mitspieler=("3",)))
        self.assertRedirects(r2, '/')

        # is it ok to hard-code the story_id here?
        story_id = 2

        r = c2.get(reverse("show_story", kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 200)
        assert(r.context['form'].fields.has_key("nextSentence"))
        # invalid entry
        r = c2.post(reverse("continue_story", kwargs={'story_id':story_id}),
            dict(nextSentence=""))
        self.assertEquals(r.status_code, 200) # no redirection means an error happend
        # valid entry
        r = c2.post(reverse("continue_story", kwargs={'story_id':story_id}),
            dict(nextSentence="it continues"))
        self.assertRedirects(r, reverse("overview"))

        r = c1.post(reverse("skip_story", kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("overview"))
        r = c2.post(reverse("skip_story", kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("overview"))

        r = c1.get(reverse("show_story", kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 200)
        assert(r.context['form'].fields.has_key("nextSentence"))
        r = c1.post(reverse("continue_story", kwargs={'story_id':story_id}),
            dict(nextSentence="it ends", finish="finish"))
        self.assertRedirects(r, reverse("overview"))

        r = c2.post(reverse("publish_story",  kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 403)

        r = c1.post(reverse("publish_story",  kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))

        r = c1.post(reverse("unpublish_story",  kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))

    def testLeaveStory(self):
        c1 = Client()
        c2 = Client()
        c1.login(username="user1", password="p455w0rd")
        c2.login(username="user2", password="p455w0rd")

        r = c1.get(reverse("new_story"))
        self.assertEquals(r.status_code, 200)
        assert(r.context['form'].fields.has_key("title"))
        assert(r.context['form'].fields.has_key("firstSentence"))
        assert(r.context['form'].fields.has_key("mitspieler"))
        vals = list(v for (k,v) in r.context['form'].fields["mitspieler"].choices)
        for i in range(2,7):
            assert("user%d" % i in vals), i

        # invalid post
        r = c1.post(reverse("create_new_story"),
            dict(title="test title", firstSentence="it begins", mitspieler=[3,4]))
        self.assertRedirects(r, reverse("overview"))

        # is it ok to hard-code the story_id here?
        story_id = 2

        # player 2 can leave
        r = c2.post(reverse("leave_story", kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("overview"))
        r = c2.get(reverse("overview"))

        # player 1 now cannot leave
        # (unfortunately, not easy to observe, as we do not see the message in the tests)
        r = c1.post(reverse("leave_story", kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("overview"))

class TemplateTagsTest(UmklappTestCase):

    def test(self):
        rev=git_revision.git_revision()
        self.assertTrue(True)
