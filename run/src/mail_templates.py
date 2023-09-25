MAIL_INSTRUCTOR_INTRO="""
    <head/>
    <body>
        Hello {call_number} course staff,<br><br>

        We are now ready to invite you to use our new tool, High Resolution Course Feedback!<br><br>

        To briefly remind you of the context, we built a tool that could help you have a more precise understanding of the students in your course with higher temporal resolution over the quarter. It works by changing when we ask students for feedback and surveying a small subset of students each week.<br><br>

        <a href="{host_name}">This website</a> will help you to set up the tool for your course. Through this website, you can manage course survey admins, update the course roster and (optionally) set the questions to ask your students each week in addition to the default questions. Based on the roster, we will choose when and whom to survey each week and send them emails (from this address: <a href="mailto:hrcf@cs.stanford.edu">hrcf@cs.stanford.edu<a/>) with an anonymous feedback form on your behalf.<br><br>

        (By default we will survey each student twice throughout the quarter. If you wish to customize how many times to survey each student, please send an email to <a href="mailto:yunsung@stanford.edu">yunsung@stanford.edu</a>.)<br><br>

        Here is what a week of survey will look like:
        <ul>
          <li>From <b>Monday~Friday,</b> your students will be asked to fill out the feedback form.</li>
          <li>On <b>Sunday,</b> you will receive a weekly digest from us along with all the feedback sampled from your students.</li>
          <li>Changes to survey questions (and the new roster) will be reflected around <b>11:59pm on Sundays</b>. Any change you make go live then. </li>
        </ul>

        Detailed instructions on updating the course roster and customizing survey questions can be found in the website. Please email <a href="mailto:yunsung@stanford.edu">yunsung@stanford.edu</a> if you have any questions.<br><br>

        Thank you for your interest and participation!<br><br>

        All the best,<br>
        The High Resolution Course Feedback Team
    </body>
"""

_RESPONSE="""
    This week, a total of <b>{total_queried}</b> students in {call_number} were asked to provide feedback, among which <b>{answered}</b> students have responded. The response rate of your class was <b>{response_rate:.2f}</b>. (The response rate across all participating classes was <b>{all_response_rate:.2f}</b>.)<br><br>

    We have attached the feedback from your students in {call_number}. Please take note of the following:
    <ul>
        <li>Responses to each question (along with the question prompts and response counts) are organized into a single text file named by their prompt.</li>
        <li>Responses to "Rating" typed questions additionally have histogram representations also named by their prompt.</li>
        <li>The 'weekly_mood' image file shows the estimated weekly mood of your class throughout the quarter. Estimates for later weeks will be populated as the quarter progresses.
        <ul>
            <li>The mood estimates are based on the responses to a default qualitative rating question: "How would you rate your course experience so far?"</li>
            <li>Each number indicates the following qualitative assessment. 5: Excellent, 4: Good, 3: Ok, 2: Below Average, 1: Poor.</li>
        </ul>
        </li>
    </ul>
    <br>

    As you review your feedback, keep in mind that this feedback is from students, who may not necessarily be able to accurately judge what is or isn’t good teaching. Take it with a grain of salt! If you see a comment that surprises you, hopefully it is a useful opportunity to reflect and improve. Above all else, don’t let feedback detract from the joy of teaching.<br><br>
"""

_NO_RESPONSE="""
    This week, a total of <b>{total_queried}</b> students in {call_number} were asked to provide feedback, but we received <b>0</b> responses. (The response rate across all participating classes was <b>{all_response_rate:.2f}</b>.)<br><br>

    Please keep in mind that students are handling many things this term! Mentioning High Resolution Course Feedback during class and encouraging students to participate can greatly help elicit more valuable feedback. (This can also give a chance for them to look out for emails from us and prevent them from going to their spam folder, which happened in few rare cases.)<br><br>
"""

MAIL_REGULAR_DIGEST="""
    <head/>
    <body>
        Hello {call_number} course staff,<br><br>

        This is your High Resolution Course Feedback weekly digest for week {week_of_query}.<br><br>

        (First as a reminder: <b>if you have not yet updated the roster and questions for next week's survey, please do it now through this link: <a href="{host_name}">Your HRCE Dashboard</a>.</b> Surveys will be sent out tomorrow morning!)<br><br>

        {response_alert}

        If you have any questions, please feel free to email us any time.<br><br>

        All the best,<br>
        The High Resolution Course Feedback Team
    </body>
"""

_NO_PARTICIPATION="""
    HRCF also sends participation reports on the last week of surveys if more than 3 students have participated throughout the term. Too few students have participated in {call_number}, however, so we are not sending a report to protect student anonymity. Please encourage more students to participate in future terms! Addressing HRCF comments during class and encouraging students to participate can greatly help elicit more valuable feedback from students.<br><br>
"""

_PARTICIPATION="""
    HRCF also sends participation reports on the last week of surveys if more than 3 students have participated throughout the term. We have made one for {call_number}, which can be found in "participation.txt".<br><br>
"""

MAIL_LAST_DIGEST="""
    <head/>
    <body>
        Hello {call_number} course staff,<br><br>

        Congratulations on finishing the last week of survey!<br><br>

        We'd like to express our great thanks to you for participating in High Resolution Course Feedback this quarter. We really wish our weekly digests helped you make your course better in one way or another. If you found it helpful, please join us again next term (and encourage other classes to join as well)!<br><br>

        {response_alert}

        {participation_notice}

        As always, if you have any questions, please feel free to email us any time.<br><br>

        All the best,<br>
        The High Resolution Course Feedback Team
    </body>
"""

def get_digest_template(is_last, no_response=None, no_participation=None):
    if not is_last:
        assert no_response is not None
        return MAIL_REGULAR_DIGEST.format(
            response_alert=_NO_RESPONSE if no_response else _RESPONSE
        )
    else:
        assert no_participation is not None
        return MAIL_LAST_DIGEST.format(
            participation=_NO_PARTICIPATION if no_participation else _PARTICIPATION,
            response_alert=_NO_RESPONSE if no_response else _RESPONSE
        )

MAIL_STUDENT_NOTICE="""
    <head/>
    <body>
        Hello {student_name},<br><br>

        You were chosen this week to give quick 2-min anonymous feedback on your course {call_number} for week {week_of_query}. Thank you for your time, your feedback is a critical and valuable resource for making our course better. (If you are no longer enrolled in the class, please contact your class TA to update the roster.)<br><br>

        Please fill out this short form: <a href="{link}">Your feedback form</a>. Fill it out now if you can, or at latest by 11:59pm this coming Friday. After this date, the survey will be closed.<br><br>

        Your feedback will be anonymous to your teaching team, but participation will be reported at the end of the quarter.<br><br>

        We deeply thank you for helping the {call_number} teaching staff improve the course.<br><br>

        All the best,<br>
        The High Resolution Course Feedback Team
    </body>
"""

MAIL_STUDENT_REMINDER="""
    <head/>
    <body>
        Hello {student_name},<br><br>

        This is a kind reminder that you were chosen this week to give quick 2-min anonymous feedback on your course {call_number}. Thank you for your time, this is a critical part of understanding our courses. (If you are no longer enrolled in the class, please contact your class TA.)<br><br>

        Please fill out this short form: <a href="{link}">Your feedback form</a>. Fill it out now if you can, or at latest by 11:59pm today (Friday).<br><br>

        Again, your feedback will be anonymous to your teaching team, but participation will be reported at the end of the quarter.<br><br>

        We deeply appreciate your time!<br><br>

        All the best,<br>
        The High Resolution Course Feedback Team
    </body>
"""

MAIL_INSTRUCTOR_REMINDER="""
    <head/>
    <body>
        Hello {call_number} course staff,<br><br>

        This is a reminder from the High Resolution Course Feedback team to update the roster and questions for the upcoming week {next_week} of your course {call_number}. Please use this link: <a href="{HOST_NAME}">Survey Settings Page</a>. <br><br>

        If you have already updated your questions, please feel free to ignore this message.<br><br>

        The weekly digest for this week (week {week_of_query}) will be sent this weekend.<br><br>

        As always, thank you for your interest and participation!<br><br>

        All the best,<br>
        The High Resolution Course Feedback Team
    </body>
"""
