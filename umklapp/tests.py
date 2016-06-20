# -*- coding: utf-8 -*-

from django.test import TestCase, Client
from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from umklapp.models import *
from umklapp.templatetags import git_revision

class SkipVoteTest(TestCase):
    def testSingles(self):
        self.assertEquals(necessary_skip_votes(2), 0)
        self.assertEquals(necessary_skip_votes(3), 2)
        self.assertEquals(necessary_skip_votes(4), 3)
        self.assertEquals(necessary_skip_votes(5), 3)
        self.assertEquals(necessary_skip_votes(6), 4)

    def testMonotonous(self):
        x = 0
        for votes in range(0,100):
            nec = necessary_skip_votes(votes)
            assert (nec >= x)
            x = nec

    def testSafeMajority(self):
        for total in range(3,100):
            necVote = necessary_skip_votes(total)
            self.assertTrue(necVote > 0.5 * total, msg="failed with total=%d, necVote=%d" % (total, necVote))

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
        self.assertEquals("first", list(s.parts())[0].content)
        self.assertEquals("", s.rules)
        self.assertEquals("foo", s.title)

    def testStoryCreationWithRules(self):
        s = Story.create_new_story(startUser=self.users[0],
                                      participating_users=self.users[1:3],
                                      first_sentence="first",
                                      rules="rule",
                                      title="foo")
        self.assertEquals("first", s.latest_story_part().content)
        self.assertEquals("rule", s.rules)
        self.assertEquals("foo", s.title)

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
        s.set_always_skip(self.users[1])
        self.assertEquals(s.numberOfActiveTellers(), 6)

    # B.) The current teller leaves
    def testLeaveStory2(self):
        s = self.stdStory()
        self.assertEquals(s.numberOfActiveTellers(), 7)
        s.advance_teller() # 1
        self.assertEquals(s.waiting_for(), self.users[2])
        s.set_always_skip(self.users[2])
        self.assertEquals(s.waiting_for(), self.users[3])
        self.assertEquals(s.numberOfActiveTellers(), 6)

    # C.) A teller leaves twice
    def testLeaveStory3(self):
        s = self.stdStory()
        self.assertEquals(s.numberOfActiveTellers(), 7)
        s.set_always_skip(self.users[2])
        s.set_always_skip(self.users[2])
        self.assertEquals(s.numberOfActiveTellers(), 6)

    # D.) Too many tellers leave
    def testLeaveStory4(self):
        s = self.stdStory()
        self.assertEquals(s.numberOfActiveTellers(), 7)
        s.set_always_skip(self.users[0])
        self.assertEquals(s.numberOfActiveTellers(), 6)
        s.set_always_skip(self.users[1])
        self.assertEquals(s.numberOfActiveTellers(), 5)
        s.set_always_skip(self.users[2])
        self.assertEquals(s.numberOfActiveTellers(), 4)
        s.set_always_skip(self.users[3])
        self.assertEquals(s.numberOfActiveTellers(), 3)
        s.set_always_skip(self.users[4])
        self.assertEquals(s.numberOfActiveTellers(), 2)
        self.assertRaises(NotEnoughActivePlayers, s.set_always_skip, self.users[5])

    def testNumberOfContributors(self):
        s = self.stdStory()
        self.assertEquals(s.numberOfContributors, 1)
        s.continue_story('test') #u1
        self.assertEquals(s.numberOfContributors, 2)
        s.continue_story('test') #u2
        self.assertEquals(s.numberOfContributors, 3)
        s.set_always_skip(self.users[0])
        self.assertEquals(s.numberOfContributors, 3)
        s.continue_story('test') #u3
        self.assertEquals(s.numberOfContributors, 4)
        s.continue_story('test') #u4
        self.assertEquals(s.numberOfContributors, 5)
        s.continue_story('test') #u5
        self.assertEquals(s.numberOfContributors, 6)
        s.continue_story('test') #u6
        self.assertEquals(s.numberOfContributors, 7)
        s.continue_story('test') #u1
        self.assertEquals(s.numberOfContributors, 7)

class ViewTests(UmklappTestCase):
    def setUp(self):
        self.addUsers()
        self.stdStory()

    def testOverviewSQLQueries(self):
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
        with self.assertNumQueries(6):
            r = c.get(reverse("overview"))

    def testLogin(self):
        c = Client()
        r1 = c.get("/", follow=True)
        self.assertEquals(r1.status_code, 200)
        assert(r1.context['form'].fields.has_key("username"))
        assert(r1.context['form'].fields.has_key("password"))
        r2 = c.post(reverse('django.contrib.auth.views.login'),
            dict(username="user1", password="p455w0rd"), follow=True)
        self.assertEquals(r2.status_code, 200)
        assert("my_new_finished_stories" in r2.context.keys())
        assert("my_running_stories" in r2.context.keys())
        # Login successful

    def testFullCycle(self):
        c1 = Client()
        c2 = Client()
        c1.login(username="user1", password="p455w0rd")
        c2.login(username="user2", password="p455w0rd")

        r1 = c1.get(reverse("new_story"))
        self.assertEquals(r1.status_code, 200)
        assert(r1.context['form'].fields.has_key("title"))
        assert(r1.context['form'].fields.has_key("rules"))
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
        # not your turn
        r = c1.post(reverse("continue_story", kwargs={'story_id':story_id}),
            dict(nextSentence="foo"))
        self.assertEquals(r.status_code, 400)
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

        r = c1.post(reverse("story_vote_skip", kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))
        r = c1.post(reverse("story_unvote_skip", kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))

        # not possible before finished
        r = c2.post(reverse("publish_story",  kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 400)
        r = c1.post(reverse("publish_story",  kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 400)
        r = c1.post(reverse("unpublish_story",  kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 400)
        r = c1.post(reverse("upvote_story",  kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 400)
        r = c1.post(reverse("downvote_story",  kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 400)

        # finish story
        r = c1.get(reverse("show_story", kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 200)
        assert(r.context['form'].fields.has_key("nextSentence"))
        r = c1.post(reverse("continue_story", kwargs={'story_id':story_id}),
            dict(nextSentence="it ends", finish="finish"))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))

        r = c2.post(reverse("publish_story",  kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 403)

        r = c1.post(reverse("publish_story",  kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))

        r = c1.post(reverse("unpublish_story",  kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))

        r = c1.post(reverse("upvote_story",  kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))

        r = c1.post(reverse("downvote_story",  kwargs={'story_id':story_id}))
        self.assertRedirects(r, reverse("show_story", kwargs={'story_id':story_id}))

        # not possible after finished:
        r = c1.post(reverse("story_vote_skip", kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 400)
        r = c1.post(reverse("story_unvote_skip", kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 400)
        r = c1.post(reverse("continue_story", kwargs={'story_id':story_id}),
            dict(nextSentence="it continues"))
        self.assertEquals(r.status_code, 400)
        r = c1.post(reverse("skip_always", kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 400)
        r = c1.post(reverse("unskip_always", kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 400)

    def testLeaveStory(self):
        c1 = Client()
        c2 = Client()
        c1.login(username="user1", password="p455w0rd")
        c2.login(username="user2", password="p455w0rd")

        r = c1.get(reverse("new_story"))
        self.assertEquals(r.status_code, 200)
        assert(r.context['form'].fields.has_key("title"))
        assert(r.context['form'].fields.has_key("rules"))
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
        self.assertEquals(r.status_code, 403)
        r = c5.post(reverse("continue_story", kwargs={'story_id':story_id}),
            dict(nextSentence="it continues"))
        self.assertEquals(r.status_code, 403)
        r = c5.post(reverse("skip_story", kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 403)
        r = c5.get(reverse("show_story", kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 403)
        r = c5.post(reverse("unskip_always", kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 403)

        # quick hack to finish story
        s = Story.objects.get(id=story_id)
        s.finish()

        # more checks c5 cannot do anything
        r = c5.post(reverse("publish_story",  kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 403)
        r = c5.post(reverse("unpublish_story",  kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 403)
        r = c5.get(reverse("show_story", kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 403)
        r = c5.post(reverse("unskip_always", kwargs={'story_id':story_id}))
        self.assertEquals(r.status_code, 403) # 400 would reveal information

    def testSeparateLists(self):
        c1 = Client()
        c1.login(username="user1", password="p455w0rd")

        r = c1.get(reverse("finished"))
        self.assertEquals(r.status_code, 200)

        r = c1.get(reverse("running"))
        self.assertEquals(r.status_code, 200)


class TemplateTagsTest(UmklappTestCase):

    def test(self):
        rev=git_revision.git_revision()
        self.assertTrue(True)
