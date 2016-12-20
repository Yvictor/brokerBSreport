'''

Created on Dec 18, 2016
@author: Yvictor

'''
#SENTRY_DNS = os.environ.get('SENTRY_DNS','https://6db9585c13094fe0a6daf59ba35bf0f1:398fc0f8893c41f2829102661ddc00f6@sentry.io/123315')
from twse import twseBSreport

bsreporter = twseBSreport()
bsreporter.processAll()