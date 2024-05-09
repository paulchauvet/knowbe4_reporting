import smtplib


def send_html_email(message_text, recipient_email, sender_email, sender_name, subject, headers=[]):
    """Send an HTML email"""
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    smtp_server_name = "smtp.newpaltz.edu"
    smtp_port = 25

    message = MIMEMultipart("alternative")
    if headers != []:
        # Use the default To header if it's not specified earlier
        if "To" not in headers.keys():
            message["To"] = recipient_email

    message["From"] = sender_name + "<" + sender_email + ">"
    message["Subject"] = subject
    message["Precedence"] = "bulk"
    message["Auto-Submitted"] = "auto-generated"

    # In case custom headers are specified
    if headers != []:
        for header_name, header_value in headers.items():
            message[header_name] = header_value



    html_message_preface = """\
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            <title>{0}</title>
        </head>
        <body>""".format(subject)

    html_message_end = """\
        </body>
        </html>"""

    html_message = html_message_preface + message_text + html_message_end



    # Attach both plain and HTML versions
    #message.attach(MIMEText(plain, 'plain'))
    message.attach(MIMEText(html_message, 'html'))


    # Create secure connection with server and send email
    server = smtplib.SMTP(smtp_server_name, smtp_port)
    #server.login(email, password)
    text = message.as_string()
    server.sendmail(sender_email, recipient_email, text)
    server.quit()

