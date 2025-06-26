#!/usr/bin/env python3

import subprocess
import time
import os
import sys
import shutil
from pathlib import Path

# === CONFIG ===
ACR_NAME = "orserviceaacr123456"
AKS_NAME = "orn-ha-cluster"
AKS_RG = "orn-ha-rg"
DOCKER_IMAGE = f"{ACR_NAME}.azurecr.io/service-a:latest"
HELM_NAMESPACE = "ingress-nginx"

# === PATH SETUP ===
ROOT_DIR = Path(__file__).resolve().parent
TERRAFORM_ACR_PATH = ROOT_DIR / "terraform/01-acr"
TERRAFORM_AKS_PATH = ROOT_DIR / "terraform/02-aks"
DOCKERFILE_PATH = ROOT_DIR / "service-A"
KUBERNETES_PATH = ROOT_DIR / "kubernetes"

def run(cmd, cwd=None, check=True):
    print(f"\n>>> Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=check)

def wait_for_ingress_controller(namespace="ingress-nginx", timeout_seconds=120):
    print(f"\nChecking if Ingress Controller is running in namespace '{namespace}'...")
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", namespace, "-l", "app.kubernetes.io/component=controller",
                 "-o", "jsonpath={.items[0].status.phase}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=True
            )
            status = result.stdout.strip()
            if status == "Running":
                print("Ingress Controller is running.")
                return True
            else:
                print(f"  Ingress controller pod status: {status} ... waiting")
        except subprocess.CalledProcessError:
            print("  Waiting for ingress controller pod to appear...")

        time.sleep(5)

    print("Timeout: Ingress controller did not become ready in time.")
    sys.exit(1)

def check_cluster_health():
    print("\n=== Cluster Health Check ===")

    # Check node status
    print("\nChecking node status...")
    try:
        run(["kubectl", "get", "nodes", "-o", "wide"])
    except subprocess.CalledProcessError:
        print("Failed to fetch node status.")

    # Check pod status
    print("\nChecking pod status across all namespaces...")
    try:
        run(["kubectl", "get", "pods", "--all-namespaces", "-o", "wide"])
    except subprocess.CalledProcessError:
        print("Failed to fetch pod status.")


def verify_network_policy_block():
    print("\nVerifying network isolation: Service-A → Service-B should be blocked...")

    try:
        cmd = [
            "kubectl", "run", "test-a", "--rm", "-i", "--tty",
            "--image=busybox",
            "--labels=app=service-a",
            "--restart=Never",
            "--", "/bin/sh", "-c",
            "wget --timeout=3 --spider http://service-b"
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Clean up common kube exec pod termination message if present
        stderr_clean = result.stderr.replace(
            "If you don't see a command prompt, try pressing enter.", "").strip()

        if result.returncode == 0:
            print("Service-A was able to reach Service-B! Network policy is NOT blocking traffic.")
        else:
            print("Service-A cannot access Service-B.")

    except subprocess.CalledProcessError as e:
        print("Network policy working: access was blocked or pod failed to start.")
    except Exception as e:
        print(f"Error verifying network policy: {e}")



def main():
    # 1. Check prerequisites and get full paths
    print("Checking prerequisites...")
    required_tools = ["az", "terraform", "docker", "kubectl", "helm"]
    tool_paths = {}
    for tool in required_tools:
        path = shutil.which(tool)
        if not path:
            print(f"Error: {tool} not found. Please install it and ensure it is in your PATH.")
            sys.exit(1)
        tool_paths[tool] = path
        print(f"Found {tool}: {path}")

    AZ = tool_paths["az"]
    TERRAFORM = tool_paths["terraform"]
    DOCKER = tool_paths["docker"]
    KUBECTL = tool_paths["kubectl"]
    HELM = tool_paths["helm"]
     
    # 2. Azure login
    print("\nLogging into Azure...")
    try:
        subprocess.run([AZ, "account", "show"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        run([AZ, "login"])

    print(f"ROOT_DIR = {ROOT_DIR}")

    # 3. ACR Terraform
    print("\nDeploying ACR with Terraform...")
    run([TERRAFORM, "init", "-input=false"], cwd=TERRAFORM_ACR_PATH)
    run([TERRAFORM, "apply", "-auto-approve"], cwd=TERRAFORM_ACR_PATH)

    # 4. AKS Terraform
    print("\nDeploying AKS with Terraform...")
    run([TERRAFORM, "init", "-input=false"], cwd=TERRAFORM_AKS_PATH)
    run([TERRAFORM, "apply", "-auto-approve"], cwd=TERRAFORM_AKS_PATH)

    # 5. Attach ACR to AKS
    print("\nAttaching ACR to AKS...")
    run([AZ, "aks", "update", "-n", AKS_NAME, "-g", AKS_RG, "--attach-acr", ACR_NAME])

    # 6. Build and push Docker image
    print("\nBuilding and pushing Docker image...")
    run([DOCKER, "build", "-t", DOCKER_IMAGE, "."], cwd=DOCKERFILE_PATH)
    run([AZ, "acr", "login", "--name", ACR_NAME])
    run([DOCKER, "push", DOCKER_IMAGE])

    # 7. Get AKS credentials
    print("\nSetting kubectl context...")
    run([AZ, "aks", "get-credentials", "--resource-group", AKS_RG,
         "--name", AKS_NAME, "--overwrite-existing"])

    # 8. Install ingress controller
    print("\nInstalling ingress controller...")
    run([HELM, "repo", "add", "ingress-nginx", "https://kubernetes.github.io/ingress-nginx"])
    run([HELM, "repo", "update"])
    run([KUBECTL, "create", "namespace", HELM_NAMESPACE], check=False)
    run([HELM, "upgrade", "--install", "ingress-nginx", "ingress-nginx/ingress-nginx",
         "--namespace", HELM_NAMESPACE])

    # 9. Apply Kubernetes manifests
    print("\nApplying Kubernetes manifests...")
    run([KUBECTL, "apply", "-f", "base/access/service-b-access.yaml"], cwd=KUBERNETES_PATH)
    run([KUBECTL, "apply", "-f", "services/service-b/deployment.yaml"], cwd=KUBERNETES_PATH)
    run([KUBECTL, "apply", "-f", "services/service-b/service.yaml"], cwd=KUBERNETES_PATH)

    run([KUBECTL, "apply", "-f", "base/access/service-a-access.yaml"], cwd=KUBERNETES_PATH)
    run([KUBECTL, "apply", "-f", "services/service-a/deployment.yaml"], cwd=KUBERNETES_PATH)
    run([KUBECTL, "apply", "-f", "services/service-a/service.yaml"], cwd=KUBERNETES_PATH)

    run([KUBECTL, "apply", "-f", "base/networkpolicy/block-service-a-to-b.yaml"], cwd=KUBERNETES_PATH)
    
    wait_for_ingress_controller()
    run([KUBECTL, "apply", "-f", "base/ingress/ingress.yaml"], cwd=KUBERNETES_PATH)

    print("\nAll resources deployed successfully.")
    
    # 10. Check pods and node status
    check_cluster_health()
     
    # 11. Check service-A to B connectivity
    verify_network_policy_block()

if __name__ == "__main__":
    main()
