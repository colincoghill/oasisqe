# -*- coding: utf-8 -*-

""" Code that links OASIS with external systems.

    Anything that wants to run an external program or connect over the network
    (except to OASIS database or memcache servers) should come through here.
"""

from oasis.lib import OaConfig, Groups, Feeds, DB, Users2, UFeeds, Users, Topics, QEditor
import os
import subprocess
import tempfile
import json
import zipfile
import shutil
from StringIO import StringIO

from logging import getLogger

L = getLogger("oasisqe")


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
    except BaseException as err:
        L.error("Exception in group feed '%s': %s" % (scriptrun, err))
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
            L.info("Group feed contained unknown user account %s" % uname)
            unknown.append(uname)
            continue
        if uname not in old_members:
            group.add_member(uid)
            added.append(uname)

    for uname in old_members:
        if uname not in new_members:
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
                except BaseException as err:
                    L.error("Exception in user feed '%s': %s" % (feed.script, err))
                    continue

                res = out.splitlines()
                if res[0].startswith("ERROR"):
                    L.error("Error running user feed '%s': %s" % (feed.script, res))
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
                Users2.create(upid,
                              '',
                              given,
                              family,
                              2,
                              studentid,
                              email,
                              None,
                              'feed',
                              '',
                              True)
                break
        else:
            L.error("Error running user feed for existing account %s" % user_id)
    return


def user_update_details_from_feed(uid, upid):
    """ Refresh the user's details from feed. Maybe their name or ID changed.
    """
    for feed in UFeeds.all_list():
        try:
            out = feeds_run_user_script(feed.script, args=[upid, ])
        except BaseException as err:
            L.error("Exception running user feed '%s': %s" % (feed.script, err))
            continue

        res = out.splitlines()
        if res[0].startswith("ERROR"):
            L.error("Error running user feed '%s': %s" % (feed.script, res))
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


def topic_to_zip(topic_id):
    """
    :param topic_id: ID of the topic to export
    :return: binary string containing ZIPped data
    """

    topic = Topics.get_topic(topic_id)
    qts = Topics.get_qts(topic_id)

    return qts_to_zip(qts, extra_info={'topic': topic})


# need to make a version that export a whole topic, with position info
def qts_to_zip(qt_ids, extra_info=None):
    """ Take a list of QTemplate IDs and return a binary string containing
        them as an .oaq file.
        (a zip file in special format)
    """

    qdir = tempfile.mkdtemp(prefix="oa")
    info = {
        'oasis': {
            'oa_version': "3.9.4",
            'qt_version': '0.9',
            'url': OaConfig.parentURL
        },
        'qtemplates': {},
        'extra': extra_info
    }

    arc = zipfile.ZipFile(os.path.join(qdir, "oasisqe.zip"),
                          'w',
                          zipfile.ZIP_DEFLATED)
    for qt_id in qt_ids:
        qtemplate = DB.get_qtemplate(qt_id)
        qtdir = os.path.join(qdir, str(qt_id))
        attachments = DB.get_qt_atts(qt_id)
        if 'qtemplate.html' not in attachments:
            attachments.append('qtemplate.html')
        if 'datfile.txt' not in attachments:
            attachments.append('datfile.txt')
        if 'image.gif' not in attachments:
            attachments.append('image.gif')
        os.mkdir(qtdir)
        os.mkdir(os.path.join(qtdir, "attach"))
        info["qtemplates"][qt_id] = {'qtemplate': qtemplate}
        info["qtemplates"][qt_id]["attachments"] = []
        info["qtemplates"][qt_id]["position"] = DB.get_qtemplate_practice_pos(qt_id)

        for name in attachments:
            if not name:
                name = 'UNKNOWN'
            mtype = DB.get_qt_att_mimetype(qt_id, name)
            if not mtype:
                mtype = ""
            data = DB.get_qt_att(qt_id, name)
            if not data:
                data = ""
            info["qtemplates"][qt_id]["attachments"].append([name, mtype, len(data)])
            subdir = os.path.join(qtdir, "attach", name)
            outf = open(subdir, "wb")
            outf.write(data)
            outf.close()
            arc.write(subdir,
                      os.path.join("%s" % qt_id, "attach", name),
                      zipfile.ZIP_DEFLATED)

    infof = open(os.path.join(qdir, "info.json"), "wb")
    infof.write(json.dumps(info))
    infof.close()
    arc.write(os.path.join(qdir, "info.json"),
              os.path.join("info.json"),
              zipfile.ZIP_DEFLATED)
    arc.close()

    readback = open(os.path.join(qdir, "oasisqe.zip"), "rb")
    data = readback.read()
    readback.close()
    shutil.rmtree(qdir)
    return data


def import_qts_from_zip(data, topic_id):
    """ Open the given OAQ file and import any qtemplates found.
        Return False if it's not valid
        Return 0 if it's valid but has no qtemplates
        Return NUM of templates imported.
    """

    # TODO: How do we protect against malicious uploads?
    # At the moment they're allowed for trusted people only,
    # but we'll eventually want this in the UI for end users.

    # eg.    unzip to huge size
    # add digital signatures?

    sdata = StringIO(data)
    tmpd = tempfile.mkdtemp(prefix="oa")
    qdir = os.path.join(tmpd, "oasisqe")
    os.mkdir(qdir)
    num = 0
    try:
        with zipfile.ZipFile(sdata, "r") as zfile:

            zfile.extractall(qdir)
            data = open("%s/info.json" % qdir, "r").read()
            info = json.loads(data)
            qtids = info['qtemplates'].keys()
            qtids.sort()
            for qtid in qtids:
                qtemplate = info['qtemplates'][qtid]['qtemplate']
                attachments = info['qtemplates'][qtid]['attachments']
                if 'position' in info['qtemplates'][qtid]:
                    position = info['qtemplates'][qtid]['position']
                else:
                    position = 0
                newid = DB.create_qt(1,   # ownerid
                                     qtemplate['title'],
                                     qtemplate['description'],
                                     qtemplate['marker'],
                                     qtemplate['scoremax'],
                                     qtemplate['status'])

                DB.move_qt_to_topic(newid, topic_id, position)
                num += 1

    #            print "%s attachments" % len(attachments)
                for att in attachments:
                    (att_name, att_type, att_size) = att
                    data = open("%s/%s/attach/%s" % (qdir, qtemplate['id'], att_name)).read()
                    DB.create_qt_att(newid, att_name, att_type, data, 1)
                    if att_name == "datfile.txt" or att_name == "datfile.dat" or att_name == "datfile" or att_name == "_datfile" or att_name == "__datfile":
                        qvars = QEditor.parse_datfile(data)
      #                  print "generating variations..."
                        for row in range(0, len(qvars)):
                            DB.add_qt_variation(newid, row + 1, qvars[row], 1)
    except zipfile.BadZipfile:
        return False
    Topics.flush_num_qs(topic_id)
    return num


#"36": {"qtemplate": {"status": 0, "marker": 1, "version": 49, "scoremax": null, "description": "No Description",
#                     "title": "Q5", "owner": 4, "id": 36, "embed_id": ""},
#       "attachments": [["UNKNOWN", "", 0], ["datfile.txt", "text/plain", 649], ["q5", "image/gif", 7083],
#                       ["q5a", "image/gif", 1216], ["q5b", "image/gif", 1222], ["q5c", "image/gif", 1367],
#                       ["q5d", "image/gif", 1355], ["qtemplate.html", "text/plain", 219], ["image.gif", "", 0]]}
