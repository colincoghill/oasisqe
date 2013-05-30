""" Test question engine related tasks.
    Creating qtemplates, generating instances, marking, etc.
"""

# One day we'll break the qengine into its own API, for now we just hit
# code from all over the place :)

import datetime

from oasis.lib import General, DB

DB.upgradeDB()


def test_instance_generate_simple_answer():
    """ Convert some html templates + variables into resulting instance HTML
        and make sure it's doing it right. Focus on simple "ANSWER"

        No side effects.
    """

    tmpl = "blah<ANSWER1>blah"
    qvars = {  }
    html = """blah<INPUT class='auto_save' TYPE='text' NAME='ANS_1' VALUE="VAL_1"/>blah"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html

    tmpl = "blah<ANSWER2>blah"
    qvars = {  }
    html = """blah<INPUT class='auto_save' TYPE='text' NAME='ANS_2' VALUE="VAL_2"/>blah"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html

    tmpl = "foo<ANSWER1>blah<ANSWER2>blah"
    qvars = {  }
    html = """foo<INPUT class='auto_save' TYPE='text' NAME='ANS_1' VALUE="VAL_1"/>blah<INPUT class='auto_save' TYPE='text' NAME='ANS_2' VALUE="VAL_2"/>blah"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html


def test_instance_generate_multif_answer():
    """ Convert some html templates + variables into resulting instance HTML
        and make sure it's doing it right. Focus on multif choice "ANSWER"

        No side effects.
    """

    tmpl = "blah<ANSWER1 MULTIF f,g,h,i>blah"
    qvars = { 'f': 7, 'g': "joe", "h": "3.4", "i": 33 }
    html = """blah<table border=0><tr><td>Please choose one:</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='1' Oa_CHK_1_1>7</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='2' Oa_CHK_1_2>joe</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='3' Oa_CHK_1_3>3.4</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='4' Oa_CHK_1_4>33</td></tr></table><br />
blah"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html

    tmpl = "blah<ANSWER1 MULTIF f,g,h,i,j>blah"
    qvars = { 'f': 7, 'g': "joe", "h": "3.4", "i": 33, "j": "&amp;" }
    html = """blah<table border=0><tr><td>Please choose one:</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='1' Oa_CHK_1_1>7</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='2' Oa_CHK_1_2>joe</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='3' Oa_CHK_1_3>3.4</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='4' Oa_CHK_1_4>33</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='5' Oa_CHK_1_5>&amp;</td></tr></table><br />
blah"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html

    tmpl = "blah<ANSWER1 MULTIF f,g,h,"
    qvars = { 'f': 7, 'g': "joe", "h": "3.4", "i": 33, "j": "&amp;" }
    html = """blah<ANSWER1 MULTIF f,g,h,"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html

    tmpl = "blah<ANSWER1 MULTIF f,g,h,i,j>"
    qvars = { 'f': 7, 'g': "joe" }
    html = """blah<table border=0><tr><td>Please choose one:</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='1' Oa_CHK_1_1>7</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='2' Oa_CHK_1_2>joe</td><FONT COLOR="red">ERROR IN QUESTION DATA</FONT><FONT COLOR="red">ERROR IN QUESTION DATA</FONT><FONT COLOR="red">ERROR IN QUESTION DATA</FONT></tr></table><br />\n"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html


def test_instance_generate_multiv_answer():
    """ Convert some html templates + variables into resulting instance HTML
        and make sure it's doing it right. Focus on multif choice "ANSWER"

        No side effects.
    """

    tmpl = "blah<ANSWER1 MULTIV f,g,h,i>blah"
    qvars = { 'f': 7, 'g': "joe", "h": "3.4", "i": 33 }
    html = """blah<table border=0><tr><th>Please choose one:</th></tr><tr><th>a)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='1' Oa_CHK_1_1></td><td CLASS='multichoicecell'> 7</td></tr><tr><th>b)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='2' Oa_CHK_1_2></td><td CLASS='multichoicecell'> joe</td></tr><tr><th>c)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='3' Oa_CHK_1_3></td><td CLASS='multichoicecell'> 3.4</td></tr><tr><th>d)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='4' Oa_CHK_1_4></td><td CLASS='multichoicecell'> 33</td></tr></table><br />
blah"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html

    tmpl = "blah<ANSWER1 MULTIV f,g,h,i,j>blah"
    qvars = { 'f': 7, 'g': "joe", "h": "3.4", "i": 33, "j": "&amp;" }
    html = """blah<table border=0><tr><th>Please choose one:</th></tr><tr><th>a)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='1' Oa_CHK_1_1></td><td CLASS='multichoicecell'> 7</td></tr><tr><th>b)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='2' Oa_CHK_1_2></td><td CLASS='multichoicecell'> joe</td></tr><tr><th>c)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='3' Oa_CHK_1_3></td><td CLASS='multichoicecell'> 3.4</td></tr><tr><th>d)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='4' Oa_CHK_1_4></td><td CLASS='multichoicecell'> 33</td></tr><tr><th>e)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='5' Oa_CHK_1_5></td><td CLASS='multichoicecell'> &amp;</td></tr></table><br />
blah"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html


def test_instance_generate_listbox_answer():
    """ Convert some html templates + variables into resulting instance HTML
        and make sure it's doing it right. Focus on listbox "ANSWER SELECT"

        No side effects.
    """

    tmpl = "blah<ANSWER1 SELECT f,g,h,i>blah"
    qvars = { 'f': 7, 'g': "joe", "h": "3.4", "i": 33 }
    html = """<SELECT class='auto_save' NAME='ANS_1'>Please choose:<OPTION VALUE='None'>--Choose--</OPTION><OPTION VALUE='1' Oa_SEL_1_1>7</OPTION><OPTION VALUE='2' Oa_SEL_1_2>joe</OPTION><OPTION VALUE='3' Oa_SEL_1_3>3.4</OPTION><OPTION VALUE='4' Oa_SEL_1_4>33</OPTION></SELECT>\n"""
    res = General.handle_listbox(tmpl, 1, qvars, shuffle=False)[1]
    assert res == html


def test_instance_generate_multi_answer():
    """ Convert some html templates + variables into resulting instance HTML
        and make sure it's doing it right. Focus on multi "ANSWER MULTI"

        No side effects.
    """

    tmpl = "blah<ANSWER1 MULTI f,g,h,i>blah"
    qvars = { 'f': 7, 'g': "joe", "h": "3.4", "i": 33 }
    html = """<table border=0><tr><th>Please choose one:</th><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='1' Oa_CHK_1_1> 7</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='2' Oa_CHK_1_2> joe</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='3' Oa_CHK_1_3> 3.4</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='4' Oa_CHK_1_4> 33</td></tr></table><br />\n"""
    res = General.handle_multi(tmpl, 1, qvars, shuffle=False)[1]
    assert res == html


def test_instance_generate_variable():
    """ Convert some html templates + variables into resulting instance HTML
        and make sure it's doing it right. Focus on variable subs.

        No side effects.
    """

    tmpl = "The value is <VAL A>"
    qvars = { "A": 7, "a": 5, "Arthur": 3 }
    html = """The value is 7"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html

    tmpl = "The value is <VAL A> <VAL Arthur>"
    qvars = { "A": 7, "a": 5, "Arthur": 3 }
    html = """The value is 7 3"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html

    tmpl = "The value is <VAL A> <VAL Arthur>"
    qvars = { "A": "&amp;", "a": 5, "Arthur": 3 }
    html = """The value is &amp; 3"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html

    tmpl = "The value is <VAL A> <VAL Arthur>"
    qvars = { "A": "<blink>annoying</blink>", "a": 5, "Arthur": 3 }
    html = """The value is <blink>annoying</blink> 3"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html

    tmpl = "The value is <VAL A> <VAL Arthur>"
    qvars = { "A": u"\x9f", "a": 5, "Arthur": 3 }
    html = u"""The value is \x9f 3"""
    res = General.gen_q_html(qvars, tmpl)
    assert res == html


def test_html_esc():
    """ Check that our HTML escaping works ok. ( & -> &amp;  etc)
    """

    assert "&amp;" == General.htmlesc("&")
    assert "&lt;" == General.htmlesc("<")
    assert "&gt;" == General.htmlesc(">")


def test_date_ops():
    """ Test our various date operations
    """

    a = datetime.date(2013,12,1)
    b = datetime.date(2013,12,2)
    c = datetime.date(2013,11,1)
    d = datetime.date(2012,11,1)

    assert General.isBetween(a,c,b) is True
    assert General.isBetween(a,b,c) is True
    assert General.isBetween(a,c,d) is False



