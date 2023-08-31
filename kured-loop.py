#!/usr/bin/env python3
import json
from time import sleep
import argparse
import subprocess
import signal

def get_leader_pods(node_name: str, namespace: str = '') -> list[dict[str, str]]:
    command = ["kubectl", "get", "pod",
               "-l", "spilo-role=master", "-lapplication=spilo",
               "--field-selector",
               f"spec.nodeName={node_name}", "-ojson"]
    if namespace:
         command += ["-n", namespace]
    else:
        command += ["-A"]
    print(command)

    process = subprocess.run(command,
                             stdout=subprocess.PIPE,
                             universal_newlines=True)

    pods = json.loads(process.stdout)["items"]
    return [{"namespace": x["metadata"]["namespace"], "name": x["metadata"]["name"]} for x in pods]


def switch(node_name: str, namespace: str = ''):
    pods = get_leader_pods(node_name, namespace)
    pre_command = ["kubectl", "exec", "-c", "postgres"]
    patronicmd = ["patronictl", "switchover", "--force"]
    for pod in pods:
        cluster_name = "-".join(pod["name"].split("-")[0:-1])
        cmd = pre_command + ["-n", pod["namespace"], pod["name"], "--"] + patronicmd + [cluster_name]
        print(cmd)
        print(f"Executing switch over for {pod['name']} in {pod['namespace']}")
        process = subprocess.run(cmd,
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
        print(process.stdout)

def get_nodes_rebooting():
    command = ["kubectl", "get", "node",
               "-l", " weave.works/kured-draining=yes",
               "-o", "jsonpath-as-json={.items[*]['metadata.name']}"]
    process = subprocess.run(command,
                             stdout=subprocess.PIPE,
                             universal_newlines=True)
    nodes = json.loads(process.stdout)

    return nodes

class Looper:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, *args):
    self.kill_now = True

  def start(self, wait_in_seconds=30):
      print("start switchover control loop")
      while not self.kill_now:
          nodes = get_nodes_rebooting()
          if len(nodes) == 1:
              print(nodes)
              switch(node_name=nodes[0])

          elif len(nodes) > 1:
              raise ValueError(f"unexpected number of nodes {nodes}")
          sleep(wait_in_seconds)

def main():
    looper = Looper()
    looper.start()

if __name__ == "__main__":
    main()
