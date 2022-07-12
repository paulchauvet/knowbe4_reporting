#!/opt/its/venv/bin/python

"""Go through one or more campaigns.  Generate a report by division for people
with incomplete training.

For the department/division reporting I'm doing here, you need to at least have those values in KnowBe4.
For us - this info is in our Active Directory for most users, so it is in KnowBe4 due to the AD Sync
(https://support.knowbe4.com/hc/en-us/articles/228373888-Active-Directory-Integration-ADI-Configuration-Guide)

If you upload users manually and fill in those values you should be fine as well.
"""

from knowbe4_functions import print_division_report, select_training_campaigns, select_phishing_campaign, \
                              generate_user_training_report, get_phishing_campaign_report, get_knowbe4_users, \
                              generate_report_by_division, print_division_report
from collections import OrderedDict


CAMPAIGN_IDS = select_training_campaigns()

PHISHING_CAMPAIGN_ID = select_phishing_campaign()
PHISHING_REPORT = get_phishing_campaign_report(PHISHING_CAMPAIGN_ID)

ACTIVE_USERS = get_knowbe4_users()

USER_TRAINING_REPORT = generate_user_training_report(CAMPAIGN_IDS, ACTIVE_USERS)
DIVISION_REPORT = generate_report_by_division(USER_TRAINING_REPORT)

# Note: for my internal process - this is replaced with a function that sends an email to each division
# head, with a list if those who are not compliant sorted by department.
# Too much of that is organizational specific (primariy the message text) so feel free to write
# your own version
# If there's demand - I'll include a cleaned-up version of my own.
print_division_report()




