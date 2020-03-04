#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import requests
import sys
import json


class GitHubClient():
    def __init__(self):
        self.GITHUB_BASE_URL = "https://api.github.com"
        self.token = None
        self.session = None

    def create_github_session(self):
        self.session = requests.Session()
        with open(os.path.join(os.path.expanduser("~"), '.github_api')) as file_:
            token = file_.read().rstrip("\n")

        if not token:
            sys.exit("Unable to read GitHub API file")

        self.session.headers.update({
            'Authorization': 'token %s' % token
        })

    def get_issue(self, project_full_name=None, issue_number=None, is_pr=False):
        if not all([project_full_name, issue_number]):
            return {}
        pr_link = 'issues'
        if is_pr:
            pr_link = 'pulls'

        pr_url = self.GITHUB_BASE_URL + "/repos/%s/%s/%s" % (project_full_name, pr_link, issue_number)
        return self.session.get(pr_url).json()

    def create_issue(self, project_full_name=None, **kwargs):
        if project_full_name is None:
            return False
        issue_url = self.GITHUB_BASE_URL + '/repos/%s/issues' % project_full_name
        r = self.session.post(issue_url, json.dumps(kwargs))
        if r.status_code == 201:
            return r.json()
        return False

    def close_issue(self, **kwargs):
        project_full_name = kwargs.get('project_full_name')
        issue_number = kwargs.get('issue_number')
        del kwargs['project_full_name']
        del kwargs['issue_number']

        issue_url = self.GITHUB_BASE_URL + '/repos/%s/issues/%s' % (project_full_name, issue_number)
        r = self.session.post(issue_url, json.dumps(kwargs))
        if r.status_code == 200:
            return r.json()
        return False

    def create_comment(self, **kwargs):
        if kwargs['project_full_name'] is None:
            return False
        project_full_name = kwargs.get('project_full_name')
        issue_number = kwargs.get('issue_number')
        comment_url = self.GITHUB_BASE_URL + '/repos/%s/issues/%s/comments' % (project_full_name, issue_number)
        data = {
            'body': kwargs.get('comment_line'),
        }
        r = self.session.post(comment_url, data=json.dumps(data))
        if not r.ok:
            return False
        return r.json()

    def get_all_items(self, url, items=[]):
        resp = self.session.get(url)
        new_items = []
        for i in resp.json():
            if i['user']['login'] != 'ansibot':
                new_items.append("@%s said - <br> %s " % (i['user']['login'], i['body']))
        if len(new_items) == 0:
            return items
        link = resp.headers.get('link')
        if link is None:
            return items + new_items
        next_url = self.find_next(link)
        if next_url is None:
            return items + new_items
        return self.get_all_items(next_url, items=items + new_items)

    def find_next(self, link):
        for l in link.split(','):
            a, b = l.split(';')
            if b.strip() == 'rel="next"':
                return a.strip()[1:-1]

    def get_comments(self, **kwargs):
        project_full_name = kwargs.get('project_full_name')
        issue_number = kwargs.get('issue_number')
        comment_url = self.GITHUB_BASE_URL + '/repos/%s/issues/%s/comments' % (project_full_name, issue_number)
        comments = self.get_all_items(url=comment_url)
        return comments