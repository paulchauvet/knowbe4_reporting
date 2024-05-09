# knowbe4_reporting
These are some functions and one or more scripts to aid in security training reporting using the KnowBe4 API.

## Description
This is a set of functions used by me (Paul Chauvet) at SUNY New Paltz
to help manage our information security training program.  I only started doing
this scripted (vs Excel downloads) since I don't have enough time to manually
chase down people who are doing training.  As often is the case, not having enough
time in the long-term but having some time in the short-term drives automation.

It started with just reporting, then moved into updating an Active Directory group
to have all users who are 'past due' on their training (as per the due date on any
specified training assignments).

The actual KnowBe4 API documentation is available from:
 * [https://developer.knowbe4.com/reporting/](https://developer.knowbe4.com/reporting/)

Note: I am someone who programs, I don't consider myself a programmer.
I'm certain this can be done better/cleaner, but it met the needs I had.


If you aren't a KnowBe4 customer - I'd highly recommend them.  Their training
is engaging, their phishing simulation tools are great, their support team
is fantastic, and now I can take advantage of their APIs to make my life easier.

No warranty express or implied. No support provided (though if you email
me I will try to answer questions!

As always - test test test. You should not go running into this connecting
to the KnowBe4 API getting thousands of queries without testing and rate
limiting your own connections.  If you get rate limited by KnowBe4, I take
no responsibility.

If you use this - and find it useful - let me know!
If you use it and find errors or would suggest changes, let me know those too!

If you have suggestions as to how to do this (insert some completely different
way) - you may want to fork this or create your own site from scratch for it.

## Requirements
* Python 3.x
* PyYAML module
* Python-ldap module
* smtplib module
* I may have forgotten a couple - working on pulling this into a clean python virtual environment so I can be specific here)
* A KnowBe4 account and API token
* Active Directory (assuming you want to maintain a past_due users group) and a user that can update that group

## Setup and installation
* Copy the knowbe4_config.yml.template to a credentials subdirectory and fill in the variables.  Those include info on your AD server (if you want to use the manage_knowbe4_pastdue_group.py script) and SMTP serer info, as well as the Knowbe4 API token.
* Test with a test user
* You may need to do some stuff to trust the certificate on your AD server

## Usage

### manage_knowbe4_pastdue_group.py
* complete the config
* run it - it 

### training_report.py
If you use the built in training_report.py function, you will be first be asked which training reports to analyze data from.  This can include all training, or just some (Completed, In Progress, Closed).

You will then be show all training modules (or all those in the status you selected) and can select one or more training modules by their training campaign id.

You can then specify whether you want to also check against a phishing campaign.  This gives additional weight to the reports (for example, John Doe didn't complete their training, and they are also phish prone (hint hint).  Those who have completed their assigned training but are phish prone are NOT included in the report.  My reasoning is to not shame those who are actually trying.

## Future
* I may generate an additional script to report on people with multiple simulation clicks or data entries in the past year though.
* I would like to generate a scorecard per-department on training compliance (even if just a percentage).

## Author
Paul Chauvet  
Information Security Officer  
State University of New York at New Paltz [https://www.newpaltz.edu](www.newpaltz.edu)  
chauvetp@newpaltz.edu

## License
All rights to the API and the KnowBe4 name are owned by KnowBe4 and none of this is meant to change that.

My own code is released under the [MIT](https://choosealicense.com/licenses/mit/) license.

## Disclaimer
The instructions and settings provided in this document may not be the only way to do things. They are the way that has worked for us at New Paltz, and I've tried to document them as well as possible - but there may be better/cleaner ways of doing things. They may not work at all for your environment. Heck - I may have made some big mistakes here.

As always - test test test and read the official Knowbe4 documentation.

No warranty express or implied. No support guaranteed.
