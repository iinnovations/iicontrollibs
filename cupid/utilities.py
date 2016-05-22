#!/usr/bin/env python

__author__ = 'Colin Reese'
__copyright__ = 'Copyright 2014, Interface Innovations'
__credits__ = ['Colin Reese']
__license__ = 'Apache 2.0'
__version__ = '1.0'
__maintainer__ = 'Colin Reese'
__email__ = 'support@interfaceinnovations.org'
__status__ = 'Development'


import datalib


def log(logfile, message, reqloglevel=1, currloglevel=1):
    if currloglevel >= reqloglevel:
        logfile = open(logfile, 'a')
        logfile.writelines([datalib.gettimestring() + ' : ' + message + '\n'])
        logfile.close()


class gmail:
    def __init__(self, server='smtp.gmail.com', port=587, subject='default subject', message='default message',
                 login='cupidmailer@interfaceinnovations.org', password='cupidmail', recipient='info@interfaceinnovations.org', sender='CuPID Mailer'):
        self.server = server
        self.port = port
        self.message = message
        self.subject = subject
        self.sender = sender
        self.login = login
        self.password = password
        self.recipient = recipient
        self.sender = sender

    def send(self):
        import smtplib

        headers = ['From:' + self.sender,
                  'Subject:' + self.subject,
                  'To:' + self.recipient,
                  'MIME-Version: 1.0',
                  'Content-Type: text/plain']
        headers = '\r\n'.join(headers)

        session = smtplib.SMTP(self.server, self.port)

        session.ehlo()
        session.starttls()
        session.ehlo
        session.login(self.login, self.password)

        session.sendmail(self.sender, self.recipient, headers + '\r\n\r\n' + self.message)
        session.quit()
