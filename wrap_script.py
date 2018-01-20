#!/usr/bin/python
import sys
import subprocess
import smtplib
import json
from email.mime.text import MIMEText

CONFIG_FILE = 'wrap_script.config.json'

with open(CONFIG_FILE, 'r') as fh:
    cfg = json.loads(fh.read())

ADMIN = cfg['admin']
DEFAULT_FROM = cfg['mailer']

SMTP_HOST = cfg['smtp']['host']
SMTP_PORT = cfg['smtp']['port']
SMTP_USER = cfg['smtp']['user']
SMTP_PASS = cfg['smtp']['password']


def send_mail(body='', subject='', to=None, from_=DEFAULT_FROM, level=None):
    """Send an email with the given parameters."""
    if level:
        if not subject:
            subject = 'General %s' % level
        subject = '[%s] %s' % (level, subject)
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_
    msg['To'] = to

    s = smtplib.SMTP()
    s.connect(SMTP_HOST, SMTP_PORT)
    s.starttls()
    s.login(SMTP_USER, SMTP_PASS)
    s.sendmail(from_, [to], msg.as_string())
    s.quit()


def send_error(**kwargs):
    return send_mail(level='Error', **kwargs)


def send_info(**kwargs):
    return send_mail(level='Info', **kwargs)


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        send_error(subject='Wrapper script failure',
                   body='Failed to run a command (no command given).',
                   to=ADMIN)
        sys.exit(1)
    try:
        output = subprocess.check_output(args, stderr=subprocess.STDOUT)
        send_info(body=output, subject='Run %s success' % args[0], to=ADMIN)
    except subprocess.CalledProcessError as e:
        subject = 'failed to run %s; code %d' % (args[0], e.returncode)
        send_error(body=e.output, subject=subject, to=ADMIN)
