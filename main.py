import argparse
import json
import re

import requests
import pyquery
from bs4 import BeautifulSoup


def login(session, email, password):
    # load Facebook's cookies.
    response = session.get('https://m.facebook.com')

    # login to Facebook
    response = session.post('https://m.facebook.com/login.php', data={
        'email': email,
        'pass': password
    }, allow_redirects=False)

    # If c_user cookie is present, login was successful
    if 'c_user' in response.cookies:

        # Make a request to homepage to get fb_dtsg token
        homepage_resp = session.get('https://m.facebook.com/home.php')

        dom = pyquery.PyQuery(homepage_resp.text.encode('utf8'))
        fb_dtsg = dom('input[name="fb_dtsg"]').val()
        token = find_value(homepage_resp.text, 'dtsg_ag":{"token":')
        return fb_dtsg, response.cookies['c_user'], response.cookies['xs'], token
    else:
        return False


def search(session, fb_dtsg_ag, user, xs, token, q, cursor=None, urls = []):

    url = 'https://m.facebook.com/search/posts/?q=%s&source=filter&pn=8&isTrending=0&' \
          'fb_dtsg_ag=%s&__a=AYlcAmMg3mcscBWQCbVswKQbSUum-R7WYoZMoRSwBlJp6gjuv2v2LwCzB_1ZZe4khj4N2vM7UjQWttgYqsq7DxeUlgmEVmSge5LOz1ZdWHEGQQ' %(q, token)
    if cursor:
        url = url + "&cursor=" + cursor
    headers = {'cookie': 'c_user=' + user + '; xs='+xs+';'}

    res = requests.get(url, headers=headers)
    res_json = json.loads(res.text.replace("for (;;);", ''))
    # story_url = find_value(res_json['payload']['actions'][0]['html'], "/story.php?", num_sep_chars=0, separator='&amp;__tn__=%2AW')
    # data_url = story_url.split('&amp;')
    # story = 'https://m.facebook.com/story.php?%s&%s' %(data_url[0], data_url[1])
    last_story_fbid = None
    id = None

    for story in re.findall(r'story_fbid=\d+&amp;id=\d+', res_json['payload']['actions'][0]['html']):
        data_url = story.split('&amp;')
        if last_story_fbid != data_url[0] or id != data_url[1]:

            story = 'https://m.facebook.com/story.php?%s&%s' % (data_url[0], data_url[1])
            if story not in urls:
                with open('story.txt', 'a') as f:
                    f.write(story+"\n")
                    f.close()
                last_story_fbid = data_url[0]
                id = data_url[1]
                urls.append(story)
    cursor = find_value(res.text, 'cursor=', num_sep_chars=0, separator='&amp')

    search(session, fb_dtsg_ag, user, xs, token, q, cursor, urls)
    return res, cursor


def find_value(html, key, num_sep_chars=1, separator='"'):
    start_pos = html.find(key)
    if start_pos == -1:
        return None
    start_pos += len(key) + num_sep_chars
    end_pos = html.find(separator, start_pos)
    return html[start_pos:end_pos]



if __name__ == "__main__":
    email = "79309732752"
    password = "afOBEpOBEk74843"
    session = requests.session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'
    })

    fb_dtsg, user_id, xs, token = login(session, email, password)
    q = 'путин'

    search(session, fb_dtsg, user_id, xs, token, q)
    if user_id:
        print('{0}:{1}:{2}'.format(fb_dtsg, user_id, xs))
    else:
        print('Login Failed')