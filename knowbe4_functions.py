#!/opt/its/venv/bin/python

"""A set of functions used to connect to and/or organize data from the KnowBe4 reporting API.

See README.md file for more information.
Author: Paul Chauvet
        Information Security Officer
        State University of New York at New Paltz
"""

import requests


#####################
## General Section ##
#####################


def get_kb4_token():
    """Pull the knowbe4 auth token which should be placed in the credentials subdirectory
    (ensure that your api token is not synced via git).
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
    credfilename = "credentials/knowbe4_token"
    credfile = open(credfilename, 'r').readlines()
    token = credfile[0].strip()
    return token

def api_connect(context):
    """Connect to the API - with the given context, and return the response.
    I only have a couple error codes handled so far but you may see others.
    """
    # This is the base_url for US customers.  See KnowBe4 documentation at
    # https://developer.knowbe4.com/rest/reporting#tag/Training/ if not clear
    base_url = "https://us.api.knowbe4.com/v1/"
    api_url = base_url + context
    #
    token = get_kb4_token()
    #
    header = {'Authorization': 'Bearer {0}'.format(token)}
    response = requests.request('GET', api_url, headers=header)
    if response.status_code == 401:
        raise Exception("The provided authorization token is not working.")
    if response.status_code == 404:
        raise Exception("The provided api path is not found.")
    else:
        return response


##################
## User Section ##
##################

def get_user_info(user_id):
    """Get info from KnowBe4 on a particular user - including items such as department, division, and their 
    manager that isn't in the training enrollment info."""
    users_api = api_connect("users/{0}".format(user_id))
    user_info = users_api.json()
    return user_info

def get_knowbe4_users(status_to_check="active"):
    """Get info from KnowBe4 on all users, or just active users.
    This supplements the user info that is returned for training enrollments, since this
    includes info like division and department that isn't in the training enrollment info.
    It's limited to 500 per page so will fetch additional pages if needed.
    By default, only active users will be returned, but you can specify 'archived' users, or
    'all' users instead (though I personally don't envision a need to).
    """
    # start with page 1 of the responses, and use this as a counter for additional pages if
    # more than 500 users are returned.
    page = 1
    # Create a dictionary, with user email addresses as the key.
    user_report_final = {}
    # Set true initially so it at least goes through one page.  If it goes for a second page and it's empty
    # the while loop will end.
    user_report = True
    while user_report:
        print("Getting page {0} of users from the KnowBe4 user api".format(page))
        # Are we checking all users or only active/archived ones as specified in the function?
        if status_to_check == "all":
            users_api = api_connect("users?per_page=500&page={0}".format(page))
        else:
            users_api = api_connect("users?per_page=500&page={0}&status={1}".format(page, status_to_check))
        user_report = users_api.json()
        for user in user_report:
            email = user['email']
            user_report_final[email] = user
        page += 1
    #        
    return user_report_final

######################
## Training Section ##
######################

def list_training_campaigns(status_to_check="In Progress"):
    """By default, only list In Progress campaigns, if no status is provided.
    If "All" is provided, list all campaigns.
    The options of Closed, or Completed."""
    from collections import OrderedDict
    # Connect to the KnowBe4 API
    training_list_api = api_connect("training/campaigns")
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

def get_training_campaign_info(id):
    """Find info on a particular training campaign, including start/end dates, completion percentages, and included modules"""
    campaign_report_api = api_connect("training/campaigns/" + id)
    campaign_info = campaign_report_api.json()
    return campaign_info

def select_training_campaigns():
    """Prompt for one or more training campaigns to report on"""
    campaign_type = input("Should we get all training campaigns (All) or just certain statuses (Completed, Closed, In Progress, etc.):   ").strip()
    campaigns = list_training_campaigns(campaign_type)
    for campaign_id, campaign_info in campaigns.items():
        print("Campaign ID: {0},Campaign Name: {1}, Campaign_Status: {2},Start Date: {3},End Date: {4}".format(campaign_id, campaign_info['name'], campaign_info['status'], campaign_info['start_date'], campaign_info['end_date']))
    # Prompt for input, but turn a comma separate string into a list (removing spaces)
    campaign_ids = input("What training should we get an enrollment report for?  For multiples, separate them by commas:  ").strip().replace(" ","").split(",")
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


def get_enrollment_report(campaign_id):
    """This will get a report on enrollment, in json format, for anyone in the campaign_id given as an argument.
    Obtain campaign_id values from list_training_campaigns or similar.
    Results are limited to 500 per page, if the results are larger it will go one page at a time."""
    page = 1
    enrollment_report_final = []
    enrollment_report = True
    while enrollment_report:
        print("Working on training campaign {0}, page {1}".format(campaign_id, page))
        enrollment_report_api = api_connect("/training/enrollments/?campaign_id={0}&per_page=500&page={1}".format(campaign_id, page))
        enrollment_report = enrollment_report_api.json()
        if enrollment_report != []:
            enrollment_report_final += enrollment_report
            page += 1
    return enrollment_report_final

def generate_user_training_report(campaign_ids, knowbe4_users):
    """Create a dictionary with info on each user
    Each entry in the dictionary has a key of an email address, and a value of a list.
    Each entry in the list is another dictionary with info on each module, including completion status and module name."""
    #
    user_report = {}
    for campaign_id in campaign_ids:
        enrollment_report = get_enrollment_report(campaign_id)
        for entry in enrollment_report:
            # Get email, user_id, first_name, and last_name from the enrollment report.
            email = entry['user']['email']
            user_id = entry['user']['id']
            first_name = entry['user']['first_name']
            last_name = entry['user']['last_name']
            module_name = entry['module_name']
            status = entry["status"]
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


######################
## Phishing Section ##
######################

def list_phishing_campaigns(status_to_check="Active"):
    """By default, only list In Progress campaigns, if no status is provided.
    If "All" is provided, list all campaigns.
    The options of Closed, or Completed."""
    # Connect to the KnowBe4 API
    phishing_list_api = api_connect("phishing/security_tests")

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
        elif status == status_to_check and status_to_check:
            phishing_list.append([name, id])

        # If a status to check was provided to the function that doesn't exist
        # in the response, then all that will be returned is an empty list.
    return phishing_list

def select_phishing_campaign():
    """Prompt for one or more phishing campaigns to report on - selecting from active campaigns only"""
    campaigns = list_phishing_campaigns()
    for entry in campaigns:
        name, id = entry
        print("Name:", name, "- ID:", id)
    campaign_id = input("Should we check against a phishing campaign as well? If so - enter the campaign id:  ").strip().replace(" ","")
    # If no campaign is selected, just return an empty 
    if campaign_id == "":
        campaign_id = {}
    return campaign_id

def get_phishing_campaign_report(pst_id):
    """This will get a report on a given phishing campaign, in json format, for anyone in the
    Obtain pst_id (phishing security test id) values from list_phishing_campaigns or similar.
    It will return a dictionary with the email addresses as the key, and will have a nested dictionary
    containing the following info:
     - whether they received it yet
     - whether they reported it
     - whether they clicked the link
     - whether they opened an attachment
     - whether they entered data"""
    if pst_id:
        page = 1
        phishing_report_full = []
        phishing_report = True
        while phishing_report:
            print("Working on phishing campaign {0}, page {1}".format(pst_id, page))
            phishing_report_api = api_connect("/phishing/security_tests/{0}/recipients?per_page=500&page={1}".format(pst_id, page))
            #phishing_report_api = api_connect("/phishing/security_tests/{0}/recipients".format(pst_id))
            phishing_report = phishing_report_api.json()
            if phishing_report != []:
                phishing_report_full += phishing_report
                page += 1
        
        user_report = {}
        for user_info in phishing_report_full:
            try:
                email = user_info['user']['email']
                attachment_opened = user_info['attachment_opened_at']
                clicked = user_info['clicked_at']
                data_entered = user_info['data_entered_at']        
                delivered = user_info['delivered_at']
                reported = user_info['reported_at']
                user_report[email] = {'attachment_opened': attachment_opened, 'clicked': clicked, 'data_entered': data_entered, 'delivered': delivered, 'reported': reported}
            except:
                print("error with user", user_info)
    # Just send back a blank dictionary if no campaign is selected
    else:
        user_report = {}

    return user_report


def get_phish_status_by_user(phishing_report, email):
    """This requires a phish report generated from the get_phishing_campaign_report.

    If we checked a phishing report and the person entered data or clicked, then return that info.
    If they didn't click, weren't in the report, or we didn't run a phishing report, just return an empty string."""
    if email in phishing_report:
        # data entered assumes clicked alreayd happened
        if 'data_entered' in phishing_report[email]:
            if phishing_report[email]['data_entered']:
                return("This person submitted data, such as a username or password, in a recent last phishing simulation exercise.")
        if 'clicked' in phishing_report[email]:
            if phishing_report[email]['clicked']:
                return("This person clicked the phishing link in a recent phishing simulation exercise, but they stopped before submitting any information to the site.")
        else:
            return("")
    else:
        return("")
