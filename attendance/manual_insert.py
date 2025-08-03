from datetime import datetime
from garden import Garden
import pprint
import requests
import json
from urllib.parse import urlparse

garden = Garden()
db_tools = garden.db_tools

def get_commit(commit_url):
    parse_result = urlparse(commit_url)
    # print(parse_result)
    (_, user, repo, commit, sha) = parse_result.path.split("/")

    api_url = 'https://api.github.com/repos/%s/%s/commits/%s' % (user, repo, sha)

    r = requests.get(api_url)

    # print(r.json())
    ts_datetime = datetime.strptime(r.json()["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%S%z")
    message = r.json()["commit"]["message"]
    ts = str(ts_datetime.timestamp())
    return {
        "user": user,
        "ts": ts,
        "ts_datetime": ts_datetime,
        "sha": sha,
        "sha_short": sha[:8],
        "message": message,
        }

# commit_url = 'https://github.com/gintire/TIL/commit/f7c915de5e029270744553ca2b0f88da823e44c5'
#commit_url = 'https://github.com/gintire/TIL/commit/93a4f58de89830b9cca0f1d554c2fe3656531bc3'
#commit_url = 'https://github.com/js7483/ddd-study/commit/94e153a2ffa1768c1843f414375616d73c68b93a'
# commit_url = 'https://github.com/Wealgo/changmin/commit/d6ecda2127ee11d2741bb42258affaf2e803bcb0'
commit_url = 'https://github.com/itsnamgyu/TIW/commit/f3d807901dc16d1c049dc14c02c1916234af8abc'

commit = get_commit(commit_url)
# print(commit)
print(commit["user"])
print(commit["sha"])
print(commit["sha_short"])
print(commit["ts"])
print(commit["ts_datetime"])
print(commit["ts_datetime"].strftime("%Y-%m-%d"))
print(commit["message"])

text = '*manual insert %s by june.kim*\n<%s|`%s`> - %s' % ("2020-04-11", commit_url, commit["sha_short"], commit["message"])

message = {'attachments':
    [{
        'author_name': commit["user"],
        'text': text
    }],
    'ts': commit["ts"],
    'ts_for_db': commit["ts_datetime"],
    'type': 'message',
    'user': 'UU9RDT66M'
}

print(message)
# exit(-1)


try:
    # PostgreSQL에 데이터 삽입
    insert_query = """
        INSERT INTO slack_messages (ts, ts_for_db, bot_id, type, text, "user", team, bot_profile, attachments)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ts) DO NOTHING
    """
    
    params = (
        message['ts'],
        message['ts_for_db'],
        message.get('bot_id'),
        message.get('type'),
        message.get('text'),
        message.get('user'),
        message.get('team'),
        None,  # bot_profile
        json.dumps(message.get('attachments')) if message.get('attachments') else None
    )
    
    result = db_tools.execute_query(insert_query, params, fetch_all=False)
    print(f"Inserted {result} rows")
    print(message)
except Exception as e:
    print(e)

