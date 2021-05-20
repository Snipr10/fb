import argparse
import json
import re
import time

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
                print(story)
                text, date, watch, like, share, comment, owner_name, owner_url = get_text(story)
                with open('story.txt', 'a') as f:
                    f.write(story+"\n")
                    f.write(text + "\n")
                    f.write('date ' + str(date) + "\n")
                    f.write('watch ' + str(watch) + "\n")
                    f.write('like ' + str(like) + "\n")
                    f.write('share ' + str(share) + "\n")
                    f.write('comment ' + str(comment) + "\n")
                    f.write('owner_name ' + str(owner_name) + "\n")
                    f.write('owner_url ' + str(owner_url) + "\n")
                    f.write('owner_id ' + str(data_url[1]) + "\n")

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


def get_text(url):
    try:
        # time.sleep(60)
        # test
        res = requests.get(url)
        res_text = res.text
        try:
            soup = BeautifulSoup(res_text)
        except Exception as e:
            print(e)
        try:
            text = soup.find_all("div", {"class": "bx"})[0].text
        except Exception as e:
            text = soup.find_all("div", {"class": "bw"})[0].text

        date = soup.find_all("abbr")[0].text
        watch = find_value(res_text, 'WatchAction"', 24, separator='}')
        like = find_value(res_text, 'LikeAction"', 24, separator='}')
        share = find_value(res_text, 'ShareAction"', 24, separator='}')
        comment = find_value(res_text, 'CommentAction"', 24, separator='}')
        try:
            owner = soup.find_all("h3", {'class': ['bt', 'bu', 'bv', 'bw']})[0]
            owner_name = owner.text
            try:

                owner_url = owner.find_all('a', href=True)[0]['href']
                owner_url = owner_url[:owner_url.find('&')].replace("?refid=52", "")
            except Exception as e:
                owner_url = '/profile.php?' + url[url.find("&id=") + 1:]
        except Exception as e:
            print(e)
            owner_name = None
            owner_url = '/profile.php?' + url[url.find("&id=") + 1:]

    except Exception as e:
        print(e)
    return text, date, watch, like, share, comment, owner_name, owner_url



if __name__ == "__main__":

    # get_text('https://m.facebook.com/story.php?story_fbid=3189586617807598&id=121860194580271')

    email = "79309732752"
    password = "afOBEpOBEk74843"
    session = requests.session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'
    })

    fb_dtsg, user_id, xs, token = login(session, email, password)
    q = 'Пицца с грибами'

    search(session, fb_dtsg, user_id, xs, token, q)
    if user_id:
        print('{0}:{1}:{2}'.format(fb_dtsg, user_id, xs))
    else:
        print('Login Failed')