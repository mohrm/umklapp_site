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
                                      rules="",
                                      title="foo")


class NewStoryTest(UmklappTestCase):
    def setUp(self):
        self.addUsers()

    def testNewStory(self):
        self.stdStory()

    def testStoryCreation(self):
        s = Story.create_new_story(startUser=self.users[0],
                                      participating_users=self.users[1:3],
                                      first_sentence="first",
                                      rules="",
                                      title="foo")
        self.assertEqual("first", list(s.parts())[0].content)
        self.assertEqual("", s.rules)
        self.assertEqual("foo", s.title)

    def testStoryCreationWithRules(self):
        s = Story.create_new_story(startUser=self.users[0],
                                      participating_users=self.users[1:3],
                                      first_sentence="first",
                                      rules="rule",
                                      title="foo")
        self.assertEqual("first", s.latest_story_part().content)
        self.assertEqual("rule", s.rules)
        self.assertEqual("foo", s.title)

    def testParticipating(self):
        s = Story.create_new_story(startUser=self.users[0],
                                      participating_users=self.users[1:3],
                                      first_sentence="first",
                                      rules="",
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
        self.assertEqual(1, s.whose_turn)
        self.assertEqual(self.users[1], s.waiting_for())
        s.continue_story("second")
        self.assertEqual(2, s.whose_turn)
        self.assertEqual(self.users[2], s.waiting_for())

    def testContinueStory2(self):
        s = self.stdStory()
        s.continue_story("\U0001F303")
        latest = s.latest_story_part()
        self.assertEqual(latest.content, "\U0001F303")

    def testContinueStory2(self):
        s = self.stdStory()
        then = s.last_action
        s.continue_story("\U0001F303")
        now = s.last_action
        self.assertNotEqual(then,now)

    def testLatestStoryPart1(self):
        s = self.stdStory()
        latest = s.latest_story_part()
        self.assertEqual(0, latest.position)

    def testLatestStoryPart2(self):
        s = self.stdStory()
        s.continue_story("second")
        latest = s.latest_story_part()
        self.assertEqual(1, latest.position)

    def testLatestStoryPart3(self):
        s = self.stdStory()
        s.continue_story("second")
        latest = s.latest_story_part()
        self.assertEqual(self.users[1], latest.teller.user)

    def testAutoSkip(self):
        s = self.stdStory()
        self.assertFalse(s.try_autoskip())
        self.assertEqual(s.waiting_for(), self.users[1])

        s.last_action = django.utils.timezone.now() - 2 * settings.AUTOSKIP
        s.save()

        self.assertTrue(s.try_autoskip())
        self.assertEqual(s.waiting_for(), self.users[2])

    def testWaitingFor(self):
        s = self.stdStory()
        self.assertEqual(s.waiting_for(), self.users[1])

    def testContinueWaitingFor(self):
        s = self.stdStory()
        s.continue_story("second")
        self.assertEqual(s.waiting_for(), self.users[2])

    def testFinish(self):
        s = self.stdStory()
        s.finish()
        self.assertTrue(s.is_finished)

    # A.) A non-current teller leaves
    def testLeaveStory1(self):
        s = self.stdStory()
        self.assertEqual(s.numberOfActiveTellers(), 7)
        s.set_always_skip(self.users[1])
        self.assertEqual(s.numberOfActiveTellers(), 6)

    # B.) The current teller leaves
    def testLeaveStory2(self):
        s = self.stdStory()
        self.assertEqual(s.numberOfActiveTellers(), 7)
        s.advance_teller() # 1
        self.assertEqual(s.waiting_for(), self.users[2])
        s.set_always_skip(self.users[2])
        self.assertEqual(s.waiting_for(), self.users[3])
        self.assertEqual(s.numberOfActiveTellers(), 6)

    # C.) A teller leaves twice
    def testLeaveStory3(self):
        s = self.stdStory()
        self.assertEqual(s.numberOfActiveTellers(), 7)
        s.set_always_skip(self.users[2])
        s.set_always_skip(self.users[2])
        self.assertEqual(s.numberOfActiveTellers(), 6)

    # D.) Too many tellers leave
    def testLeaveStory4(self):
        s = self.stdStory()
        self.assertEqual(s.numberOfActiveTellers(), 7)
        s.set_always_skip(self.users[0])
        self.assertEqual(s.numberOfActiveTellers(), 6)
        s.set_always_skip(self.users[1])
        self.assertEqual(s.numberOfActiveTellers(), 5)
        s.set_always_skip(self.users[2])
        self.assertEqual(s.numberOfActiveTellers(), 4)
        s.set_always_skip(self.users[3])
        self.assertEqual(s.numberOfActiveTellers(), 3)
        s.set_always_skip(self.users[4])
        self.assertEqual(s.numberOfActiveTellers(), 2)
        self.assertRaises(NotEnoughActivePlayers, s.set_always_skip, self.users[5])

    def testNumberOfContributors(self):
        s = self.stdStory()
        self.assertEqual(s.numberOfContributors, 1)
        s.continue_story('test') #u1
        self.assertEqual(s.numberOfContributors, 2)
        s.continue_story('test') #u2
        self.assertEqual(s.numberOfContributors, 3)
        s.set_always_skip(self.users[0])
        self.assertEqual(s.numberOfContributors, 3)
        s.continue_story('test') #u3
        self.assertEqual(s.numberOfContributors, 4)
        s.continue_story('test') #u4
        self.assertEqual(s.numberOfContributors, 5)
        s.continue_story('test') #u5
        self.assertEqual(s.numberOfContributors, 6)
        s.continue_story('test') #u6
        self.assertEqual(s.numberOfContributors, 7)
        s.continue_story('test') #u1
        self.assertEqual(s.numberOfContributors, 7)

class ViewTests(UmklappTestCase):
    def setUp(self):
        self.addUsers()
        self.stdStory()

    def testSQLQueries(self):
        """ This test adds a large number of unfinished and finished stories,
        with lots of text, and the makes sure that the number of SQL queries is
        as expected."""
        for i in range(6):
            s =  Story.create_new_story(startUser=self.users[0],
                                      participating_users=self.users[1:],
                                      first_sentence="first",
                                      rules="",
                                      title="foo")
            for j in range(3):
                s.continue_story("Text %d" % j)
            if i >= 3:
                s.finish()
        c = Client()
        r = c.post(reverse('django.contrib.auth.views.login'),
            dict(username="user1", password="p455w0rd"), follow=True)
        with self.assertNumQueries(7):
            r = c.get(reverse("overview"))
        with self.assertNumQueries(6):
            r = c.get(reverse("running"))
        with self.assertNumQueries(6):
            r = c.get(reverse("finished"))
        with self.assertNumQueries(3):
            r = c.get(reverse("new_story"))

    def testLogin(self):
        c = Client()
        r1 = c.get("/", follow=True)
        self.assertEqual(r1.status_code, 200)
        assert("username" in r1.context['form'].fields)
        assert("password" in r1.context['form'].fields)
        r2 = c.post(reverse('django.contrib.auth.views.login'),
            dict(username="user1", password="p455w0rd"), follow=True)
        self.assertEqual(r2.status_code, 200)
        assert("my_new_finished_stories" in list(r2.context.keys()))
        assert("my_running_stories" in list(r2.context.keys()))
        # Login successful

    def testFullCycle(self):
        c1 = Client()
        c2 = Client()
        c1.login(username="user1", password="p455w0rd")
        c2.login(username="user2", password="p455w0rd")

        r1 = c1.get(reverse("new_story"))
        self.assertEqual(r1.status_code, 200)
        assert("title" in r1.context['form'].fields)
        assert("rules" in r1.context['form'].fields)
        assert("firstSentence" in r1.context['form'].fields)
        assert("mitspieler" in r1.context['form'].fields)
        vals = list(v.split()[0] for (k,v) in r1.context['form'].fields["mitspieler"].choices)
        for i in range(2,7):
            assert("user%d" % i in vals), i

        # invalid post
        r2 = c1.post(reverse("create_new_story"),
            dict(title="test title", firstSentence="", mitspieler=("3",)))
        self.assertEqual(r2.status_code, 200) # no redirection means an error happend

        # valid post
        r2 = c1.post(reverse("create_new_story"),
            dict(title="test title", firstSentence="it begins", mitspieler=("3",)))
        self.assertRedirects(r2, '/')

        # is it ok to hard-code the story_id here?
        story_id = 2

        r = c2.get(reverse("show_story", kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 200)
        assert("nextSentence" in r.context['form'].fields)
        # not your turn
        r = c1.post(reverse("continue_story", kwargs={'story_id':story_id}),
            dict(nextSentence="foo"))
        self.assertEqual(r.status_code, 400)
        # invalid entry
        r = c2.post(reverse("continue_story", kwargs={'story_id':story_id}),
            dict(nextSentence=""))
        self.assertEqual(r.status_code, 200) # no redirection means an error happend
        # valid entry
        r = c2.post(reverse("continue_story", kwargs={'story_id':story_id}),
            dict(nextSentence="it continues"))
        self.assertRedirects(r, reverse("overview"))

        r = c1.post(reverse("skip_story", kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("overview"))
        r = c2.post(reverse("skip_story", kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("overview"))

        # not possible before finished
        r = c2.post(reverse("publish_story",  kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 400)
        r = c1.post(reverse("publish_story",  kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 400)
        r = c1.post(reverse("unpublish_story",  kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 400)
        r = c1.post(reverse("upvote_story",  kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 400)
        r = c1.post(reverse("downvote_story",  kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 400)

        # finish story
        r = c1.get(reverse("show_story", kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 200)
        assert("nextSentence" in r.context['form'].fields)
        r = c1.post(reverse("continue_story", kwargs={'story_id':story_id}),
            dict(nextSentence="it ends", finish="finish"))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))

        r = c2.post(reverse("publish_story",  kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 403)

        r = c1.post(reverse("publish_story",  kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))

        r = c1.post(reverse("unpublish_story",  kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))

        r = c1.post(reverse("upvote_story",  kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))

        r = c1.post(reverse("downvote_story",  kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))

        r = c1.post(reverse("upvote_storypart", kwargs={'storypart_id': 2}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id': story_id}))

        r = c2.post(reverse("upvote_storypart", kwargs={'storypart_id': 2}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id': story_id}))

        r = c2.post(reverse("downvote_storypart", kwargs={'storypart_id': 2}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id': story_id}))

        # not possible after finished:
        r = c1.post(reverse("continue_story", kwargs={'story_id':story_id}),
            dict(nextSentence="it continues"))
        self.assertEqual(r.status_code, 400)
        r = c1.post(reverse("skip_always", kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 400)
        r = c1.post(reverse("unskip_always", kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 400)

    def testLeaveStory(self):
        c1 = Client()
        c2 = Client()
        c1.login(username="user1", password="p455w0rd")
        c2.login(username="user2", password="p455w0rd")

        r = c1.get(reverse("new_story"))
        self.assertEqual(r.status_code, 200)
        assert("title" in r.context['form'].fields)
        assert("rules" in r.context['form'].fields)
        assert("firstSentence" in r.context['form'].fields)
        assert("mitspieler" in r.context['form'].fields)
        vals = list(v.split()[0] for (k,v) in r.context['form'].fields["mitspieler"].choices)
        for i in range(2,7):
            assert("user%d" % i in vals), i

        # invalid post
        r = c1.post(reverse("create_new_story"),
            dict(title="test title", firstSentence="it begins", mitspieler=[3,4]))
        self.assertRedirects(r, reverse("overview"))

        # is it ok to hard-code the story_id here?
        story_id = 2

        # player 2 can leave
        r = c2.post(reverse("skip_always", kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("overview"))
        r = c2.get(reverse("overview"))

        # player 1 now cannot leave
        # (unfortunately, not easy to observe, as we do not see the message in the tests)
        r = c1.post(reverse("skip_always", kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("overview"))

        # player 2 joins again
        r = c2.post(reverse("unskip_always", kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("overview"))

    def testNoPermission(self):
        c1 = Client()
        c1.login(username="user1", password="p455w0rd")
        c5 = Client()
        c5.login(username="user5", password="p455w0rd")

        r = c1.post(reverse("create_new_story"),
            dict(title="test title", firstSentence="it begins", mitspieler=[3,4]))
        self.assertRedirects(r, reverse("overview"))

        # check c5 cannot do anything
        story_id = 2 # is it ok to hard-code the story_id here?
        r = c5.post(reverse("skip_always", kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 403)
        r = c5.post(reverse("continue_story", kwargs={'story_id':story_id}),
            dict(nextSentence="it continues"))
        self.assertEqual(r.status_code, 403)
        r = c5.post(reverse("skip_story", kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 403)
        r = c5.get(reverse("show_story", kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 403)
        r = c5.post(reverse("unskip_always", kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 403)

        # quick hack to finish story
        s = Story.objects.get(id=story_id)
        s.finish()

        # more checks c5 cannot do anything
        r = c5.post(reverse("publish_story",  kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 403)
        r = c5.post(reverse("unpublish_story",  kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 403)
        r = c5.get(reverse("show_story", kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 403)
        r = c5.post(reverse("unskip_always", kwargs={'story_id':story_id}))
        self.assertEqual(r.status_code, 403) # 400 would reveal information

    def testSeparateLists(self):
        c1 = Client()
        c1.login(username="user1", password="p455w0rd")

        r = c1.get(reverse("finished"))
        self.assertEqual(r.status_code, 200)

        r = c1.get(reverse("running"))
        self.assertEqual(r.status_code, 200)


class TemplateTagsTest(UmklappTestCase):

    def test(self):
        rev=git_revision.git_revision()
        self.assertTrue(True)
