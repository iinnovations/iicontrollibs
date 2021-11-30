#!/usr/bin/python3

__author__ = "Colin Reese"
__copyright__ = "Copyright 2021, Interface Innovations"
__credits__ = ["Colin Reese"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Colin Reese"
__email__ = "support@interfaceinnovations.org"
__status__ = "Development"

import utility
import netfun
from time import sleep
from datalib import gettimestring


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

    def run(self):
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
                        this_mail = utility.gmail()
                        this_mail.subject = '{} is offline, status {}'.format(domain, check_result['status'])
                        this_mail.message = 'AWS ping utility shows domain {} to be offline at {}'.format(domain, gettimestring())
                        this_mail.send()
                if all_fine:
                    this_mail = utility.gmail()
                    this_mail.subject = 'All domains appear to be online'.format(domain, check_result['status'])
                    this_mail.message = 'AWS ping utility shows domains {} to be online'.format(self.domains,
                                                                                                      gettimestring())
                    this_mail.send()

                if not self.quiet:
                    print('sleeping for {}ms'.format(self.check_frequency_ms))
                    sleep(self.check_frequency_ms/1000)

    def check_domain(self, domain):
        check_results = netfun.pingstatus(domain, threshold=self.ping_threshold_ms, quiet=self.quiet)
        return check_results


if __name__=='__main__':
    monitor = NetworkMonitor()
    monitor.run()