# -*- coding: utf-8 -*-

""" Code that links OASIS with external systems.

    Anything that wants to run an external program or connect over the network
    (except to OASIS database or memcache servers) should come through here.
"""

from oasis.lib import OaConfig, Groups, Feeds, Periods, Users2, UFeeds, Users
from logging import log, ERROR, INFO
import os
import subprocess


def feeds_available_group_scripts():
    """ Return a list of file names of available group feed scripts.
    """

    feed_dir = os.path.join(OaConfig.feed_path, "group")
    files = [
        f
        for f
        in os.listdir(feed_dir)
        if os.path.isfile(os.path.join(feed_dir, f))
    ]
    return files


def feeds_available_user_scripts():
    """ Return a list of file names of available user feed scripts.
    """

    feed_dir = os.path.join(OaConfig.feed_path, "user")
    files = [
        f
        for f
        in os.listdir(feed_dir)
        if os.path.isfile(os.path.join(feed_dir, f))
    ]
    return files


def feeds_run_group_script(filename, args=None):
    """ Run the external group script with the given args (if any).
        Return resulting output as a list of strings or raise IOError
        with an error message.
        This function may block until the script has finished so should
        only be called, eg. by a scheduled task, not triggered directly
        from the UI.
    """
    if not args:
        args = []
    # make sure we're only running code from the group feeds folder.
    safe_fname = os.path.basename(filename)
    full_path = os.path.join(OaConfig.feed_path, "group", safe_fname)
    if not os.path.isfile(full_path):
        raise IOError("Invalid group script file %s" % safe_fname)

    cmd = [full_path, ] + args
    output = subprocess.check_output(cmd)
    return output


def feeds_run_user_script(filename, args=None):
    """ Run the external group script with the given args (if any).
        Return resulting output as a list of strings or raise IOError
        with an error message.
        This function may block until the script has finished so should
        only be called, eg. by a scheduled task, not triggered directly
        from the UI.
    """
    if not args:
        args = []
    # make sure we're only running code from the user feeds folder.
    safe_fname = os.path.basename(filename)
    full_path = os.path.join(OaConfig.feed_path, "user", safe_fname)
    if not os.path.isfile(full_path):
        raise IOError("Invalid user script file %s" % safe_fname)

    cmd = [full_path, ] + args
    output = subprocess.check_output(cmd)
    return output


def group_update_from_feed(group_id, refresh_users=False):
    """ Update group membership from it's feed
        Returns (added, removed, unknown) with usernames of users
    """
    group = Groups.Group(g_id=group_id)
    if not group.source == 'feed':
        return

    feed = Feeds.Feed(f_id=group.feed)
    scriptrun = ' '.join([feed.script, group.feedargs])
    try:
        output = feeds_run_group_script(feed.script, args=[group.feedargs, ])
    except BaseException, err:
        log(ERROR, "Exception while running group feed '%s': %s" % (scriptrun, err))
        raise

    removed = []
    added = []
    unknown = []
    old_members = group.member_unames()
    new_members = output.split()[1:]
    for uname in new_members:
        uid = Users2.uid_by_uname(uname)
        if not uid:
            users_update_from_feed([uname, ])
            log(INFO, "Group feed contained unknown user account %s" % uname)
            unknown.append(uname)
            continue
        if not uname in old_members:
            group.add_member(uid)
            added.append(uname)

    for uname in old_members:
        if not uname in new_members:
            uid = Users2.uid_by_uname(uname)
            group.remove_member(uid)
            removed.append(uname)

    if refresh_users:
        for uname in group.member_unames():
            uid = Users2.uid_by_uname(uname)
            user_update_details_from_feed(uid, uname)

    return added, removed, unknown


def users_update_from_feed(upids):
    """ Given a list of upids, go through and try to fetch details from
        feed, updating/creating the accounts if needed.
    """
    for upid in upids:
        user_id = Users2.uid_by_uname(upid)
        if not user_id:  # we don't know who they are, so create them.
            for feed in UFeeds.all_list():

                try:
                    out = feeds_run_user_script(feed.script, args=[upid, ])
                except BaseException, err:
                    log(ERROR, "Exception running user feed '%s': %s" % (feed.script, err))
                    continue

                res = out.splitlines()
                if res[0].startswith("ERROR"):
                    log(ERROR, "Error running user feed '%s': %s" % (feed.script, res))
                    continue

                line = res[1]
                studentid = ""
                try:
                    (upid, name, email, studentid) = line.split(',')

                except ValueError:
                    try:
                        (upid, name, email) = line.split(',')
                    except ValueError:
                        continue

                given = name.split(" ")[0]
                try:
                    family = " ".join(name.split(" ")[1:])
                except ValueError:
                    family = ""
                Users2.create(upid, '', given, family, 2, studentid, email, None, 'feed', '', True)
                break
        else:
            log(ERROR, "Error running user feed for existing account %s" % user_id )
    return


def user_update_details_from_feed(uid, upid):
    """ Refresh the user's details from the feed. Maybe their name or ID has changed.
    """
    for feed in UFeeds.all_list():
        try:
            out = feeds_run_user_script(feed.script, args=[upid, ])
        except BaseException, err:
            log(ERROR, "Exception running user feed '%s': %s" % (feed.script, err))
            continue

        res = out.splitlines()
        if res[0].startswith("ERROR"):
            log(ERROR, "Error running user feed '%s': %s" % (feed.script, res))
            continue

        line = res[1]
        studentid = ""
        try:
            (upid, name, email, studentid) = line.split(',')

        except ValueError:
            try:
                (upid, name, email) = line.split(',')
            except ValueError:
                continue

        given = name.split(" ")[0]
        try:
            family = " ".join(name.split(" ")[1:])
        except ValueError:
            family = ""

        Users.set_email(uid, email)
        Users.set_givenname(uid, given)
        Users.set_familyname(uid, family)
        Users.set_studentid(uid, studentid)