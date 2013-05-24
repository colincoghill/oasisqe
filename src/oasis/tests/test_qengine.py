""" Test question engine related tasks.
    Creating qtemplates, generating instances, marking, etc.
"""

# One day we'll break the qengine into its own API, for now we just hit
# code from all over the place :)



from oasis.lib import OaGeneral


def test_instance_generate():
    """ Convert some html templates + variables into resulting instance HTML
        and make sure it's doing it right.

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
