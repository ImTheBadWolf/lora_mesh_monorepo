from header import *
from message import *
from node import *
from time import sleep

node0 = Node(0x0000)
node1 = Node(0x0001)
node2 = Node(0x0002)
node3 = Node(0x0003)
node4 = Node(0x0004)
node5 = Node(0x0005)
node6 = Node(0x0006)
node7 = Node(0x0007)
node8 = Node(0x0008)
node9 = Node(0x0009)
node10 = Node(0x00010)
node11 = Node(0x00011)
node12 = Node(0x00012)
node13 = Node(0x00013)
node14 = Node(0x00014)
node15 = Node(0x00015)
node16 = Node(0x00016)


node0.add_neighbor(node1, 15)
node0.add_neighbor(node2)

node1.add_neighbor(node0)
node1.add_neighbor(node2)
node1.add_neighbor(node6)

node2.add_neighbor(node0)
node2.add_neighbor(node1)
node2.add_neighbor(node3)

node3.add_neighbor(node2)
node3.add_neighbor(node4)

node4.add_neighbor(node3)
node4.add_neighbor(node2)
node4.add_neighbor(node5)

node5.add_neighbor(node4)
node5.add_neighbor(node6)

node6.add_neighbor(node5)
node6.add_neighbor(node7)
node6.add_neighbor(node1)

node7.add_neighbor(node6)
node7.add_neighbor(node8)

node8.add_neighbor(node7)
node8.add_neighbor(node9, 15)
node8.add_neighbor(node10)
#node8.add_neighbor(node11)

node9.add_neighbor(node8)
node9.add_neighbor(node10)
node9.add_neighbor(node12)

node10.add_neighbor(node8)
node10.add_neighbor(node9)
node10.add_neighbor(node11, 2)
node10.add_neighbor(node13, 15)

#node11.add_neighbor(node8)
node11.add_neighbor(node10)
node11.add_neighbor(node13)

node12.add_neighbor(node9)
node12.add_neighbor(node16)

node13.add_neighbor(node10)
node13.add_neighbor(node11)
node13.add_neighbor(node14)

node14.add_neighbor(node13)
node14.add_neighbor(node15)

node15.add_neighbor(node14)
node15.add_neighbor(node16)

node16.add_neighbor(node15)
node16.add_neighbor(node12)


node0.send_message(0x0012, 'Hello World!')
sleep(0.2)

for i in range(0, 2000000):
  node0.tick()
  node1.tick()
  node2.tick()
  node3.tick()
  node4.tick()
  node5.tick()
  node6.tick()
  node7.tick()
  node8.tick()
  node9.tick()
  node10.tick()
  node11.tick()
  node12.tick()
  node13.tick()
  node14.tick()
  node15.tick()
  node16.tick()
