#!/usr/bin/python3

__author__ = "Colin Reese"
__copyright__ = "Copyright 2021, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

# import utility
# import netfun
from time import sleep
# from datalib import gettimestring

def gettimestring(timeinseconds=None):
    import time
    if timeinseconds:
        try:
            timestring = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timeinseconds))
        except TypeError:
            timestring = ''
    else:
        timestring = time.strftime('%Y-%m-%d %H:%M:%S')
    return timestring

def runping(pingAddress='8.8.8.8', numpings=1, quiet=False):
    pingtimes = []
    import subprocess
    for i in range(numpings):
        # Perform the ping using the system ping command (one ping only)
        import os

        try:
            # result, err = Popen(['ping','-c','1', pingAddress], stdout=PIPE, stderr=PIPE).communicate()
            # Default ping timeout is 500ms. This is about right.
            # if quiet:
            # result = subprocess.Popen(['fping','-c','1', pingAddress], stdout=os.devnull)
            # else:
            if quiet:
                DEVNULL = open(os.devnull, 'wb')
                result = subprocess.Popen(['fping', '-c', '1', pingAddress], stdout=subprocess.PIPE, stderr=DEVNULL)
                DEVNULL.close()
            else:
                result = subprocess.Popen(['fping', '-c', '1', pingAddress], stdout=subprocess.PIPE)

            pingresult = result.stdout.read().decode('utf-8')
            # print(pingresult)
        except:
            print('there is problem with your pinging')
            pingtimes.append(-1)
        else:
            # Extract the ping time
            if pingresult:
                resultsplit = pingresult.split(',')
                # print(resultsplit)
                # print(resultsplit[2].split('ms')[0].strip())
                latency = float(resultsplit[2].split('ms')[0].strip())
                # print('latency is ' + str(latency))
                pingtimes.append(latency)

            else:
                pingtimes.append(0)


            """ OLD STUFF
            if len(result) < 2:
                # Failed to find a DNS resolution or route
                failed = True
                latency = 0
            else:
                index = result.find('time=')
                if index == -1:
                    # Ping failed or timed-out
                    failed = True
                    latency = 0
                else:
                    # We have a ping time, isolate it and convert to a number
                    failed = False
                    latency = result[index + 5:]
                    latency = latency[:latency.find(' ')]
                    latency = float(latency)
            """
    return pingtimes


def pingstatus(pingAddress='8.8.8.8', numpings=1, threshold=2000, quiet=True):
    pingtimes = runping(pingAddress, numpings, quiet=True)
    pingmax = max(pingtimes)
    pingmin = min(pingtimes)
    pingave = sum(pingtimes)/len(pingtimes)
    if pingave == 0:
        status = 2
    elif pingave <= threshold and pingave > 0:
        status = 0
    else:
        status = 2

    return {'pingtimes': pingtimes, 'pingmax': pingmax, 'pingmin': pingmin, 'pingave': pingave, 'status':status}


class Gmail:
    def __init__(self, server='smtp.gmail.com', port=587, subject='default subject', message='default message',
                 login='cupidmailer@interfaceinnovations.org', password='cupidmail', recipient='cupid_status@interfaceinnovations.org', sender='CuPID Mailer'):
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

        if isinstance(self.recipient, list):
            self.recipients = self.recipient
        elif self.recipient.find(',') >=0:
            self.recipients = self.recipient.split(',')
        else:
            self.recipients = [self.recipient]



        session = smtplib.SMTP(self.server, self.port)

        session.ehlo()
        session.starttls()
        session.ehlo
        session.set_debuglevel(1)
        session.login(self.login, self.password)

        print('MAIL RECIPIENT!')
        print(self.recipients)
        for recipient in self.recipients:
            headers = ['From:' + self.sender,
                       'Subject:' + self.subject,
                       'To:' + recipient,
                       'MIME-Version: 1.0',
                       'Content-Type: text/plain']
            headers = '\r\n'.join(headers)
            if recipient:
                session.sendmail(self.sender, recipient.strip(), headers + '\r\n\r\n' + self.message)
        session.quit()



class NetworkMonitor:

    def __init__(self, **kwargs):
        self.settings = {
            'domains': ['interfaceinnovations.org', 'cupidcontrol.com'],
            'ping_threshold_ms': 1000,
            'check_frequency_ms': 60000,
            'retries': 3,
            'quiet': False
        }
        self.settings.update(kwargs)

        for item, value in self.settings.items():
            print(item, value)
            setattr(self, item, value)

    def run_once(self):
        self.run(run_once=True)

    def run(self, run_once=False):
        if not self.quiet:
            print('checking {} domains ..'.format(len(self.domains)))

            while True:
                all_fine = True
                for domain in self.domains:
                    if not self.quiet:
                        print('checking domain {}'.format(domain))

                    check_result = self.check_domain(domain)

                    if not self.quiet:
                        print('result for domain {} : status = {}'.format(domain, check_result['status']))

                    if check_result['status']:
                        all_fine = False
                        this_mail = Gmail()
                        this_mail.recipient = ['offline_status@interfaceinnovations.org','5038886154@vtext.com']
                        this_mail.subject = '{} is offline, status {}'.format(domain, check_result['status'])
                        this_mail.message = 'AWS ping utility shows domain {} to be offline at {}'.format(domain, gettimestring())

                        this_mail.send()
                if all_fine:
                    this_mail = Gmail()
                    this_mail.subject = 'All domains appear to be online'.format(domain, check_result['status'])
                    this_mail.message = 'AWS ping utility shows domains {} to be online'.format(self.domains,
                                                                                                      gettimestring())
                    this_mail.send()

                if run_once:
                    break

                if not self.quiet:
                    print('sleeping for {}ms'.format(self.check_frequency_ms))
                    sleep(self.check_frequency_ms/1000)

    def check_domain(self, domain):
        check_results = pingstatus(domain, threshold=self.ping_threshold_ms, quiet=self.quiet)
        return check_results


if __name__=='__main__':
    monitor = NetworkMonitor()
    monitor.run_once()