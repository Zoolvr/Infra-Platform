import subprocess
import sys

def run_kubectl(args):
    """Exécute une commande kubectl et retourne la sortie."""
    cmd = ["kubectl"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()

def check_nodes():
    print("=== Noeuds du cluster ===")
    output = run_kubectl(["get", "nodes"])
    print(output)
    print()

def check_pods():
    print("=== Pods (tous namespaces) ===")
    output = run_kubectl(["get", "pods", "-A"])
    print(output)
    print()

def check_argocd_apps():
    print("=== Applications ArgoCD ===")
    output = run_kubectl(["get", "applications", "-n", "argocd"])
    print(output)
    print()

if __name__ == "__main__":
    print("Vérification de l'état de la plateforme\n")
    check_nodes()
    check_pods()
    check_argocd_apps()