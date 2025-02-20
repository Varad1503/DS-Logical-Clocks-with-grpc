from time import sleep
import grpc
import Relay_pb2_grpc
from Relay_pb2 import Msg_request

class Customer:
    def __init__(self,id,events):
        self.id = id
        self.events = events
        self.recvMsg = list()
        self.stub = None
        self.clock = 1
        self.only_events = list()
    
    def createStub(self):
        port = 50000 + self.id
        port = str(port)
        channel = grpc.insecure_channel("localhost:" + port)
        self.stub = Relay_pb2_grpc.relayStub(channel)
    
    def executeEvents(self):
        for event in self.events:
            response = self.stub.Deliver(Msg_request(id=event["customer-request-id"], interface=event["interface"], money=event["money"], clock=self.clock))
            self.recvMsg.append({"customer-request-id" : response.id,"interface" : response.interface, "logical_clock" : self.clock ,"comment" : "Event_sent from customer " + str(self.id)})
            self.only_events.append({"id" : self.id,"type" : "customer","customer-request-id" : response.id,"interface" : response.interface, "logical_clock" : self.clock ,"comment" : "Event_sent from customer " + str(self.id)})
            self.clock += 1
    def output(self):
        #print("Writing Output in JSON FILES")
        return self.recvMsg
    def output_only_events(self):
        #print("Writing Output in JSON FILES")
        return self.only_events