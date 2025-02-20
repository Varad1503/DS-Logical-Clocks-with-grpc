from concurrent import futures
from time import sleep
import Relay_pb2_grpc
import Relay_pb2
from Relay_pb2 import branch_comm
from Relay_pb2 import Msg_response
from Relay_pb2 import branch_res
import grpc

class Branch(Relay_pb2_grpc.relayServicer):
    def __init__(self,id,balance,branches):
        self.id = id
        self.balance = balance
        self.branches = branches
        self.clock = 1
        self.stubList = list()
        self.events = list()
        self.branchid = list()
        self.only_events = list()
    def createStubs(self):
        for branch in self.branches:
            if branch != self.id:
                port = 50000 + branch
                port = str(port)
                channel = grpc.insecure_channel("localhost:"+port)
                stub = Relay_pb2_grpc.relayStub(channel)
                self.stubList.append(stub)
                self.branchid.append(branch)

    def Deliver(self, request, context):
        if request != "query":
            response = self.Update(request)
            self.Branch_message_Handler(response, 1)
        else: 
           response = self.Query(request)
        return response
    
    def Cast(self, request, context):
        if request.interface != "query":
            self.Recv_from_Branch(request)
            if request.interface == "withdraw":
                self.Withdraw(request)
            elif request.interface == "deposit":
                self.Deposit(request)
            response = branch_res(id=request.id, interface=request.interface, money= request.money, clock= request.clock, branch = self.id)
        return response
    
    def Branch_message_Handler(self, request, _propogate):
        result = "success"
        response = Msg_response(id=request.id, interface=request.interface, result=result, money=self.balance, clock=self.clock)
        if _propogate == 1 : 
            if request.interface == "withdraw":
                self.Propagate_Withdraw(request)
                return response
            elif request.interface == "deposit":
                self.Propagate_Deposit(request)
                return response
        else:
            return response
        
    def Query(self,request):
        result = "Success"
        self.clock = max(self.clock,request)+1
        response = Msg_response(id=request.id, interface=request.interface, result=result, money=self.balance, clock=self.clock)
        return response

    def Withdraw(self,request):
        self.clock = max(self.clock, request.clock) + 1
        self.balance -= request.money
    
    def Deposit(self,request):
        self.clock = max(self.clock,request.clock) + 1
        self.balance += request.money

    def Propagate_Deposit(self, request):
        for stub in self.stubList:
            response = stub.Cast(
                branch_comm(id=request.id, interface=request.interface, money=request.money, clock=self.clock, branch = self.id)
            )
            self.Sent_to_Branch(response)

    def Propagate_Withdraw(self, request):
        for stub in self.stubList:
            response = stub.Cast(
                branch_comm(id=request.id, interface=request.interface, money=request.money, clock=self.clock, branch = self.id)
            )
            self.Sent_to_Branch(response)

    def Update(self, request):
        if request.interface == "withdraw":
            self.Withdraw(request)
            result = "Success"
        elif request.interface == "deposit":
            self.Deposit(request)
            result = "Success"
        self.clock = max(self.clock, request.clock) + 1
        self.events.append({"customer-request-id": request.id,"logical_clock": self.clock, "interface": request.interface, "comment" : "event_recv from customer " + str(self.id)})
        self.only_events.append({"id": self.id ,"type": "branch","customer-request-id": request.id,"logical_clock": self.clock, "interface": request.interface, "comment" : "event_recv from customer " + str(self.id)})
        response = branch_res(id = request.id, interface = request.interface , money = request.money, clock = self.clock, branch = self.id )
        return response

    def Sent_to_Branch(self, request):
        self.clock = max(self.clock,request.clock)+1
        self.events.append({"customer-request-id": request.id,"logical_clock": self.clock, "interface": request.interface + "_propagate", "comment" : "event_sent to branch " + str(request.branch)})
        self.only_events.append({"id": self.id ,"type": "branch","customer-request-id": request.id,"logical_clock": self.clock, "interface": request.interface + "_propagate", "comment" : "event_sent to branch " + str(request.branch)})

    def Recv_from_Branch(self, response):
        self.clock = max(self.clock, response.clock) + 1
        self.events.append({"customer-request-id": response.id,"logical_clock": self.clock, "interface": response.interface + "_propagate", "comment" : "event_recv from branch " + str(response.branch)})
        self.only_events.append({"id": self.id ,"type": "branch","customer-request-id": response.id,"logical_clock": self.clock, "interface": response.interface + "_propagate", "comment" : "event_recv from branch " + str(response.branch)})
   
    def output(self):
        return self.events
    
    def output_only_events(self):
        return self.only_events