def get_credentials(system):
    """Pull credentials for various systems from their text files.  You should ensure your credentials directory is not synced via git"""
    if system == "active_directory_group_manager":
        credfilename = "credentials/active_directory_group_manager"
    #
    # Read the appropriate credentials file
    credfile = open(credfilename, 'r').readlines()
    # Parse through the credentials file
    for line in credfile:
        if "username" in line:
            username = line.split(": ")[1].rstrip()
        if "password" in line:
            password = line.split(": ")[1].rstrip()
    return username, password

def create_ad_connection(username, password, ldap_url):
    """Create and return LDAP connection"""
    import ldap
    ldapconn = ldap.initialize(ldap_url)
    ldapconn.protocol_version = ldap.VERSION3
    ldapconn.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
    ldapconn.set_option(ldap.OPT_REFERRALS, 0)
    ldapconn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    ldapconn.bind_s(username, password)
    return ldapconn

def get_user_dn(ldap_conn, username, search_base):
    import ldap
    """Get the dn for the user, return None if there are no results or more than one"""
    result = ldap_conn.search_s(search_base, \
        ldap.SCOPE_SUBTREE, "cn={0}".format(username))
    # Remove any domaindnszone referrals
    for entry in result:
        if not entry[0]:
            result.remove(entry)
    if len(result) != 1:
        user_dn = None
    else:
        user_dn = result[0][0]
    return user_dn

def get_group_membership(groupname, username, password, search_base, ad_url, ldap_port="636"):
    """Get the members of a given group in Active Directory"""
    import ldap
    # Setup connection
    scope = ldap.SCOPE_SUBTREE
    ldap.protocol_version = ldap.VERSION3
    ldap.set_option(ldap.OPT_REFERRALS, 0)
    
    # Initalize and bind
    ad_ldap = ldap.initialize(ad_url + ":" + ldap_port)
    ad_ldap.simple_bind_s(username, password)

    searchterm = "cn=" + groupname

    # start at user 0, and setup userlist
    usercount = 0
    userlist = []

    searchcheck = True

    while searchcheck:
        retrieve_attributes = ["member;range=" + str(usercount) + "-" + str(usercount + 1499)]
        ad_result = ad_ldap.search_s(search_base, scope, searchterm, retrieve_attributes)
        if ad_result[0][1] == {}:
            return set([])

        keylist = ad_result[0][1].keys()

        # If there's an asterix, then we're at the last 'page' of results
        if "*" in str(keylist):
            searchcheck = False

            # parse the users
            for dn in ad_result[0][1].get("member;range=" + str(usercount) + "-*"):
                # entry is a bytes literal - convert to utf-8 string
                dn = dn.decode('utf-8')                
                username = dn.split("CN=")[1].split(",")[0].lower()
                userlist.append(username)

        # If no asterix, increment usercount and continue
        else:
            # parse the users
            for dn in ad_result[0][1].get("member;range=" + str(usercount) + "-" + str(usercount + 1499)):
                # entry is a bytes literal - convert to utf-8 string
                dn = dn.decode('utf-8')
                username = dn.split("CN=")[1].split(",")[0].lower()
                userlist.append(username)

            usercount = usercount + 1500

    # Return a list of usernames
    return set(userlist)

def update_group(ldap_conn, group_dn, ad_base, additions, removals):
    """Make additions and removals as necessary to the AD group specified in group_dn."""
    import ldap
    for user in additions:
        try:
            print("Working on adding {0}, to group {1}".format(user, group_dn))
            if "ou=npuser" in user.lower():
                # Full DN provided
                user_dn = user.encode('utf8')
            else:
                # Username only provided - change it to a DN
                user_dn = get_user_dn(ldap_conn, user, ad_base).encode('utf8')            
            ldap_conn.modify_s(group_dn, [(ldap.MOD_ADD, "member", [user_dn])])
            print("Added {0} to group {1}".format(user, group_dn))
        except:
            print("Error: Unable to add {0} to group {1}".format(user, group_dn))

    for user in removals:
        print("Working on removing {0}, from group {1}".format(user, group_dn))
        if "ou=npuser" in user.lower():
            # Full DN provided
            user_dn = user.encode('utf8')
        else:
            # Username only provided - change it to a DN
            user_dn = get_user_dn(ldap_conn, user, ad_base).encode('utf8')            
        
        try:
            ldap_conn.modify_s(group_dn, [(ldap.MOD_DELETE, "member", [user_dn])])
            print("Removed {0} from group {1}".format(user, group_dn))
        except:
            print("Error: Unable to remove {0} from group {1}".format(user, group_dn))

def update_group_with_report(group, groupdn, ad_base, ldap_conn, additions, removals):
    """Update the specified group with the entries the removals and additions lists.
    If there are any changes, update the output_message to include them and return that."""
    output_message = ""
    if removals or additions:
        print("{0} group removals: {1}".format(group, removals))
        print("{0} group additions: {1}".format(group, additions))
        output_message += "{0} group removals: {1}\n".format(group, removals)
        output_message += "{0} group additions: {1}\n".format(group, additions)
        update_group(ldap_conn, groupdn, ad_base, additions, removals)
    return output_message
