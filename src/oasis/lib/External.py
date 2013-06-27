""" Code that links OASIS with external systems.

    Anything that wants to run an external program or connect over the network
    (except to OASIS database or memcache servers) should come through here.
"""

from oasis.lib import OaConfig, Groups, Feeds, Periods, Users2
from logging import log, ERROR, INFO
import os
import subprocess


def feeds_available_group_scripts():
    """ Return a list of file names of available group feed scripts.
    """

    feed_dir = os.path.join(OaConfig.feed_path, "group")
    files = [f
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

    cmd = [full_path,] + args
    output = subprocess.check_output(cmd)
    return output


def group_update_from_feed(group_id):
    """ Update group membership from it's feed
        Returns (added, removed, unknown) with usernames of users added or removed
    """

    group = Groups.Group(g_id=group_id)
    if not group.source == 'feed':
        return

    feed = Feeds.Feed(f_id=group.feed)
    period = Periods.Period(p_id=group.period)
    scriptrun = ' '.join([feed.script, group.feedargs, period.code])
    try:
        output = feeds_run_group_script(feed.script, args=[group.feedargs, period.code])
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

    return added, removed, unknown
