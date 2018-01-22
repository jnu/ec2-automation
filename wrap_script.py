#!/usr/bin/python
"""Send output from a command as an email.

Usage:
./wrap_script.py <config_file> <cmd> [<arg1>, ... <argN>]

    config_file     Path to JSON mailer config
    cmd             Command to execute
    arg1 ... argN   Arguments to cmd

Example:
$ ./wrap_script.py config.json ./my_script arg1 ...

Config:
    The config file is JSON and requires the following parameters:

    WrapScriptConfig
        admin       str         Email address to send output to
        mailer      str         The "from" address
        smtp        SMTPConfig  Config for SMTP server

    SMTPConfig
        host        str         SMTP server host
        port        int         SMTP server port
        user        str         SMTP user
        password    str         SMTP password

Example Config:
{
    "admin": "foo@bar.com",
    "mailer": "\"Auto Bot\" <no-reply@bar.com>",
    "smtp": {
        "host": "smtp.bar.com",
        "port": 587,
        "user": "smtp_user",
        "password": "53cr37p@55w0rd"
    }
}
"""
import sys
import subprocess
import smtplib
import json
from email.mime.text import MIMEText


def send_mail(smtp_cfg, body='', subject='', to=None, from_=None, level=None):
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
    s.connect(smtp_cfg['host'], smtp_cfg['port'])
    s.starttls()
    s.login(smtp_cfg['user'], smtp_cfg['password'])
    s.sendmail(from_, [to], msg.as_string())
    s.quit()


def send_error(*args, **kwargs):
    return send_mail(*args, level='Error', **kwargs)


def send_info(*args, **kwargs):
    return send_mail(*args, level='Info', **kwargs)


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as fh:
        cfg = json.loads(fh.read())

    to_addr = cfg['admin']
    from_addr = cfg['mailer']
    smtp_cfg = cfg['smtp']
    args = sys.argv[2:]

    if not args:
        send_error(smtp_cfg,
                   subject='Wrapper script failure',
                   body='Failed to run a command (no command given).',
                   to=to_addr,
                   from_=from_addr)
        sys.exit(1)
    try:
        output = subprocess.check_output(args, stderr=subprocess.STDOUT)
        send_info(smtp_cfg,
                  body=output,
                  subject='Run %s success' % args[0],
                  to=to_addr,
                  from_=from_addr)
    except subprocess.CalledProcessError as e:
        subject = 'failed to run %s; code %d' % (args[0], e.returncode)
        send_error(smtp_cfg,
                   body=e.output,
                   subject=subject,
                   to=to_addr,
                   from_=from_addr)
