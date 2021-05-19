from flask import Flask
from flask import request
app = Flask(__name__)

import os
import base64
import time
import github_team_members

@app.route('/')
def home_page():
    return 'Elan'

@app.route('/add/<corpid>')
def add(corpid):
    emc_ca_root = '/home/c4dev/EMC_CA_Root.pem'
    baseurl = 'https://eos2git.cec.lab.emc.com/api/v3'
    org = 'unity-file'
    teamid = 1649
    try:
        admin = os.environ['CORPUSER']
        adminpasswd = base64.b64decode(os.environ['CORPPASSWD']).decode()
        os.environ["REQUESTS_CA_BUNDLE"] = emc_ca_root
        tm = github_team_members.TeamManager(admin, adminpasswd, baseurl, org, teamid, corpid)
        tm.add_user()
        del os.environ["REQUESTS_CA_BUNDLE"]
        return 'OK'
    except Exception as e:
        github_team_members.die('Got exception %s when adding %s' % (type(e), corpid))
    
@app.route('/remove/<corpid>')
def remove(corpid):
    emc_ca_root = '/home/c4dev/EMC_CA_Root.pem'
    baseurl = 'https://eos2git.cec.lab.emc.com/api/v3'
    org = 'unity-file'
    teamid = 1649
    delay = request.args.get('delay')
    print(delay)
    time.sleep(int(delay))
    try:
        admin = os.environ['CORPUSER']
        adminpasswd = base64.b64decode(os.environ['CORPPASSWD']).decode()
        os.environ["REQUESTS_CA_BUNDLE"] = emc_ca_root
        tm = github_team_members.TeamManager(admin, adminpasswd, baseurl, org, teamid, corpid)
        tm.remove_user()
        del os.environ["REQUESTS_CA_BUNDLE"]
        return 'OK'
    except Exception as e:
        github_team_members.die('Got exception %s when removing %s' % (type(e), corpid))




if __name__ == '__main__':
    app.run(host='0.0.0.0', port='2240')