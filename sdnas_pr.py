# -*- coding: utf-8 -*
import io
import re
import requests
import urllib3
urllib3.disable_warnings()
from datetime import datetime, timedelta
from github import Github
from bs4 import BeautifulSoup


api_url = "https://eos2git.cec.lab.emc.com/api/v3"
login_url = "https://eos2git.cec.lab.emc.com/login"
session_url = "https://eos2git.cec.lab.emc.com/session"
token = "de9fd4365f01a820c00213ac292687757d39a980"
svc_token = "860a851befd7b1587af74e4d4a775b889fb21f6d"
logfile = "2_weeks.log"

def get_prs():
    g = Github(token, base_url=api_url, verify=False)
    repo = g.get_repo("mrs-sdnas/sdnas")

    pulls = repo.get_pulls(state='closed', sort='upated', direction="desc")
    return pulls


def send_request(myurl):

    r1 = requests.get(login_url, verify=False)
    soup = BeautifulSoup(r1.text,features='lxml')
    s1 = soup.find(name='input',attrs={'name':'authenticity_token'}).get('value')
    r1_cookies = r1.cookies.get_dict()
    #print(r1_cookies)
    #print(s1)
     
    r2 = requests.post(
        session_url,
        data ={
            'commit':'Sign in',
            'utf8':'✓',
            'authenticity_token':s1,
            'login':'svc_ctdciauto',
            'password': '78^GPgau?ySW#f=x'
        },
        verify = False,
        cookies = r1.cookies.get_dict(),
    )
    #print(r2.cookies.get_dict())
    
    r3 = requests.get(
        myurl,
        verify = False,
        cookies = r2.cookies.get_dict()
 
    )
    return r3.text

def find_files(myurl):
    files = []
    rs = send_request(myurl)
    lines = (line.strip() for line in rs.splitlines())
    for line in lines:
        #print line
        matchobj = re.match(r"^diff\s--git\sa(\/.*)\sb\/.*$", line)
        if matchobj:
            files.append(matchobj.group(1))
    print files 
    return files

def filter_merged(pulls):
    with io.open(logfile, 'w', encoding='utf8') as f:
        f.write(u"====Merged PRs in 2 weeks====\n")
        for pr in pulls:
            #someone is just closed
            if pr.merged_at:
                if pr.merged_at >= since_date and "[SDNAS" in pr.title:
                    print pr.title, pr.merged_at
                    fl = find_files(pr.diff_url)
                    fls = ""
                    if fl:
                        fls = ";".join(fl)
                    print fls
                    f.write(pr.title + "\t" + str(pr.merged_at) + "\t" + pr.html_url + "\t" + fls + "\n");
                else:
                    continue

def filter_opened(pulls):
    with io.open(logfile, 'a', encoding='utf8') as f:
        f.write(u"====Open PRs in 2 weeks====\n")
        for pr in pulls:
            #someone is just closed
            if pr.updated_at:
                if pr.updated_at >= since_date:
                    print  pr.title, pr.updated_at
                    f.write(pr.title + "\t" + str(pr.updated_at) + "\t" + pr.html_url +"\n");
                else:
                    break
        
since_date = datetime.now() - timedelta(days=14)

pulls = get_prs()
filter_merged(pulls)
#filter_opened(pulls)

#url1 = "https://eos2git.cec.lab.emc.com/mrs-sdnas/sdnas/pull/6914.diff"
#url1 = "https://eos2git.cec.lab.emc.com/raw/unity-protocols/unity/pull/1690.diff"
#find_files(url1)
