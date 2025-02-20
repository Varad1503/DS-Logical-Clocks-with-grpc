import argparse
import json
import multiprocessing
from time import sleep
from concurrent import futures
import grpc
import Relay_pb2_grpc
from Branch import Branch
from Customer import Customer

def Start_Process(process,Branch_Processes,Customer_Processes):
    branches = []
    customers = []
    branchIDs = []
    for p in process:
        if p["type"] == "branch":
            branchIDs.append(p["id"])
    for p in process:
        if p["type"] == "branch":
            branch = Branch(p["id"],p["balance"],branchIDs)
            branches.append(branch)
    print("Starting Branch Processes\n")
    for branch in branches:
        branch_process = multiprocessing.Process(target=run_branch, args=(branch,))
        Branch_Processes.append(branch_process)
        branch_process.start()
    sleep(1)
    for p in process:
        if p["type"] == "customer":
            customer = Customer(p["id"], p["customer-requests"])
            customers.append(customer)
    print("\nStarting Customer Processes\n")
    for customer in customers:
        customer_process = multiprocessing.Process(target=run_customer, args=(customer,))
        Customer_Processes.append(customer_process)
        customer_process.start()
    for customerProcess in Customer_Processes:
        customerProcess.join()
    sleep(1)
def run_customer(customer):
    customer.createStub()
    customer.executeEvents()
    sleep(1.5 * customer.id)
    output_customer_events = json.load(open("customer_output.json"))
    output_customer_events.append({"id": customer.id, "type": "customer", "events": customer.output()})
    output_customer = json.dumps(output_customer_events, indent=4)
    output_file2 = open("customer_output.json", "w")
    output_file2.write(output_customer)
    output_file2.close()
    only_events_customer = json.load(open("events_output.json"))
    only_events_customer.extend(customer.output_only_events())
    only_events = json.dumps(only_events_customer, indent=4)
    output_file3 = open("events_output.json", "w")
    output_file3.write(only_events)
    output_file3.close()
def run_branch(branch):
    branch.createStubs()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    Relay_pb2_grpc.add_relayServicer_to_server(branch, server)
    port = 50000 + branch.id
    print("Server started. Listening on port : " + str(port))
    server.add_insecure_port("localhost:" + str(port))
    server.start()
    sleep(1.5 * branch.id)
    output_branch_events = json.load(open("branch_output.json"))
    output_branch_events.append({"id": branch.id,"type": "branch", "events": branch.output()})
    output_branch = json.dumps(output_branch_events, indent=4)
    output_file = open("branch_output.json", "w")
    output_file.write(output_branch)
    output_file.close()
    only_events_branch = json.load(open("events_output.json"))
    only_events_branch.extend(branch.output_only_events())
    only_events = json.dumps(only_events_branch, indent=4)
    output_file3 = open("events_output.json", "w")
    output_file3.write(only_events)
    output_file3.close()
    server.wait_for_termination()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    args = parser.parse_args()
    try:
        print("\nNOTE: Wait till all processes are terminated.\n")
        input = json.load(open(args.input_file))
        output_file = open("branch_output.json", "w")
        output_file.write("[]")
        output_file.close()
        output_file2 = open("customer_output.json", "w")
        output_file2.write("[]")
        output_file2.close()
        output_file3 = open("events_output.json","w")
        output_file3.write("[]")
        output_file3.close()
        Branch_Processes = []
        Customer_Processes = []
        Start_Process(input,Branch_Processes,Customer_Processes)
        print("Output File customer_output.son has been created inside the folder")
        print("Output File branch_output.son has been created inside the folder")
        print("Output File events_output.son has been created inside the folder")
        print("\nTerminating Processes")
        sleep(1)
        for p in Customer_Processes:
            p.terminate()
        for p in Branch_Processes:
            p.terminate()
    except FileNotFoundError:
        print("Could not find input file '" + args.input_file)
    except json.decoder.JSONDecodeError:
        print("Error decoding JSON file")  