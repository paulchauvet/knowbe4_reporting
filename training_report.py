#!/opt/its/venv/bin/python

"""Go through one or more campaigns.  Generate a report by division for people
with incomplete training.

Eventually generate a scorecard by division and/or department of completion
rates.

Requirements: You have to have your departments and divisions populated
in Active Directory or somewhere you can query, at least if you want
to do this the way I'm doing it.
"""

from knowbe4_functions import select_training_campaigns, select_phishing_campaign, generate_user_training_report, \
                              get_phishing_campaign_report, get_phish_status_by_user, get_knowbe4_users, check_training_compliance
from mail_functions import send_html_email
from misc_utils import get_division_info
from collections import OrderedDict

def generate_report_by_division(user_report):
    """Generate a report of incomplete training users, by division, then department."""
    division_report = {}
    # Sort by email address, which will in turn sort by last name in the final report if we're using an ordered dictionary.
    emaillist = list(user_report.keys())
    emaillist.sort()
    for email in emaillist:
        userinfo = user_report[email]
        division = userinfo['division']
        department = userinfo['department']
        training_info = userinfo['training_info']
        first_name = userinfo['first_name']
        last_name = userinfo['last_name']
        training_status = check_training_compliance(training_info)
        # first entry of this division
        if division not in division_report:
            division_report[division] = {department: OrderedDict({email: {'training_status': training_status, 'first_name': first_name, 'last_name': last_name}})}
        # first entry of this department for this division
        elif department not in division_report[division]:
            division_report[division][department] = OrderedDict({email: {'training_status': training_status, 'first_name': first_name, 'last_name': last_name}})
        # department and division have already been started, append to the list for the given department
        else:
            division_report[division][department][email] = {'training_status': training_status, 'first_name': first_name, 'last_name': last_name}
    return division_report

def generate_division_report_messages():
    division_report_emails = {}
    #
    ## Sort divisions to generate report in division order
    divisions = list(DIVISION_REPORT.keys())
    divisions.sort()
    for division in divisions:
        try:
            division_head_salutation = get_division_info(division)['salutation']
        except:
            # I should raise an exception here and just send myself an email
            # that someone's missing - but I'll handle that later.
            print(division, "error getting salutation")
            division_head_salutation = "Vice President"
        #
        report_message_body = '<p>Dear {0},</p><br />'.format(division_head_salutation)
        report_message_body += '<p>As you know, SUNY New Paltz requires all employees to complete Information Security Awareness training, on an annual basis.  This is required as per the <a href="https://www.suny.edu/sunypp/documents.cfm?doc_id=848">SUNY Information Security Policy</a> as well as federal and state requirements.<p><br />'
        report_message_body += '<p>The following employees within your division have not yet completed the training this year.  They have been sent notices when the training was first assigned and periodically as the due date has approached.</p><br />'
        report_message_body += '<p>For any faculty/staff who started at the college before this year, the general training was assigned {0}, and was set to be due on {1}.</p><br />'.format(TRAINING_START_DATE, TRAINING_END_DATE)
        report_message_body += '<p>For new faculty/staff who started after January 1st, 2022, the training was assigned once they were added to the system, and set with a due date three months later.</p><br />'
        report_message_body += '<h3><u>Division: {0}</u></h3><br />\n'.format(division)
        #
        departments = list(DIVISION_REPORT[division].keys())
        departments.sort()
        #
        for department in departments:
            # HRDI is a division and a department, no need to list both in the email
            if department not in ("Human Resources, Diversity & Inclusion"):
                report_message_body += "<h4><u>Department: {0}</u></h4>\n".format(department)
            #
            report_message_body += "<ul>\n"
            #
            all_complete = True
            #
            for email in DIVISION_REPORT[division][department]:
                training_compliance = DIVISION_REPORT[division][department][email]['training_status']
                givenName = DIVISION_REPORT[division][department][email]['givenName']
                sn = DIVISION_REPORT[division][department][email]['sn']
                displayName = givenName + " " + sn
                if training_compliance != 'All assigned training complete':
                    training_compliance.sort()
                    output = "<li>{0} ({1}) - incomplete training modules:\n".format(displayName, email)
                    #
                    # Start a separate list for each user for their training
                    output += "<ul>\n"
                    for module in training_compliance:
                        output += "<li>{0}</li>".format(module)
                    # End user specific list
                    #
                    # Get their status for the phishing simulation.  If they have a flag against them, include it after the training modules.
                    phish_status = get_phish_status_by_user(PHISHING_REPORT, email)
                    if phish_status:
                        output += "<li><b>Note: {0}</b></li>".format(phish_status)
                    #
                    output += "</ul>"
                    output += "</li>"
                    report_message_body += output
                    all_complete = False
            if all_complete:
                output = "<li>All faculty and staff in this department have completed all training modules assigned!</li>\n"
                report_message_body += output
            #
            report_message_body += "</ul>\n"
        #
        division_report_emails[division] = report_message_body
    # All emails are set as a dictionary with per-division keys
    return division_report_emails

TRAINING_START_DATE = "January 20th, 2022"
TRAINING_END_DATE = "June 30th, 2022"

CAMPAIGN_IDS = select_training_campaigns()

PHISHING_CAMPAIGN_ID = select_phishing_campaign()
PHISHING_REPORT = get_phishing_campaign_report(PHISHING_CAMPAIGN_ID)

ACTIVE_USERS = get_knowbe4_users()

USER_TRAINING_REPORT = generate_user_training_report(CAMPAIGN_IDS, ACTIVE_USERS)
DIVISION_REPORT = generate_report_by_division(USER_TRAINING_REPORT)
DIVISION_REPORT_EMAILS = generate_division_report_messages()


for division, message_body in DIVISION_REPORT_EMAILS.items():
    division_head_salutation = get_division_info(division)['salutation']

    # Eventually send these directly - but for now just use my address
    #division_head_email = get_division_info(division)['email']
    division_head_email = "chauvetp@newpaltz.edu"

    subject = "Faculty and Staff in {0} who haven't completed the annual security awareness training".format(division)
    #if division == "Administration & Finance":
    send_html_email(message_body, division_head_email, "chauvetp@newpaltz.edu", "Paul Chauvet", subject)






