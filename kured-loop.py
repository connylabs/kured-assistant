#!/usr/bin/env python3
import json
import signal
import subprocess
from time import sleep
from types import FrameType


def get_leader_pods(node_name: str, namespace: str = "") -> list[dict[str, str]]:
    command = [
        "kubectl",
        "get",
        "pod",
        "-l",
        "spilo-role=master",
        "-lapplication=spilo",
        "--field-selector",
        f"spec.nodeName={node_name}",
        "-ojson",
    ]
    if namespace:
        command += ["-n", namespace]
    else:
        command += ["-A"]
    print(command)

    process = subprocess.run(command, stdout=subprocess.PIPE, universal_newlines=True)

    pods = json.loads(process.stdout)["items"]
    return [
        {"namespace": x["metadata"]["namespace"], "name": x["metadata"]["name"]}
        for x in pods
    ]


def switch(node_name: str, namespace: str = "") -> None:
    pods = get_leader_pods(node_name, namespace)
    pre_command = ["kubectl", "exec", "-c", "postgres"]
    patronicmd = ["patronictl", "switchover", "--force"]
    for pod in pods:
        cluster_name = "-".join(pod["name"].split("-")[0:-1])
        cmd = (
            pre_command
            + ["-n", pod["namespace"], pod["name"], "--"]
            + patronicmd
            + [cluster_name]
        )
        print(cmd)
        print(f"Executing switch over for {pod['name']} in {pod['namespace']}")
        process = subprocess.run(cmd, stdout=subprocess.PIPE, universal_newlines=True)
        print(process.stdout)


def get_nodes_rebooting() -> list[str]:
    command = [
        "kubectl",
        "get",
        "node",
        "-l",
        " weave.works/kured-draining=yes",
        "-o",
        "jsonpath-as-json={.items[*]['metadata.name']}",
    ]
    process = subprocess.run(command, stdout=subprocess.PIPE, universal_newlines=True)
    nodes: list[str] = json.loads(process.stdout)
    return nodes


class Looper:
    kill_now = False

    def __init__(self) -> None:
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signal: int, frame: FrameType | None) -> None:
        self.kill_now = True

    def start(self, wait_in_seconds: int = 30) -> None:
        print("start switchover control loop")
        while not self.kill_now:
            nodes = get_nodes_rebooting()
            if len(nodes) == 1:
                print(nodes)
                switch(node_name=nodes[0])

            elif len(nodes) > 1:
                raise ValueError(f"unexpected number of nodes {nodes}")
            sleep(wait_in_seconds)


def main() -> None:
    looper = Looper()
    looper.start()


if __name__ == "__main__":
    main()
