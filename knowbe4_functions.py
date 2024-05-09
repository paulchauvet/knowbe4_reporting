#!/opt/its/venv/bin/python

"""This is a set of functions used by me (Paul Chauvet) at SUNY New Paltz
to help manage our information security training program.  I only started doing
this scripted (vs Excel downloads) since I don't have enough time to manually
chase down people who are doing training.  

The actual documentation is available from:
 - https://developer.knowbe4.com/reporting/

Note: I am someone who programs, I don't consider myself a programmer.
I'm certain this can be done cleaner, but it met the needs I had:
  - reporting on training compliance/non-compliance
  - reporting on phishing simulations (to be implemented, but I want
      to generate reports on who clicked, who submitted, for one or more
      simulations, or even all since a target date.

If you aren't a KnowBe4 customer - I'd highly recommend them.  Their training
is engaging, their phishing simulation tools are great, their support team
is fantastic, and now I can take advantage of their APIs to make my life easier.

No warranty express or implied. No support provided (though if you email
me I will try to answer questions!

As always - test test test. You should not go running into this connecting
to the KnowBe4 API getting thousands of queries without testing and rate
limiting your own connections.  If you get rate limtied by KnowBe4, or they
sick Kevin Mitnick on your company for revenge, I take no responsibility.

If you use this - and find it useful - let me know!
If you use it and find errors or would suggest changes
- sure - let me know those too!

If you have suggestions as to how to do this (insert some completely different
way) - you may want to fork this or create your own site from scratch for it.

Paul Chauvet
Information Security Officer
State University of New York at New Paltz

"""

from pandas import date_range
import requests


#####################
## General Section ##
#####################


def get_knowbe4_token(credfilename):
    """Pull the knowbe4 auth token from the credentials directory (which is not synced to git).
    For this function - the token should be the only thing in the file, 
    on the first line, with or without a line break at the end.
    # You can get this via your KnowBe4 account as an admin as follows:
    # 1 - Login
    # 2 - Click Account Settings
    # 3 - Go to Account Integrations -> API
    # 4 - Check "Enable Reporting API"
    # 5 - Click "Regenerate token" if there is no token there
    # 6 - Note: This will invalidate any token you already have"
    """
    credfile = open(credfilename, 'r').readlines()
    token = credfile[0].strip()
    return token

def api_connect(knowbe4_api_token, context):
    # This is the base_url for US customers.  See KnowBe4 documentation at
    # https://developer.knowbe4.com/rest/reporting#tag/Training/ if not clear
    base_url = "https://us.api.knowbe4.com/v1/"
    api_url = base_url + context
    #
    header = {'Authorization': 'Bearer {0}'.format(knowbe4_api_token)}
    response = requests.request('GET', api_url, headers=header)
    if response.status_code == 401:
        raise Exception("The provided authorization token is not working.")
    if response.status_code == 404:
        raise Exception("The provided api path is not found.")
    else:
        return response


##################
## User Section  ##
##################
def get_user_info(knowbe4_api_token, user_id):
    """Get info from KnowBe4 on a particular user - including items such as department, division, and their 
    manager that isn't in the training enrollment info."""
    users_api = api_connect(knowbe4_api_token, "users/{0}".format(user_id))
    user_info = users_api.json()
    return user_info

def get_knowbe4_users(knowbe4_api_token, status_to_check="active"):
    """Get info from KnowBe4 on all users - since this includes info like division and department
    that isn't in the training enrollment info.  It's limited to 500 per page so will fetch additional pages if needed.
    By default, only active users will be returned, not archived users, are included.
    You can use 'all' as an argument to include all users, not just those with certain statuses.
    """
    page = 1
    user_report_final = {}
    user_report = True
    while user_report:
        print("Getting page {0} of users from the KnowBe4 user api".format(page))
        # Are we checking all users or only active ones?
        if status_to_check == "all":
            users_api = api_connect(knowbe4_api_token, "users?per_page=500&page={0}".format(page))
        else:
            users_api = api_connect(knowbe4_api_token, "users?per_page=500&page={0}&status={1}".format(page, status_to_check))
        user_report = users_api.json()
        for user in user_report:
            email = user['email']
            status = user['status']
            if status_to_check == "all":
                user_report_final[email] = user
            elif status_to_check == status:
                user_report_final[email] = user
        page += 1
    #        
    return user_report_final

######################
## Training Section ##
######################

def list_training_campaigns(knowbe4_api_token, status_to_check="In Progress"):
    """By default, only list In Progress campaigns, if no status is provided.
    If "All" is provided, list all campaigns.
    The options of Closed, or Completed."""
    from collections import OrderedDict
    # Connect to the KnowBe4 API
    training_list_api = api_connect(knowbe4_api_token, "training/campaigns")
    # Get all campaigns, as a list of dictionary objects.
    training_campaigns = training_list_api.json()

    # Create a new dictionary, with the campaign id as the key, for the response.
    training_list = OrderedDict()

    for campaign in training_campaigns:
        id = campaign['campaign_id']
        
        if status_to_check == "All":
            training_list[id] = campaign
        elif campaign['status'] == status_to_check:
            training_list[id] = campaign
    #
        # If a status to check was provided to the function that doesn't exist
        # in the response, then all that will be returned is an empty list.
    return training_list

def get_training_campaign_info(knowbe4_api_token, id):
    """Find info on a particular training campaign, including start/end dates, completion percentages, and included modules"""
    campaign_report_api = api_connect(knowbe4_api_token, "training/campaigns/" + id)
    campaign_info = campaign_report_api.json()
    return campaign_info

def select_training_campaigns():
    """Prompt for one or more training campaigns to report on"""
    campaign_type = input("\nShould we get all training campaigns (All) or just certain statuses (Completed, Closed, In Progress, etc.):   ").strip()
    campaigns = list_training_campaigns(campaign_type)
    for campaign_id, campaign_info in campaigns.items():
        print("Campaign ID: {0},Campaign Name: {1}, Campaign_Status: {2},Start Date: {3},End Date: {4}".format(campaign_id, campaign_info['name'], campaign_info['status'], campaign_info['start_date'], campaign_info['end_date']))
    # Prompt for input, but turn a comma separate string into a list (removing spaces)
    campaign_ids = input("\nWhat training should we get an enrollment report for?  For multiples, separate them by commas:  ").strip().replace(" ","").split(",")
    return campaign_ids

def check_training_compliance(training_info):
    """Check if all training modules a user has are marked as Passed.
        If so - return "All assigned Training Complete.
        If not - return a list of modules that they haven't completed."""
    passed = []
    incomplete = []
    for training in training_info:
        if training['status'] == 'Passed':
            passed.append(training['module_name'])
        else:
            incomplete.append(training['module_name'])
    if passed and not incomplete:
        status = "All assigned training complete"
    else:
        status = incomplete
    return status


def get_enrollment_report(knowbe4_api_token, campaign_id):
    """This will get a report on enrollment, in json format, for anyone in the campaign_id given as an argument.
    Obtain campaign_id values from list_training_campaigns or similar.
    Results are limited to 500 per page, if the results are larger it will go one page at a time."""
    page = 1
    enrollment_report_final = []
    enrollment_report = True
    while enrollment_report:
        print("Working on training campaign {0}, page {1}".format(campaign_id, page))
        enrollment_report_api = api_connect(knowbe4_api_token, "/training/enrollments/?campaign_id={0}&per_page=500&page={1}".format(campaign_id, page))
        enrollment_report = enrollment_report_api.json()
        if enrollment_report != []:
            enrollment_report_final += enrollment_report
            page += 1
    return enrollment_report_final

def generate_user_training_report(knowbe4_api_token, campaign_ids, knowbe4_users):
    """Create a dictionary with info on each user
    Each entry in the dictionary has a key of an email address, and a value of a list.
    Each entry in the list is another dictionary with info on each module, including completion status and module name."""
    #
    user_report = {}
    for campaign_id in campaign_ids:
        enrollment_report = get_enrollment_report(knowbe4_api_token, campaign_id)
        for entry in enrollment_report:
            # Get email, user_id, first_name, and last_name from the enrollment report.
            email = entry['user']['email']
            user_id = entry['user']['id']
            first_name = entry['user']['first_name']
            last_name = entry['user']['last_name']
            module_name = entry['module_name']
            status = entry["status"]
            # Only handle those in the active list
            # (They should age out of the training soon)
            if email in knowbe4_users:
                # if they aren't in the user report, create them in the format of:
                if email not in user_report:
                    department = knowbe4_users[email]['department']
                    division = knowbe4_users[email]['division']
                    user_report[email] = {'division': division, 'department': department, 'first_name': first_name, 'last_name': last_name, 'training_info': [{'module_name': module_name, 'status': status}]}
                # if they are already in the report, we don't need to update anything but the training modules.
                else:
                    user_report[email]['training_info'].append({'module_name': module_name, 'status': status})
    #
    return user_report

def check_if_user_is_past_due(training_info):
    # Assume past_due is False until we hit one that is past due
    past_due = False
    for module in training_info:
        if module['status'] == 'Past Due':
            past_due = True
    return past_due

def get_past_due_users(active_knowbe4_users, user_training_report):
    """Find out which users (if any) are past due on training."""
    # Create a list for those overdue on training
    training_past_due_users = []
    #
    # Go through each user in the training report
    for email, userinfo in user_training_report.items():
        username = email.split("@")[0]
        # Check if they are in the active users list (i.e. exclude anyone who is no longer active in the training
        # system, but may have been when the training was assigned, such as former employees)
        if email in active_knowbe4_users:
            # This will return 'True' if they are past due
            if check_if_user_is_past_due(userinfo['training_info']):
                training_past_due_users.append(username)
    return training_past_due_users


######################
## Phishing Section ##
######################

def list_phishing_campaigns(knowbe4_api_token, status_to_check="Active"):
    """By default, only list In Progress campaigns, if no status is provided.
    If "All" is provided, list all campaigns.
    The options of Closed, or Completed."""
    # Connect to the KnowBe4 API
    phishing_list_api = api_connect(knowbe4_api_token, "phishing/security_tests")

    # Get all campaigns, as a list dict objects.
    phishing_campaigns = phishing_list_api.json()

    # Create a list for the response.  So far I'm only returning name and ID.
    # You could return the entire json response if you want.
    phishing_list = []

    for campaign in phishing_campaigns:
        id = campaign['pst_id']
        name = campaign['name']
        status = campaign['status']

        if status_to_check == "All":
            phishing_list.append([name, id])
        elif status == status_to_check:
            phishing_list.append([name, id])

        # If a status to check was provided to the function that doesn't exist
        # in the response, then all that will be returned is an empty list.
    return phishing_list

def select_phishing_campaigns(status="Active"):
    """Prompt for one or more phishing campaigns to report on - selecting from active campaigns only"""
    campaigns = list_phishing_campaigns(status)
    print("\nPhishing Campaigns")
    for entry in campaigns:
        name, id = entry
        print("Name:", name, "- ID:", id)
    campaign_ids = input("\n\nShould we check against a phishing campaign as well?\nIf so - enter the campaign id (For multiples, separate them by commas):  ").strip().replace(" ","").split(",")
    # If no campaign is selected, just return an empty 
    if campaign_ids == "":
        campaign_ids = []
    return campaign_ids

def get_phishing_campaign_report(knowbe4_api_token, pst_ids):
    """This will get a report on one or more phishing campaigns, in json format, for anyone in the
    Obtain pst_id (phishing security test id) values from list_phishing_campaigns or similar.
    It will return a dictionary with the email addresses as the key, and will have a nested dictionary
    containing the following info:
     - whether they received it yet
     - whether they reported it
     - whether they clicked the link
     - whether they opened an attachment
     - whether they entered data"""
    user_report = {}
    # Gather the info from KnowBe4 for the given campaign id(s)
    phishing_report_full = []     
    for pst_id in pst_ids:
        # Start with page 1 - and initially set this to True so we at least get one page
        page = 1
        phishing_report = True
        # Get the repot for a given PST campaign
        while phishing_report:
            print("Working on phishing campaign {0}, page {1}".format(pst_id, page))
            phishing_report_api = api_connect(knowbe4_api_token, "/phishing/security_tests/{0}/recipients?per_page=500&page={1}".format(pst_id, page))
            phishing_report = phishing_report_api.json()
            if phishing_report != []:
                phishing_report_full += phishing_report
                page += 1
    #    
    for user_info in phishing_report_full:
        email = user_info['user']['email']
        attachment_opened = user_info['attachment_opened_at']
        clicked = user_info['clicked_at']
        data_entered = user_info['data_entered_at']        
        delivered = user_info['delivered_at']
        reported = user_info['reported_at']
        campaign_id = user_info['pst_id']
        if email in user_report:
            user_report[email][campaign_id] = {'attachment_opened': attachment_opened, 'clicked': clicked, 'data_entered': data_entered, 'delivered': delivered, 'reported': reported}
        else:
            user_report[email] = {campaign_id: {'attachment_opened': attachment_opened, 'clicked': clicked, 'data_entered': data_entered, 'delivered': delivered, 'reported': reported}}

    return user_report


def get_phish_status_by_user(phishing_report, email):
    """This requires a phish report generated from the get_phishing_campaign_report.
    If in any of the checked phishing reports the person entered data or clicked, then return that info.
    If they didn't click, weren't in the report, or we didn't run a phishing report, just return None."""
    # Default to 'they never clicked or submitted'
    submitted = False
    clicked = False
    if email in phishing_report:
        for campaign, campaign_info in phishing_report[email].items():
            # data entered assumes clicked already happened
            if 'data_entered' in campaign_info:
                if campaign_info['data_entered'] != None:
                    clicked = True
            if 'clicked' in campaign_info:
                if campaign_info['clicked'] != None:
                    submitted = True
    if submitted:
        response = "This person submitted data, such as a username or password, in a recent last phishing simulation exercise."
    elif clicked:
        response = "This person clicked the phishing link in a recent phishing simulation exercise, but they stopped before submitting any information to the site."
    else:
        response = None
    return response

def generate_phish_report_by_user(phishing_report):
    # Do this so my final dictionary is ordered alphabetically
    from collections import OrderedDict
    users = list(phishing_report.keys())
    users.sort()
    report = OrderedDict()
    for user in users:
        for campaign_id in phishing_report[user]:
            data_entered = phishing_report[user][campaign_id].get('data_entered', None)
            clicked = phishing_report[user][campaign_id].get('clicked', None)
            reported = phishing_report[user][campaign_id].get('reported', None)
            # If the user is not already in the report, create an entry for them
            if user not in report:
                report[user] = {'data_entered': [], 'clicked': [], 'reported': []}
            if data_entered:
                report[user]['data_entered'].append(data_entered)
            if clicked:
                report[user]['clicked'].append(clicked)
            if reported:
                report[user]['reported'].append(reported)
    return report


##########################
## Group Update Section ##
##########################
def get_group_update_lists(current_group_members, past_due_users):
    group_additions = []
    group_removals = []
    # Find who is past due on their training, but not in the past-due group
    for user in past_due_users:
        if user not in current_group_members:
            group_additions.append(user)
    group_additions.sort()
    # Find who is in the past due group, but is no longer past due on their training
    for user in current_group_members:
        if user not in past_due_users:
            group_removals.append(user)
    group_removals.sort()
    return group_additions, group_removals