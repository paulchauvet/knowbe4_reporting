#!/opt/its/venv/bin/python

"""Go through one or more phishing campaigns.  Generate a report by user of how many times they clicked or submitted data.
You can use this, for example, to pull the last several phishing simulations, and it will generate reports on those users who have 

Note: This is broken for now - I need to update it to change how it pulls API keys
"""

from knowbe4_functions import select_phishing_campaigns, get_phishing_campaign_report, generate_phish_report_by_user


# Get a list of all phishing campaigns, and prompt the user for which ones they want to report on
PHISHING_CAMPAIGN_IDS = select_phishing_campaigns("All")
PHISHING_CAMPAIGN_REPORT = get_phishing_campaign_report(PHISHING_CAMPAIGN_IDS)
PHISHING_REPORT_BY_USER = generate_phish_report_by_user(PHISHING_CAMPAIGN_REPORT)

print("Found {0} users in the phishing report".format(len(PHISHING_REPORT_BY_USER)))

MULTIPLE_DATA_SUBMISSIONS = []
print("\n\nThe following users have entered data in more than one of the selected phishing simulations")
# Find multiple data submissions
for user in PHISHING_REPORT_BY_USER:
    submit_count = len(PHISHING_REPORT_BY_USER[user]['data_entered'])
    if submit_count > 1:
        print(user, PHISHING_REPORT_BY_USER[user]['data_entered'])
        MULTIPLE_DATA_SUBMISSIONS.append(user)

print("\n\nThe following users have clicked the link in more than one of the selected phishing simulations")
# Find multiple clickers
for user in PHISHING_REPORT_BY_USER:
    click_count = len(PHISHING_REPORT_BY_USER[user]['clicked'])
    if click_count > 1 and user not in MULTIPLE_DATA_SUBMISSIONS:
        print(user, PHISHING_REPORT_BY_USER[user]['clicked'])
