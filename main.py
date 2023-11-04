from __future__ import annotations

import asyncio
from pyppeteer import launch
import pyppeteer.network_manager
import requests

with open('credentials.txt', encoding='utf-8') as file:
    username = file.readline()
    password = file.readline()

auth: None | str = None
response: None | pyppeteer.network_manager.Response = None
persoon_id: None | int = None


def on_response(r: pyppeteer.network_manager.Response):
    global response
    if r.url.startswith('https://novum.magister.net/api/account'):
        response = r


def on_request(r: pyppeteer.network_manager.Request):
    print(r.url)
    if r.url.startswith('https://novum.magister.net/api/account'):
        global auth
        print(r.method)
        print(r.headers)
        try:
            auth = r.headers['authorization']
        except KeyError:
            print('no token?')
            auth = 'error'


async def main():
    browser = await launch(headless=True)
    page = await browser.newPage()
    url = 'https://novum.magister.net/magister/#/agenda'
    await page.goto(url, timeout='networkidle0')

    await page.waitForSelector('#username', visible=True)

    await page.type('#username', username)
    await page.click('#username_submit')
    await page.waitForSelector('#rswp_password', visible=True)
    await page.type('#rswp_password', password)

    # await page.setRequestInterception(True)
    page.on('request', on_request)
    page.on('response', on_response)

    await page.click('#rswp_submit')

    # print(await page.evaluate('navigator.userAgent', force_expr=True))

    # await page.waitForSelector('#afsprakenLijst', visible=True)
    i = 0
    while auth is None and i < 10:
        await asyncio.sleep(.5)
        print('waiting for token', i)
        i += 1

    i = 0
    while auth is None and i < 10:
        await asyncio.sleep(.5)
        print('waiting for account', i)
    j = await response.json()

    # await page.screenshot(path='example.png')
    await browser.close()

    global persoon_id
    if 'Persoon' not in j:
        print('Error')
        return
    p = j['Persoon']
    if 'Id' not in p:
        print('Error')
        return
    persoon_id = p['Id']

asyncio.get_event_loop().run_until_complete(main())

if persoon_id is None:
    print('no persoon_id')
    exit(1)

r = requests.get(f'https://novum.magister.net/api/personen/{persoon_id}/afspraken?status=1&tot=2023-11-10&van=2023-11-03',
                 headers={'authorization': auth})

print(r.status_code)
print(r.content)
