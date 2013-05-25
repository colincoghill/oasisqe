""" Test question engine related tasks.
    Creating qtemplates, generating instances, marking, etc.
"""

# One day we'll break the qengine into its own API, for now we just hit
# code from all over the place :)



from oasis.lib import OaGeneral, OaDB

OaDB.upgradeDB()


def test_instance_generate_simple_answer():
    """ Convert some html templates + variables into resulting instance HTML
        and make sure it's doing it right. Focus on simple "ANSWER"

        No side effects.
    """

    tmpl = "blah<ANSWER1>blah"
    qvars = {  }
    html = """blah<INPUT class='auto_save' TYPE='text' NAME='ANS_1' VALUE="VAL_1"/>blah"""
    res = OaGeneral.generateQuestionHTML(qvars, tmpl)
    assert res == html

    tmpl = "blah<ANSWER2>blah"
    qvars = {  }
    html = """blah<INPUT class='auto_save' TYPE='text' NAME='ANS_2' VALUE="VAL_2"/>blah"""
    res = OaGeneral.generateQuestionHTML(qvars, tmpl)
    assert res == html

    tmpl = "foo<ANSWER1>blah<ANSWER2>blah"
    qvars = {  }
    html = """foo<INPUT class='auto_save' TYPE='text' NAME='ANS_1' VALUE="VAL_1"/>blah<INPUT class='auto_save' TYPE='text' NAME='ANS_2' VALUE="VAL_2"/>blah"""
    res = OaGeneral.generateQuestionHTML(qvars, tmpl)
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
    res = OaGeneral.generateQuestionHTML(qvars, tmpl)
    assert res == html

    tmpl = "blah<ANSWER1 MULTIF f,g,h,i,j>blah"
    qvars = { 'f': 7, 'g': "joe", "h": "3.4", "i": 33, "j": "&amp;" }
    html = """blah<table border=0><tr><td>Please choose one:</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='1' Oa_CHK_1_1>7</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='2' Oa_CHK_1_2>joe</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='3' Oa_CHK_1_3>3.4</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='4' Oa_CHK_1_4>33</td><td CLASS='multichoicecell'><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='5' Oa_CHK_1_5>&amp;</td></tr></table><br />
blah"""
    res = OaGeneral.generateQuestionHTML(qvars, tmpl)
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
    res = OaGeneral.generateQuestionHTML(qvars, tmpl)
    print res
    assert res == html

    tmpl = "blah<ANSWER1 MULTIV f,g,h,i,j>blah"
    qvars = { 'f': 7, 'g': "joe", "h": "3.4", "i": 33, "j": "&amp;" }
    html = """blah<table border=0><tr><th>Please choose one:</th></tr><tr><th>a)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='1' Oa_CHK_1_1></td><td CLASS='multichoicecell'> 7</td></tr><tr><th>b)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='2' Oa_CHK_1_2></td><td CLASS='multichoicecell'> joe</td></tr><tr><th>c)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='3' Oa_CHK_1_3></td><td CLASS='multichoicecell'> 3.4</td></tr><tr><th>d)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='4' Oa_CHK_1_4></td><td CLASS='multichoicecell'> 33</td></tr><tr><th>e)</th><td><INPUT class='auto_save' TYPE='radio' NAME='ANS_1' VALUE='5' Oa_CHK_1_5></td><td CLASS='multichoicecell'> &amp;</td></tr></table><br />
blah"""
    res = OaGeneral.generateQuestionHTML(qvars, tmpl)
    print res
    assert res == html


def test_instance_generate_variable():
    """ Convert some html templates + variables into resulting instance HTML
        and make sure it's doing it right. Focus on variable subs.

        No side effects.
    """

    tmpl = "The value is <VAL A>"
    qvars = { "A": 7, "a": 5, "Arthur": 3 }
    html = """The value is 7"""
    res = OaGeneral.generateQuestionHTML(qvars, tmpl)
    assert res == html

    tmpl = "The value is <VAL A> <VAL Arthur>"
    qvars = { "A": 7, "a": 5, "Arthur": 3 }
    html = """The value is 7 3"""
    res = OaGeneral.generateQuestionHTML(qvars, tmpl)
    assert res == html

    tmpl = "The value is <VAL A> <VAL Arthur>"
    qvars = { "A": "&amp;", "a": 5, "Arthur": 3 }
    html = """The value is &amp; 3"""
    res = OaGeneral.generateQuestionHTML(qvars, tmpl)
    assert res == html

    tmpl = "The value is <VAL A> <VAL Arthur>"
    qvars = { "A": "<blink>annoying</blink>", "a": 5, "Arthur": 3 }
    html = """The value is <blink>annoying</blink> 3"""
    res = OaGeneral.generateQuestionHTML(qvars, tmpl)
    assert res == html

    tmpl = "The value is <VAL A> <VAL Arthur>"
    qvars = { "A": u"\x9f", "a": 5, "Arthur": 3 }
    html = u"""The value is \x9f 3"""
    res = OaGeneral.generateQuestionHTML(qvars, tmpl)
    assert res == html