import argparse
import requests
import pyquery


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


def search(session, fb_dtsg_ag, user, xs, token, cursor=None):
    q = 'Лукашенко'

    url = 'https://m.facebook.com/search/posts/?q=%s&source=filter&' \
          'fb_dtsg_ag=%s&__a=AYnmX0A2hAmjDWfmKoVolMOtFA9NnM16t-BVbT6UQ6JYSsKG3ZLwM51qfB9Y7FGT_uYB5T5kK5sXAHBC6fg9--US' \
          '-q0H3rkLfbzCYOrgr0O4Rg' %(q, token)
    if cursor:
        url = url + "&cursor=" + cursor
    headers = {'cookie': 'c_user=' + user + '; xs='+xs+';'}

    res = requests.get(url, headers=headers)
    cursor = find_value(res.text, 'cursor=', num_sep_chars=0, separator='&amp')
    # next
    # search(session, fb_dtsg_ag, user, xs, token, cursor) - WORK!
    return res, cursor


def find_value(html, key, num_sep_chars=1, separator='"'):
    start_pos = html.find(key)
    if start_pos == -1:
        return None
    start_pos += len(key) + num_sep_chars
    end_pos = html.find(separator, start_pos)
    return html[start_pos:end_pos]


if __name__ == "__main__":
    email = "79910393419"
    password = "qBYxj33184"
    session = requests.session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:39.0) Gecko/20100101 Firefox/39.0'
    })

    fb_dtsg, user_id, xs, token = login(session, email, password)
    search(session, fb_dtsg, user_id, xs, token)
    if user_id:
        print('{0}:{1}:{2}'.format(fb_dtsg, user_id, xs))
    else:
        print('Login Failed')