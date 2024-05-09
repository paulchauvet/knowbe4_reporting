#!/opt/its/venv/bin/python

"""Go through one or more campaigns.  Generate a report by division for people
with incomplete training.

For the department/division reporting I'm doing here, you need to at least have those values in KnowBe4.
For us - this info is in our Active Directory for most users, so it is in KnowBe4 due to the AD Sync
(https://support.knowbe4.com/hc/en-us/articles/228373888-Active-Directory-Integration-ADI-Configuration-Guide)

If you upload users manually and fill in those values you should be fine as well.
"""

from knowbe4_functions import get_config, select_training_campaigns, select_phishing_campaigns, generate_user_training_report, \
                              get_phishing_campaign_report, get_knowbe4_users, get_phish_status_by_user
from collections import OrderedDict

def print_division_report(division_report, phishing_report):
    """Prints the report - by division and department.
    For my own environment, I use email instead of printing (with reports sent to each division VP
    but I haven't had a chance to clean up the stuff there specific to my organization."""
    divisions = list(division_report.keys())
    divisions.sort()
    for division in divisions:
        print("\n\n\nDivision:" + division)
        print("===============================")
        departments = list(division_report[division].keys())
        departments.sort()
        for department in departments:
            # Set all-complete as true - at least until it's changed to false.
            all_completed = True
            print("\nDepartment: " + department)
            print("-----------------------------")
            for email, userinfo in division_report[division][department].items():
                training_status = userinfo['training_status']
                display_name = userinfo['display_name']
                if training_status != "All assigned training complete":
                    print("{0} ({1}) - Incomplete training: {2}".format(display_name, email, training_status))
                    all_completed = False
                    # Have a special addition if they have also recently failed phishing simulations
                    phishing_status = get_phish_status_by_user(phishing_report, email)
                    if phishing_status:
                        print("   Note:" + phishing_status)
            if all_completed:
                print("All individuals in this department have completed their assigned training")

CONFIG = get_config()
KB4_API_TOKEN = CONFIG['knowbe4_token']

CAMPAIGN_IDS = select_training_campaigns(KB4_API_TOKEN)

PHISHING_CAMPAIGN_IDS = select_phishing_campaigns(KB4_API_TOKEN, "All")
PHISHING_REPORT = get_phishing_campaign_report(KB4_API_TOKEN, PHISHING_CAMPAIGN_IDS)

ACTIVE_USERS = get_knowbe4_users(KB4_API_TOKEN)

USER_TRAINING_REPORT = generate_user_training_report(KB4_API_TOKEN, CAMPAIGN_IDS, ACTIVE_USERS)

for user, userinfo in USER_TRAINING_REPORT.items():
    print(user, userinfo)



