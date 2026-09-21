# Infra-Platform

Plateforme Kubernetes sur AWS, montée entièrement en code. Voici
comment je l'ai construite, dans l'ordre.

## Pourquoi

Je connaissais Terraform et le CI/CD en théorie, jamais en pratique.
J'ai monté ce projet pour changer ça, avec un vrai use case du début à
la fin plutôt qu'un tuto isolé.

## Le réseau AWS

J'ai commencé par le réseau, parce que rien ne peut exister sans lui.
Avec Terraform :
- un VPC (le réseau privé)
- un subnet public dedans
- une internet gateway pour sortir sur le net
- une table de routage pour relier les deux

Tout ça écrit dans `main.tf`, jamais cliqué dans la console AWS.

## Le pare-feu et la connexion

Ensuite, un security group qui n'ouvre que deux ports : 22 (SSH) et
6443 (l'API Kubernetes). Et une paire de clés SSH générée en local,
dont seule la clé publique part sur AWS.

## La machine et Kubernetes

Une instance EC2, avec un script qui s'exécute tout seul au premier
démarrage pour installer k3s (une version légère de Kubernetes). Je
n'ai jamais eu besoin de me connecter pour taper la commande
d'installation moi-même.

## Le pipeline

Une fois l'infra qui marchait à la main, j'ai automatisé sa
vérification. Un fichier GitHub Actions qui, à chaque push sur le
dossier `terraform/`, vérifie le format du code, sa syntaxe, et
affiche ce qui va changer avant que quoi que ce soit ne soit appliqué.
L'apply reste manuel, volontairement — je ne voulais pas qu'une erreur
modifie l'infra toute seule.

## Piloter à distance

Au début je me connectais en SSH pour tout faire sur le cluster, ce
qui n'avait pas de sens pour un projet censé tout automatiser. J'ai
récupéré le fichier de connexion généré par k3s, changé l'adresse
dedans, et depuis j'utilise `kubectl` en local. Le SSH ne sert plus
qu'à ouvrir un accès temporaire aux interfaces web.

## ArgoCD

Installé dans le cluster, il surveille un dossier du repo (`gitops/`)
et redéploie automatiquement tout ce qui y change. Testé en supprimant
des pods à la main : recréés en quelques secondes, sans que je fasse
rien.

## Les secrets

Chiffrés avec SOPS avant d'être commités. Une clé publique sert à
chiffrer, une clé privée (gardée en local, jamais sur GitHub) sert à
déchiffrer. Le fichier reste lisible dans sa structure, seules les
valeurs deviennent illisibles.

## Le monitoring

Prometheus et Grafana installés avec Helm en une commande. Accès via
le même principe de tunnel SSH que pour ArgoCD, pour voir l'usage
CPU/RAM du cluster en direct.

## Le script Python

Un petit outil qui regroupe plusieurs commandes `kubectl` en une
seule, pour vérifier l'état de la plateforme sans avoir à taper trois
commandes différentes à chaque fois.

## Ce que je garderais différent en vrai

- Le SSH est ouvert à tout le monde (`0.0.0.0/0`), à restreindre en usage réel
- Le certificat de l'API Kubernetes ne connaît pas l'IP publique, d'où
un `insecure-skip-tls-verify` que je devrais corriger proprement
- Le déchiffrement des secrets est manuel, un opérateur dédié le
ferait automatiquement en prod
- Une seule instance, pas de haute dispo — suffisant pour apprendre,
pas pour tenir en prod

## Structure du repo

```
terraform/          code d'infra AWS
.github/workflows/   pipeline CI
gitops/               ce qu'ArgoCD déploie
scripts/              outillage Python
docs/                  captures d'écran
```

## Pour reproduire

```bash
aws configure
cd terraform
terraform init
terraform apply
```

Récupérer le kubeconfig sur l'instance (`/etc/rancher/k3s/k3s.yaml`),
changer l'IP dedans, puis piloter en local avec `kubectl`.

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f
https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

```bash
helm repo add prometheus-community
https://prometheus-community.github.io/helm-charts
kubectl create namespace monitoring
helm install monitoring prometheus-community/kube-prometheus-stack
--namespace monitoring
```

```bash
sops -e -i gitops/secrets/mon-secret.yaml
```

## En images
