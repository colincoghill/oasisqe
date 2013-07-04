# -*- coding: utf-8 -*-
#
# This code is under the GNU Affero General Public License
# http://www.gnu.org/licenses/agpl-3.0.html

""" Main entry point. This uses Flask to provide a WSGI app, it should be
    run from a WSGI web server such as Apache or Nginx. """

# We include the views covering logging in/out and account signup and related.

from flask import Flask, session, redirect, url_for, request, \
    render_template, flash, abort
import datetime
import os
import _strptime  # import should prevent thread import blocking issues
                  # ask Google about:     AttributeError: _strptime
import logging
from logging import log, INFO, ERROR
from logging.handlers import SMTPHandler, RotatingFileHandler
from functools import wraps
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from oasis.lib import OaConfig, Users2, Users, DB
from oasis.lib.Audit import audit
from oasis.lib.Permissions import satisfy_perms

app = Flask(__name__,
            template_folder=os.path.join(OaConfig.homedir, "templates"),
            static_folder=os.path.join(OaConfig.homedir, "static"),
            static_url_path=os.path.join(os.path.sep, OaConfig.staticpath, "static"))
app.secret_key = OaConfig.secretkey
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB max file size upload

# Email error messages to admins ?
if OaConfig.email_admins:
    MH = SMTPHandler(OaConfig.smtp_server,
                     OaConfig.email,
                     OaConfig.email_admins,
                     'OASIS Internal Server Error')
    MH.setLevel(logging.ERROR)
    app.logger.addHandler(MH)

app.debug = False

if not app.debug:  # Log info or higher
    try:
        FH = RotatingFileHandler(filename=OaConfig.logfile)
        FH.setLevel(logging.INFO)
        FH.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s | %(pathname)s:%(lineno)d"
        ))
        app.logger.addHandler(FH)
        logging.log(logging.INFO,
                    "File logger starting up")
    except IOError, err:  # Probably a permission denied or folder not exist
        logging.log(logging.ERROR,
                    """Unable to open log file: %s""" % err)


@app.context_processor
def template_context():
    """ Useful values for templates to always have access to"""
    if 'username' in session:
        username = session['username']
    else:
        username = None

    if "user_fullname" in session:
        user_fullname = session['user_fullname']
    else:
        user_fullname = None
    today = datetime.date.today()

    if "user_authtype" in session:
        auth_type = session['user_authtype']
    else:
        auth_type = "none"
    return {'cf': {
        'static': OaConfig.staticURL + u"/static/",
        'url': OaConfig.parentURL + u"/",
        'username': username,
        'userfullname': user_fullname,
        'email': OaConfig.email,
        'today': today,
        'auth_type': auth_type,
        'feed_path': OaConfig.feed_path,
        'open_registration': OaConfig.open_registration,
        'enable_local_login': OaConfig.enable_local_login,
        'enable_webauth_login': OaConfig.enable_webauth_login,
    }}


def authenticated(func):
    """ Decorator to check the user is currently authenticated and
        deal with the session/redirect """
    @wraps(func)
    def call_fn(*args, **kwargs):
        """ If they're not in session, redirect them and remember where
            they were going.
        """
        if 'user_id' not in session:
            session['redirect'] = request.path
            return redirect(url_for('index'))
        return func(*args, **kwargs)

    return call_fn


def require_perm(perms, redir="setup_top"):
    """ Decorator to check the user has at least one of a given list of global
        perms.
        Will flash() a message to them and redirect if they don't.

        example:

        @app.route(...)
        @require_perm('sysadmin', url_for('index'))
        def do_stuff():

        or

        @app.route(...)
        @require_perm(['sysadmin', 'useradmin'], url_for['admin'])
        def do_stuff():
    """

    def decorator(func):
        """ Handle decorator
        """
        @wraps(func)
        def call_fn(*args, **kwargs):
            """ check auth first, can't have perms if we're not.
            """
            if 'user_id' not in session:
                session['redirect'] = request.path
                return redirect(url_for('index'))

            user_id = session['user_id']

            if isinstance(perms, str):
                permlist = (perms,)
            else:
                permlist = perms

            if satisfy_perms(user_id, 0, permlist):
                return func(*args, **kwargs)
            flash("You do not have permission to do that.")
            return redirect(url_for(redir))

        return call_fn

    return decorator


def require_course_perm(perms, redir=None):
    """ Decorator to check the user has at least one of a given list of course
        perms.
        Will flash() a message to them and redirect if they don't.

        example:

        @app.route(...)
        @require_perm('sysadmin', url_for('index'))
        def do_stuff():

        or

        @app.route(...)
        @require_perm(['sysadmin', 'useradmin'], url_for['admin'])
        def do_stuff():
    """

    def decorator(func):
        """ Handle decorator
        """
        @wraps(func)
        def call_fn(*args, **kwargs):
            """ check auth first, can't have perms if we're not.
            """
            if 'user_id' not in session:
                session['redirect'] = request.path
                return redirect(url_for('index'))

            user_id = session['user_id']

            if isinstance(perms, str):
                permlist = (perms,)
            else:
                permlist = perms

            course_id = kwargs['course_id']

            if satisfy_perms(user_id, course_id, permlist):
                return func(*args, **kwargs)
            flash("You do not have course permission to do that.")
            if redir:
                return redirect(url_for(redir))
            else:
                return redirect(url_for("cadmin_top", course_id=course_id))

        return call_fn

    return decorator


@app.route("/")
def index():
    """ Main landing page. Welcome them and give them some login instructions.
    """
    if 'user_id' in session:
        return redirect(url_for("main_top"))

    if OaConfig.default == "landing":
        return render_template("landing_page.html")
    if OaConfig.default == "locallogin":
        return redirect(url_for("login_local"))
    if OaConfig.default == "webauth":
        return redirect(url_for("login_webauth_submit"))
    return render_template("landing_page.html")


@app.route("/login/local/")
def login_local():
    """ Present a login page for people with local OASIS accounts to log in"""

    mesg_login = DB.get_message("loginmotd")
    return render_template("login_screen_local.html", mesg_login=mesg_login)


@app.route("/login/local/submit", methods=['POST', ])
def login_local_submit():
    """ They've entered some credentials on the local login screen.
        Check them, then set up the session or redirect back with an error.
    """
    if not 'username' in request.form or not 'password' in request.form:
        log(INFO, "Failed Login")
        flash("Incorrect name or password.")
        return redirect(url_for("login_local"))

    username = request.form['username']
    password = request.form['password']

    user_id = Users2.verify_pass(username, password)
    if not user_id:
        log(INFO, "Failed Login for %s" % username)
        flash("Incorrect name or password.")
        return redirect(url_for("login_local"))

    user = Users2.get_user(user_id)
    if not user['confirmed']:
        flash("""Your account is not yet confirmed. You should have received
                 an email with instructions in it to do so.""")
        return redirect(url_for("login_local"))
    session['username'] = username
    session['user_id'] = user_id
    session['user_givenname'] = user['givenname']
    session['user_familyname'] = user['familyname']
    session['user_fullname'] = user['fullname']
    session['user_authtype'] = "local"

    audit(1, user_id, user_id, "UserAuth",
          "%s successfully logged in locally" % (session['username'],))

    if 'redirect' in session:
        log(INFO, "Following redirect for %s" % username)
        target = OaConfig.parentURL + session['redirect']
        del session['redirect']
        return redirect(target)
    log(INFO, "Successful Login for %s" % username)
    return redirect(url_for("main_top"))


@app.route("/login/signup")
def login_signup():
    """ Present a signup page for people to register a new account."""
    if not OaConfig.open_registration:
        abort(404)

    return render_template("login_signup.html")


@app.route("/login/forgot_pass")
def login_forgot_pass():
    """ Ask them for their username to begin forgotten password process."""

    return render_template("login_forgot_pass.html")


@app.route("/login/forgot_pass/submit", methods=["POST", ])
def login_forgot_pass_submit():
    """ Forgot their password. Grab their username and send them a reset email.
    """

    if "cancel" in request.form:
        flash("Password reset cancelled.")
        return redirect(url_for("login_local"))

    username = request.form.get('username', None)

    if username == "admin":
        flash("""The admin account cannot do an email password reset,
                 please see the Installation instructions.""")
        return redirect(url_for("login_forgot_pass"))

    if username:
        user_id = Users2.uid_by_uname(username)
    else:
        user_id = None

    if not user_id:
        flash("Unknown username ")
        return redirect(url_for("login_forgot_pass"))

    user = Users2.get_user(user_id)
    if not user['source'] == "local":
        flash("Your password is not managed by OASIS, "
              "please contact IT Support.")
        return redirect(url_for("login_forgot_pass"))

    code = Users.gen_confirm_code()
    Users.set_confirm_code(user_id, code)

    email = user['email']
    if not email:
        flash("We do not appear to have an email address on file for "
              "that account.")
        return redirect(url_for("login_forgot_pass"))

    text_body = render_template(os.path.join("email", "forgot_pass.txt"), code=code)
    html_body = render_template(os.path.join("email", "forgot_pass.html"), code=code)
    send_email(user['email'],
               from_addr=None,
               subject="OASIS Password Reset",
               text_body=text_body,
               html_body=html_body)

    return render_template("login_forgot_pass_submit.html")


@app.route("/login/confirm/<string:code>")
def login_confirm(code):
    """ They've clicked on a confirmation link."""
    if not OaConfig.open_registration:
        abort(404)

    if len(code) > 20:
        abort(404)

    uid = Users.verify_confirm_code(code)
    if not uid:
        abort(404)
    Users.set_confirm(uid)
    Users.set_confirm_code(uid, "")
    return render_template("login_signup_confirmed.html")


@app.route("/login/email_passreset/<string:code>")
def login_email_passreset(code):
    """ They've clicked on a password reset link.
        Log them in (might as well) and send them to the password reset page."""
    # This will also confirm their email if they haven't.
    # Doesn't seem to be any harm in doing that

    if len(code) > 20:
        abort(404)

    uid = Users.verify_confirm_code(code)
    if not uid:
        abort(404)
    Users.set_confirm(uid)
    Users.set_confirm_code(uid, "")
    user = Users2.get_user(uid)
    session['username'] = user['uname']
    session['user_id'] = uid
    session['user_givenname'] = user['givenname']
    session['user_familyname'] = user['familyname']
    session['user_fullname'] = user['fullname']
    session['user_authtype'] = "local"
    audit(1, uid, uid, "UserAuth",
          "%s logged in using password reset email" % (session['username'],))

    flash("Please change your password")
    return redirect(url_for("setup_change_pass"))


@app.route("/login/signup/submit", methods=['POST', ])
def login_signup_submit():
    """ They've entered some information and want an account.
        Do some checks and send them a confirmation email if all looks good.
    """
    # TODO: How do we stop someone using this to spam someone?
    if not OaConfig.open_registration:
        abort(404)
    form = request.form
    if not ('username' in form
            and 'password' in form
            and 'confirm' in form
            and 'email' in form):
        flash("Please fill in all fields")
        return redirect(url_for("login_signup"))

    username = form['username']
    password = form['password']
    confirm = form['confirm']
    email = form['email']

    # TODO: Sanitize username
    if username == "" or password == "" or confirm == "" or email == "":
        flash("Please fill in all fields")
        return redirect(url_for("login_signup"))

    if not confirm == password:
        flash("Passwords don't match")
        return redirect(url_for("login_signup"))

    # basic checks in case they entered their street address or something
    # a fuller check is too hard or prone to failure
    if not "@" in email or not "." in email:
        flash("Email address doesn't appear to be valid")
        return redirect(url_for("login_signup"))

    existing = Users2.uid_by_uname(username)
    if existing:
        flash("An account with that name already exists, "
              "please try another username.")
        return redirect(url_for("login_signup"))

    code = Users.gen_confirm_code()
    newuid = Users.create(uname=username,
                          passwd="NOLOGIN",
                          email=email,
                          givenname=username,
                          familyname="",
                          acctstatus=1,
                          studentid="",
                          source="local",
                          confirm_code=code,
                          confirm=False)
    Users2.set_password(newuid, password)

    text_body = render_template(os.path.join("email", "confirmation.txt"), code=code)
    html_body = render_template(os.path.join("email", "confirmation.html"), code=code)
    send_email(email,
               from_addr=None,
               subject="OASIS Signup Confirmation",
               text_body=text_body,
               html_body=html_body)

    return render_template("login_signup_submit.html", email=email)


@app.route("/login/webauth/error")
def login_webauth_error():
    """ They've tried to use web authentication but the web server doesn't
        appear to be providing the right credentials. Display an error page.
    """

    return render_template("login_webauth_error.html")


@app.route("/login/webauth/submit")
def login_webauth_submit():
    """ The web server should have verified their credentials and
        provide it in env['REMOTE_USER']
        Check them, then set up the session or redirect back with an error.
        If we haven't seen them before, check with our user account feed(s)
        to see if we can find them.
    """
    if not 'REMOTE_USER' in request.environ:
        log(ERROR, "REMOTE_USER not provided by web server and 'webauth' is being attempted.")
        return redirect(url_for("login_webauth_error"))

    username = request.environ['REMOTE_USER']

    if '@' in username:
        username = username.split('@')[0] #  TODO: this is for UofA, how do we make it more general?
    user_id = Users2.uid_by_uname(username)
    if not user_id:
        Users2.create(username, '', '', '', 1, '', '', None, 'unknown', '', True)
        user_id = Users2.uid_by_uname(username)

    user = Users2.get_user(user_id)
    session['username'] = username
    session['user_id'] = user_id
    session['user_givenname'] = user['givenname']
    session['user_familyname'] = user['familyname']
    session['user_fullname'] = user['fullname']
    session['user_authtype'] = "httpauth"

    audit(1, user_id, user_id, "UserAuth",
          "%s successfully logged in via webauth" % session['username'])

    if 'redirect' in session:
        target = OaConfig.parentURL + session['redirect']
        del session['redirect']
        return redirect(target)

    return redirect(url_for("main_top"))


def send_email(to_addr, from_addr=None, subject="Message from OASIS",
               text_body=None, html_body=None):
    """ Send an email to the given address.
        You must provide both an html body and a text body.

        If "from_addr" is not specified, use the default from the config file.

        Will not attempt to validate the email addresses, please do so before
        calling, but will check the database for blacklisted addresses.

        Returns True if successful, and a string containing human readable error
        message of it fails, or refuses.

        :param to_addr:  string containing the email address to send to
        :param from_addr: string containing the email address the mail is from
        :param subject: string containing the text to put in the Subject line
        :param text_body: the main text of the email
        :param html_body: an HTML version of the main text, for recipients
                          that support it.
    """

    # TODO: attempt to not send email to the same address too often,
    # to prevent us being used to annoy someone.

    _blacklist = []

    if to_addr in _blacklist:
        return "Attempting to send to blacklisted address."

    if not from_addr:
        from_addr = OaConfig.email

    if not text_body and not html_body:
        return "Attempting to send empty email"

    # Create message container - the correct MIME type is multipart/alternative.
    _msg = MIMEMultipart('alternative')
    _msg['Subject'] = subject
    _msg['From'] = from_addr
    _msg['To'] = to_addr

    # Record the MIME types of both parts - text/plain and text/html.
    _part1 = MIMEText(text_body, 'plain')
    _part2 = MIMEText(html_body, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multi-part message, in this case
    # the HTML message, is best and preferred.
    _msg.attach(_part1)
    _msg.attach(_part2)

    # Send the message via local SMTP server.
    _smtp = smtplib.SMTP(OaConfig.smtp_server)
    # sendmail function takes 3 arguments: sender's address, recipient's address
    # and message to send - here it is sent as one string.
    _smtp.sendmail(from_addr, to_addr, _msg.as_string())
    _smtp.quit()

    return True


from oasis import views_practice
from oasis import views_assess
from oasis import views_cadmin
from oasis import views_admin
from oasis import views_setup
from oasis import views_api
from oasis import views_embed
from oasis import views_misc
