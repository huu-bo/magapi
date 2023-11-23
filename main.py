from __future__ import annotations

import asyncio
from pyppeteer import launch
import pyppeteer.network_manager
import requests
import json

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
    while response is None and i < 10:
        await asyncio.sleep(.5)
        print('waiting for auth', i)
        i += 1
    j = await response.json()

    # await page.screenshot(path='example.png')
    await page.close()

    # page = await browser.newPage()
    # await page.setViewport({'width': 500, 'height': 500})
    # await page.setContent('<p>Bring your laptop to class.&nbsp;</p><p><br></p><p>This test will be taken on&nbsp;<a href=\\"http://exam.net/\\" target=\\"_blank\\">Exam.net</a>.&nbsp;</p>')
    # await page.screenshot(path='english.png')

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

# r = requests.get(f'https://novum.magister.net/api/personen/{persoon_id}/afspraken?status=1&tot=2023-11-10&van=2023-11-03',
#                  headers={'authorization': auth})

# print(r.status_code)
# print(r.content)

with open('payload.txt', 'r', encoding='utf-8') as file:
    payload = file.read()

for i, line in enumerate(payload.split('\n')):
    data = ('{"Id":0,"Links":null,"Start":"2023-11-22T07:00:00.000Z","Einde":"2023-11-22T07:30:00.000Z","DuurtHeleDag":false,'
            + f'"Omschrijving":"vanuit magapi2 {i} (attempt 5)","LesuurVan":null,"LesuurTotMet":null,"Type":1,"Inhoud":'
            + f'{json.dumps(line)},'
            + '"InfoType":6,"Afgerond":false,"Aantekening":null,"Vakken":null,"Docenten":null,"Lokatie":"006","Status":2,"Lokalen":null,"Groepen":null,"OpdrachtId":0,"HeeftBijlagen":false,"Bijlagen":null,"WeergaveType":1,"TaakAangemaaktOp":null,"TaakGewijzigdOp":null,"HerhaalStatus":0,"Herhaling":null,"IsOnlineDeelname":false,"Subtype":1}')

    r = requests.post(
        f'https://novum.magister.net/api/personen/{persoon_id}/afspraken',
        data=data.encode('utf-8'),
        headers={
            'Content-type': 'application/json',
            'authorization': auth
        }, timeout=1000
    )

    print(r.status_code)
    # if r.status_code != 201:
    #     print(r.content)
