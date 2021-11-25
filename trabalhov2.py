import threading
import random
import collections
import time


class Client(threading.Thread):

    def __init__(self, clientNumber, saloon):
        threading.Thread.__init__(self)
        self.clientNumber = clientNumber
        self.saloon = saloon
        self.drink = True
        self.eventWait = threading.Event()

    def proceed(self):
        self.eventWait.set()

    def order(self):
        if random.choice(['bebe', 'nao bebe', 'bebe']) == 'nao bebe':
            self.drink = False
            self.saloon.addToNoDrink(self)
            self.eventWait.wait()
            self.eventWait.clear()
            print("Cliente", str(self.clientNumber), "nao vai beber")
            self.saloon.waitToDrink()

        else:
            self.drink = True
            self.saloon.addToDrink(self)

    def orderWait(self):
        self.eventWait.wait()
        self.eventWait.clear()

    def receiveOrder(self):
        time.sleep(1)
        print("Cliente",
              str(self.clientNumber),
              "bebendo")

    def consumeOrder(self):
        time.sleep(1)
        print("Cliente", str(self.clientNumber), "bebeu")
        self.saloon.waitToDrink()

    def run(self):
        while not self.saloon.close():
            self.order()

            if self.drink:
                self.orderWait()
                self.receiveOrder()
                self.consumeOrder()

####################################################################################################################################


class Waiter(threading.Thread):

    def __init__(self, maxClients, waiterNumber, saloon):
        threading.Thread.__init__(self)
        self.maxClients = maxClients
        self.waiterNumber = waiterNumber
        self.saloon = saloon
        self.orderNoted = []

    def receiveMaxOrder(self):
        maxOrder = len(self.orderNoted)

        while maxOrder < self.maxClients:
            currentClient = self.saloon.takeOrder()

            if currentClient is not None:

                if currentClient.drink:
                    self.orderNoted.append(currentClient)
                    print("Garcom", str(self.waiterNumber), "recebeu o pedido do cliente", str(
                        currentClient.clientNumber))

                else:
                    currentClient.proceed()

            else:
                break

    def registerOrder(self):
        hasOrder = len(self.orderNoted)

        if hasOrder > 0:
            time.sleep(1)
            print("Garcom", str(self.waiterNumber), "registrou os pedidos dos clientes", str(
                [i.clientNumber for i in self.orderNoted])[1:-1])

    def deliveryOrder(self):
        for i in self.orderNoted:
            i.proceed()
            print("Garcom", str(self.waiterNumber),
                  "entregou para o cliente", str(i.clientNumber))

        self.orderNoted.clear()

    def run(self):
        while not self.saloon.close():
            self.receiveMaxOrder()
            self.registerOrder()
            self.deliveryOrder()

####################################################################################################################################


class Saloon(threading.Thread):

    def __init__(self, numberOfClients, totalRounds):
        self.numberOfClients = numberOfClients
        self.totalRounds = totalRounds
        self.notDrinkYet = numberOfClients
        self.arrDrink = collections.deque([], 1)
        self.arrNoDrink = collections.deque([], 1)
        self.lock = threading.Condition()
        self.lockAux = threading.Condition()
        self.waitAllToDrink = threading.Condition()
        self.empty = threading.Semaphore(1)
        self.full = threading.Semaphore(0)
        self.totalOrdered = 0
        self.round = 0

    def waitToDrink(self):
        with self.waitAllToDrink:

            if self.notDrinkYet - 1 == 0:
                self.notDrinkYet = self.numberOfClients
                self.round = self.round + 1

                if self.round != self.totalRounds:
                    self.totalOrdered = 0
                    print("\nRodada:", str(self.round + 1))

                self.waitAllToDrink.notifyAll()
            else:
                self.notDrinkYet = self.notDrinkYet - 1
                self.waitAllToDrink.wait()

    def close(self):
        return self.totalRounds == self.round

    def addToDrink(self, client):
        self.empty.acquire()
        with self.lock:
            self.arrDrink.append(client)

        self.full.release()

    def addToNoDrink(self, client):
        self.empty.acquire()
        with self.lock:
            self.arrNoDrink.append(client)

        self.full.release()

    def takeOrder(self):
        with self.lockAux:
            if self.totalOrdered < self.numberOfClients:
                self.full.acquire()

                with self.lock:
                    if len(self.arrDrink) == 1:
                        clientServed = self.arrDrink.popleft()

                    else:
                        clientServed = self.arrNoDrink.popleft()

                    self.empty.release()
                    self.totalOrdered = self.totalOrdered + 1
                    return clientServed
            else:
                return None

####################################################################################################################################


parameters = {"numberOfClients": 3, "numberOfWaiters": 2,
              "waiterCapacity": 2, "numberOfRounds": 4}

print(str(parameters.get("numberOfWaiters")), "garcons distribuem", str(parameters.get("numberOfRounds")),
      "rodadas para", str(parameters.get("numberOfClients")), "clientes, pegando", str(parameters.get("waiterCapacity")), "pedidos por vez", "\n")

if parameters.get("numberOfClients") > 0:
    saloon = Saloon(parameters.get("numberOfClients"),
                    parameters.get("numberOfRounds"))

    waiterList = []
    for i in range(parameters.get("numberOfWaiters")):
        waiterList.append(Waiter(parameters.get("waiterCapacity"), i, saloon))

    clientList = []
    for i in range(parameters.get("numberOfClients")):
        clientList.append(Client(i, saloon))

    [i.start() for i in waiterList], [i.start() for i in clientList], [i.join()
                                                                       for i in clientList], [i.join() for i in clientList]

print("\nFim do rodizio")
