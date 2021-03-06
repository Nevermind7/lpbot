# -*- coding: utf-8 -*-

# Author: Edward Powell, embolalia.net
# Copyright 2014, Nikola Kovacevic, <nikolak@outlook.com>


import re

import praw
import arrow

from lpbot.module import commands, rule, NOLIMIT
from lpbot.formatting import bold, color, colors
from lpbot import tools

USER_AGENT = "github.com/Nikola-K/lpbot IRC bot"

domain = r'https?://(?:www\.|np\.)?reddit\.com'
short_domain = r'https?://(?:www\.|np\.)?redd\.it/(\S+)'
post_url = '(%s/r/.*?/comments/[\w-]+)' % domain
user_url = '%s/u(ser)?/([\w-]+)' % domain
post_regex = re.compile(post_url)
user_regex = re.compile(user_url)
short_regex = re.compile(short_domain)


def setup(bot):
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.lpbotMemory()
    bot.memory['url_callbacks'][post_regex] = rpost_info
    bot.memory['url_callbacks'][user_regex] = redditor_info
    bot.memory['url_callbacks'][short_regex] = rpost_info


def shutdown(bot):
    del bot.memory['url_callbacks'][post_regex]
    del bot.memory['url_callbacks'][user_regex]
    del bot.memory['url_callbacks'][short_regex]


@rule('.*%s.*' % post_url)
@rule('.*%s.*' % short_domain)
def rpost_info(bot, trigger, match=None):
    r = praw.Reddit(user_agent=USER_AGENT)
    match = match or trigger

    if len(match.group(1)) < 10:
        post_url = "https://www.reddit.com/comments/{}/".format(match.group(1))
    else:
        post_url = match.group(1)

    s = r.get_submission(url=post_url)

    message = ('[reddit] {title} {link}{nsfw} | {points} points ({percent}) | '
               '{comments} comments | Posted by {author} {post_time}')

    if s.is_self:
        link = '(self.{})'.format(s.subreddit.display_name)
    else:
        link = '({}) to r/{}'.format(s.url, s.subreddit.display_name)

    if s.over_18:
        nsfw = bold(color(' [NSFW]', colors.RED))
        # TODO implement per-channel settings db, and make this able to kick
    else:
        nsfw = ''

    if s.author:
        author = s.author.name
    else:
        author = '[deleted]'

    if s.created:
        post_time = arrow.get(s.created_utc, tzinfo="utc").humanize()
    else:
        post_time = ''

    if s.score > 0:
        point_color = colors.GREEN
    else:
        point_color = colors.RED

    percent = color(str(int(s.upvote_ratio * 100)) + '%', point_color)

    message = message.format(
        title=s.title, link=link, nsfw=nsfw, points=s.score, percent=percent,
        comments=s.num_comments, author=author, post_time=post_time)
    bot.say(message)


# If you change this, you'll have to change some other things...
@commands('redditor')
def redditor_info(bot, trigger, match=None):
    """Show information about the given Redditor"""
    commanded = re.match(bot.config.prefix + 'redditor', trigger)
    r = praw.Reddit(user_agent=USER_AGENT)
    match = match or trigger
    try:
        u = r.get_redditor(match.group(2))
    except:
        if commanded:
            bot.say('No such Redditor.')
            return NOLIMIT
        else:
            return
            # Fail silently if it wasn't an explicit command.

    message = '[redditor] ' + u.name
    if commanded:
        message = message + ' | http://reddit.com/u/' + u.name
    if u.is_gold:
        message = message + ' | 08Gold'
    if u.is_mod:
        message = message + ' | 05Mod'
    message = message + ' | Link: ' + str(u.link_karma) + ' | Comment: ' + str(u.comment_karma)

    # TODO detect cake day with u.created
    bot.say(message)


# If you change the groups here, you'll have to change some things above.
@rule('.*%s.*' % user_url)
def auto_redditor_info(bot, trigger):
    redditor_info(bot, trigger)
