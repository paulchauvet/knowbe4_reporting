#!/opt/its/venv/bin/python

"""For a given list of training campaigns, find users who are past due.
Ensure those individuals (and only those individuals) are in the knowbe4_past_due group in AD.
For us, that group is synchronized to Azure AD, and is used in a conditional access group which
blocks all users in that group, from getting access to a set of apps we deem "High Risk".

# Dependencies
- A KnowBe4 API token
    - You can get this via your KnowBe4 account as an admin as follows:
      - 1 - Login
      - 2 - Click Account Settings
      - 3 - Go to Account Integrations -> API
      - 4 - Check "Enable Reporting API"
      - 5 - Click "Regenerate token" if there is no token there
      - 6 - Note: This will invalidate any token you already have

- python3-ldap & pandas python libraries (most likely installed via PIP)

- An Active Directory server, with:
   - a group that you are going to have all 'past due' users in
   - a username/password for a user that can update that group

- a mail server that can receive mail if you want to get updates/errors
"""

from datetime import datetime
from knowbe4_functions import get_config, generate_user_training_report, get_knowbe4_users, get_past_due_users, get_group_update_lists
from mail_functions import send_html_email
from active_directory_functions import create_ad_connection, get_group_membership, update_group_with_report


## Start Configuration

CONFIG = get_config()

KB4_API_TOKEN = CONFIG['knowbe4_token']

# This should include a list of the campaign IDs for the year that you are basing this on.
# It must be updated each January (or as needed for your training cycles) as new training is setup.
CAMPAIGN_IDS = CONFIG['knowbe4_campaign_ids'].strip().split(", ")

# This determines what year you're looking for training in.
# For us, we use a yearly training cycle with training offered in the start of January, and that training year closes at
# the end of the year.  That doens't mean all training is due at the end of the year, but this assumes that new assignments
# will be created and assigned at the start of each year
TRAINING_YEAR = CONFIG['knowbe4_training_year']

# Email config
# This includes both a person to notify if there are problems or changes, as well as the name/address those emails will come from
SMTP_SERVER = CONFIG['smtp_server']
SMTP_PORT = CONFIG['smtp_port']
EMAIL_RECIPIENT_ADDRESS = CONFIG['smtp_recipient_address']
EMAIL_SENDER_ADDRESS = CONFIG['smtp_from_address']
EMAIL_SENDER_NAME = CONFIG['smtp_from_name']
EMAIL_SUBJECT = CONFIG['smtp_subject']

# Set email host address, and other info in the "mail_functions.py" script, or alter as needed

# Active Directory Config
AD_URL = CONFIG['ad_url']
AD_BASE = CONFIG['ad_base']
AD_USER = CONFIG['ad_username']
AD_PASS = CONFIG['ad_password']

TRAINING_PAST_DUE_GROUP = CONFIG['ad_group_name']
GROUP_DN = CONFIG['ad_group_dn']


# People who have been granted a temporary exemption if needed
# For example individuals on leave (I'd automate this if I could but don't have access to that data automatically...)
EXCEPTIONS = []

## End Configuration

# Create what will be used as the email message body for a report of what has changed
output_message = f"The following is a list of changes made to the {TRAINING_PAST_DUE_GROUP} group in Active Directory<br />"

# Get who is currently in that group
CURRENT_GROUP_MEMBERS = get_group_membership(TRAINING_PAST_DUE_GROUP, AD_USER, AD_PASS, AD_BASE, AD_URL)

## Gathering information from KnowBe4 on who is past due
# Make sure we're in the current training year
# This will have to be updated manually each year, with a new date to match the new campaign ids.
if TRAINING_YEAR == datetime.now().year:

    # Get information from KnowBe4's API
    try:
        # Connect to KnowBe4 API
        KB4_API_TOKEN = get_knowbe4_token(KB4_API_TOKEN_FILE)

        # Get a list of active users in KnowBe4
        ACTIVE_KNOWBE4_USERS = get_knowbe4_users(KB4_API_TOKEN)

        # Get the report for the active users for the given campaigns
        USER_TRAINING_REPORT = generate_user_training_report(KB4_API_TOKEN, CAMPAIGN_IDS, ACTIVE_KNOWBE4_USERS)

        # From the report, determine which users have past due training
        PAST_DUE_USERS = get_past_due_users(ACTIVE_KNOWBE4_USERS, USER_TRAINING_REPORT)
    except Exception as e:
        send_html_email("Error with manage_knowbe4_pastdue_group.py script in KB4 information gathering section" + str(e), SMTP_SERVER, SMTP_PORT, EMAIL_RECIPIENT_ADDRESS, EMAIL_SENDER_ADDRESS, EMAIL_SENDER_NAME, "Error with manage_kno
wbe4_pastdue_group.py script in KB4 information gathering section")
        print("ERROR in kb4 information gathering section!")
        raise

    # Get who should be added to and removed from the group
    GROUP_ADDITIONS, GROUP_REMOVALS = get_group_update_lists(CURRENT_GROUP_MEMBERS, PAST_DUE_USERS)
    
    for user in EXCEPTIONS:
        if user in GROUP_ADDITIONS:
            GROUP_ADDITIONS.remove(user)

    print("adding", GROUP_ADDITIONS, "to the list")
    print("removing", GROUP_REMOVALS, "from the list")

    ## If there are any users in the additions or removal lists, proceed
    if GROUP_ADDITIONS != [] or GROUP_REMOVALS != []:
        try:
            # Connect to Active Directory
            AD_CONN = create_ad_connection(AD_USER, AD_PASS, AD_URL)

            output_message += update_group_with_report(TRAINING_PAST_DUE_GROUP, GROUP_DN, AD_BASE, AD_CONN, GROUP_ADDITIONS, GROUP_REMOVALS) + "<br />"

        except Exception as e:
            send_html_email("Error with manage_knowbe4_pastdue_group.py script in Group Update section" + str(e), SMTP_SERVER, SMTP_PORT, EMAIL_RECIPIENT_ADDRESS, EMAIL_SENDER_ADDRESS, EMAIL_SENDER_NAME, "Error with manage_knowbe4_pastdue_group.py script in Group Update section")
            print("ERROR in Group Update section!")
            raise



    # Send the email if there have been any changes made
    if output_message != f"The following is a list of changes made to the {TRAINING_PAST_DUE_GROUP} group in Active Directory<br />":
        send_html_email(output_message, SMTP_SERVER, SMTP_PORT, EMAIL_RECIPIENT_ADDRESS, EMAIL_SENDER_ADDRESS, EMAIL_SENDER_NAME, EMAIL_SUBJECT)

else:
    print("The TRAINING_YEAR and CAMPAIGN_IDS variables need to be updated")
