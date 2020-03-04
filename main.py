#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import click
import sys
from libgithub import GitHubClient
from pprint import pprint
import json

test = 'ansible-collections/vmware'

@click.command()
@click.option('-d', '--debug', help='Debug', is_flag=True, default=True)
@click.option('-v', '--verbose', help='verbose', is_flag=True, default=False)
@click.option('--dest', help='Destination organization', default=test)
@click.option('--src', help='Source organization', default='ansible/ansible')
@click.option('--issue', help='Issue to migrate')
def main(issue, debug, dest, src, verbose):
    gh = GitHubClient()
    gh.create_github_session()
    is_pr = False
    issue_details = gh.get_issue(
        project_full_name=src,
        issue_number=issue,
        is_pr=is_pr,
    )
    comment_data = {
            'project_full_name': src,
            'issue_number': issue,
        }
    src_comments = gh.get_comments(**comment_data)

    issue_data = {
        'title': issue_details['title'],
        'body': issue_details['body'],
    }

    r = gh.create_issue(dest, **issue_data)
    if not r:
        print("Failed to migrate %s" % issue_details['html_url'])

    print(r['html_url'])
    comments = src_comments + [
        'Migrated from %s' % issue_details['html_url'],
        'cc @%s' % issue_details['user']['login']
    ]
    dest_issue_number = r['number']
    comment_data = {
        'issue_number': dest_issue_number ,
        'project_full_name': dest,
        'comment_line': None
    }
    for comment in comments:
        comment_data['comment_line'] = comment
        r = gh.create_comment(**comment_data)
        if not r:
            print("Failed to comment %s" % dest_issue_number)

    issue_data = {
        'project_full_name': src,
        'issue_number': issue,
        'state': 'closed',
    }
    r = gh.close_issue(**issue_data)
    if not r:
        print("Failed to close issue %s" % issue)

if __name__ == "__main__":
    main()
