# SPDX-FileCopyrightText: 2022 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

import secrets  # pylint: disable=no-name-in-module

import socketpool
import wifi
import time
import random
import json

from adafruit_httpserver.mime_type import MIMEType
from adafruit_httpserver.request import HTTPRequest
from adafruit_httpserver.response import HTTPResponse
from adafruit_httpserver.server import HTTPServer
from adafruit_httpserver.server import HTTPMethod

ssid, password = secrets.SSID, secrets.PASSWORD  # pylint: disable=no-member
lastMillis = 0; #TODO just for testing

print("Connecting to", ssid)
wifi.radio.connect(ssid, password)
print("Connected to", ssid)

pool = socketpool.SocketPool(wifi.radio)
server = HTTPServer(pool)

MESSAGE_LIST = [
  {
    'id': 1,
    'from': 'John Doe',
    'to': 'YOU',
    'payload': 'Prijata sprava od hocikoho, ma byt siva, ziadne ikonky<br>Id sit adipisicing culpa cupidatat fugiat veniam proident voluptate. Ullamco nisi aliquip magna eu elit deserunt sint ea amet deserunt ex minim amet aliquip. Enim duis quis minim fugiat quis dolor aliqua Lorem elit aliquip anim. Est ex cupidatat irure et enim mollit proident. Aliqua pariatur non magna labore laboris occaecat nostrud minim aliqua.',
    'msg_type': 'text',
  },
  {
    'id': 2,
    'from': 'YOU',
    'to': 'ALL',
    'payload': 'Sprava ktoru som poslal ale neocakavam ACK, ma byt modra, v pravo dole nemaju byt ziadne ikonky<br>Commodo culpa sit culpa in minim commodo incididunt in pariatur minim fugiat. Commodo tempor elit ut nisi ex occaecat',
    'msg_type': 'text',
    'my_msg': 'true',
    'state': 'DONE'
  },
  {
    'id': 11,
    'from': 'Felix',
    'to': 'ALL',
    'payload': 'Prijata sprava od hocikoho, ma byt siva, ziadne ikonky<br>Id sit adipisicing culpa cupidatat fugiat veniam proident voluptate. Ullamco nisi aliquip magna eu elit deserunt sint ea amet deserunt ex minim amet aliquip. Enim duis quis minim fugiat quis dolor aliqua Lorem elit aliquip anim. Est ex cupidatat irure et enim mollit proident. Aliqua pariatur non magna labore laboris occaecat nostrud minim aliqua.',
    'msg_type': 'text',
  },
  {
    'id': 23,
    'from': 'YOU',
    'to': 'Felix',
    'payload': 'Sprava ktoru som poslal a ku ktorej som ZATIAL neprijal ACK (este bezi timeout tej sprave), ma byt modra, v pravo dole ikonka s prazdnym checkom<br>esse mollit sit anim minim voluptate. Laboris deserunt exercitation exercitation commodo cupidatat ad eiusmod minim. Aute elit do dolor proident tempor cupidatat officia reprehenderit.',
    'msg_type': 'wack_text',
    'my_msg': 'true',
    'state': 'REBROADCASTED'
  },
  {
    'id': 3,
    'from': 'YOU',
    'to': 'Felix',
    'payload': 'Sprava ktoru som poslal a ku ktorej som prijal ACK, ma byt modra, v pravo dole ikonka s vyfarbenym checkom<br>In eu ea esse irure aliqua culpa et aute esse laboris incididunt. Dolor laboris aliqua consectetur sint Lorem quis eu eu magna deserunt voluptate aliquip magna reprehenderit. Sit labore ipsum voluptate incididunt culpa. Labore minim irure dolor occaecat deserunt in Lorem anim nulla quis laboris labore do. Consectetur pariatur sint officia Lorem quis aute minim dolor duis occaecat.Nisi ea cillum non sit adipisicing velit sit aliquip mollit id occaecat duis et commodo. Eu officia exercitation consectetur aliquip minim cupidatat id sunt laboris occaecat consequat exercitation deserunt irure. Officia laboris consectetur consequat reprehenderit exercitation do id. Est do nostrud in irure sint. Irure sit consectetur sint enim labore incididunt sit laboris ipsum. Aliqua pariatur non in cupidatat aliquip ea quis dolore ullamco duis qui in. Exercitation occaecat cillum irure eiusmod ut ex tempor officia dolor aliqua irure velit ea.',
    'msg_type': 'wack_text',
    'my_msg': 'true',
    'state': 'ACK'
  },
  {
    'id': 111,
    'from': 'Frederick',
    'to': 'YOU',
    'payload': 'Prijata sprava od hocikoho, ma byt siva, ziadne ikonky<br>Id sit adipisicing culpa cupidatat fugiat veniam proident voluptate. Ullamco nisi aliquip magna eu elit deserunt sint ea amet deserunt ex minim amet aliquip. Enim duis quis minim fugiat quis dolor aliqua Lorem elit aliquip anim. Est ex cupidatat irure et enim mollit proident. Aliqua pariatur non magna labore laboris occaecat nostrud minim aliqua.',
    'msg_type': 'text',
  },
  {
    'id': 4,
    'from': 'YOU',
    'to': '0xABCD',
    'payload': 'WACK sprava ktoru som poslal a ku ktorej som po timeoute NEprijal ACK, ma byt modra ale s opacity, vpravo dole niesu ikonky ale bublina s informaciou o tom ze je failed, bublina sa da klikat a znovu posielat spravu<br>Culpa veniam voluptate fugiat ad consectetur sit irure non ips',
    'msg_type': 'wack_text',
    'my_msg': 'true',
    'state': 'NAK'
  },
  {
    'id': 66,
    'from': 'Enviroment sensor',
    'to': 'ALL',
    'payload': ' Temperature: 25°C Humidity: 50%<br>125 ppm CO2<br>sprava ma byt oranzova, ziadne ikonky v pravo dole',
    'msg_type': 'sensor',
  },
  {
    'id': 5,
    'from': 'YOU',
    'to': 'ALL',
    'payload': 'obycajna sprava ktoru som poslal ale ziadna dalsia node ju nerebroadcastovala, modra, opacity, dole bublina s informaciou o tom ze je failed, bublina sa da klikat a znovu posielat spravu<br>pa veniam voluptate fugiat ad consectetur sit irure non pa veniam voluptate fugiat ad consectetur sit irure non ',
    'msg_type': 'text',
    'my_msg': 'true',
    'state': 'FAILED'
  },
  {
    'id': 6,
    'from': 'Enviroment sensor',
    'to': 'ALL',
    'payload': ' Temperature: 25°C Humidity: 50%<br>125 ppm CO2<br>sprava ma byt oranzova, ziadne ikonky v pravo dole',
    'msg_type': 'sensor',
  },
]


@server.route("/")
def base(request: HTTPRequest):

    with HTTPResponse(request, content_type=MIMEType.TYPE_HTML) as response:
        response.send_file("index.html")

@server.route("/messages")
def ajax(request: HTTPRequest):
  data = {
     'messages': MESSAGE_LIST
  }
  with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
    response.send(json.dumps(data))

@server.route("/send_message", method=HTTPMethod.POST)
def send_message(request: HTTPRequest):
  #TODO data.get('max_hop')
  #TODO data.get('priority')
  data = json.loads(request.body)
  print(data)
  MESSAGE_LIST.append({
    'id': random.randint(100,50000),
    'from': 'YOU',
    'to': data.get('destination'),
    'payload': data.get('message'),
    'msg_type': 'wack_text' if data.get('wack') else 'text',
    'my_msg': 'true',
    'state': 'REBROADCASTED'
  })
  if data.get('wack'):
    global lastMillis
    lastMillis = int(time.time() * 1000)
  with HTTPResponse(request, content_type=MIMEType.TYPE_TXT) as response:
    response.send("OK")


print(f"Listening on http://{wifi.radio.ipv4_address}:80")
#server.serve_forever(str(wifi.radio.ipv4_address))

#Start the server.
server.start(str(wifi.radio.ipv4_address))
while True:
  try:
    if lastMillis != 0 and int(time.time() * 1000) - lastMillis > 5000:
      lastMillis = 0
      newState = 'ACK' if random.randint(0,1) == 1 else 'NAK'
      print("Updating message state to: " + newState)
      MESSAGE_LIST[-1]['state'] = newState

    server.poll()
  except OSError as error:
    print(error)
    continue