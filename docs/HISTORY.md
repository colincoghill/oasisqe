
OASIS
-----

Notes from the main programmer. 26 May 2015.


Back in 1997, at the University of Auckland, my then boss, Professor John Boys, came to me with an idea for a web based
program to assist with teaching by providing practice questions to students. While there were some existing "quiz"
programs around, there was nothing that focused on repeated practice, especially for large classes.

I wrote a prototype (using PHP and MySQL) which could present a few numerical questions with semi-randomly varying
values, and we deployed it for use in a second year electronics course. Feedback and many initial suggestions that
shaped the first system came from Dr Abbas Bigdeli, one of the first lecturers to trial OASIS.
Thus was the OASIS system born.

After a year of successful use, we realised that it wouldn't be hard to modify the system to provide automated marking
of assessments, and this became version 2. It was still very "prototype" and needed a lot of programmer attention to
do things like set up assignments or extract results. Several more courses picked up the system and used it on
a trial basis.

I was, at the time, working as a software developer while studying, and I needed to prove to the university that I
was capable of study at a higher level than in the past. So I designed and programmed OASIS version 3. This served
the dual role of working as a production system to serve practice questions and assessments to our students, but also
as a research platform for academics to experiment and measure e-learning related things. This was built using the
Python programming language and the PostgreSQL database. Using Python was a bit of a gamble - the language was
relatively unknown at the time, and I was just learning it - but my instincts told me it was the right choice.
A decade later and Python is a lot more known and respected, and I'm very happy with that choice.

OASIS v3 was finished in approximately 2001, and has been a solid base for the last decade or so. Over time we have
added more features, often from student projects. Apart from occasional bug-fixes and minor additions, the
last major work was done in 2004.

In 2012 while the Engineering Faculty was going through the large number of software applications we have, a good look
at OASIS concluded that the software was still strong and very much useful to the Faculty. However, the code was old,
using some components that haven't been supported for many years, and contained some security issues that weren't
known about when the system was first designed. We also intend to scale the system up, to support a larger number
of students.

During the end of 2012 and the start of 2013 I have gone through the OASIS code, changing out no longer supported
components, fixing security issues, and restructuring the code to make it more maintainable. A more modern look
and feel came naturally since I had to replace all the HTML anyway.

As an extra, I have focused on turning OASIS into more of a standalone application, designed so that other
organizations can install and use it. In the past a few have done so, but installation and running of the system
has always been relatively complex. The code has been placed under the open source GNU "AGPL" license.

Right now, most of the work has been done, the system is running as a "beta" in the Faculty and appears to be working
well. The open source release needs a few extra parts to be useful to other people.

I intend to do a short series of releases, the first being a fully functional practice system, then adding core
features - assessment, external authentication, etc - until it is functionally equivalent to the old system
that has worked so well for our Faculty. This will be OASIS v4.

Then I can start doing the more exciting stuff again and add new features for v4.1 and into the future!


- Colin
