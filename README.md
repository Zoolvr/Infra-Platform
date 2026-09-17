# Infra-Platform — Internal Developer Platform sur AWS



Plateforme Kubernetes end-to-end, entièrement pilotée en code : provisioning d'infrastructure, pipeline CI/CD, déploiement continu GitOps, gestion sécurisée des secrets et monitoring.



**Contexte**



Projet personnel réalisé pour combler des compétences concrètes en Infrastructure as Code, CI/CD et GitOps, dans le cadre d'une recherche de poste DevOps/Infrastructure junior en alternance. L'objectif : reproduire, à petite échelle, les pratiques utilisées en entreprise pour automatiser de bout en bout la création et l'exploitation d'une infrastructure.



Aucune action n'est faite manuellement sur les serveurs : tout part d'un `git push`.



**Architecture**



```

GitHub Repo

&#x20;  │

&#x20;  ├── Push sur terraform/ ──► GitHub Actions (lint, validate, plan)

&#x20;  │

&#x20;  ├── terraform apply ──► AWS (VPC, subnet, security group, EC2)

&#x20;  │                                   │

&#x20;  │                                   ▼

&#x20;  │                        Instance EC2 (k3s)

&#x20;  │                                   │

&#x20;  │                    ┌──────────────┼──────────────┐

&#x20;  │                    ▼              ▼              ▼

&#x20;  │                 ArgoCD      Prometheus/      Application

&#x20;  │              (GitOps)        Grafana          démo

&#x20;  │                    ▲

&#x20;  └── Push sur gitops/ ┘  (sync automatique)

```



\##Stack technique



| Brique | Outil | Rôle |

|---|---|---|

| Infrastructure as Code | \*\*Terraform\*\* | Provisioning du VPC, subnet, sécurité, instance EC2 sur AWS |

| Orchestration | \*\*k3s\*\* | Distribution Kubernetes légère, adaptée aux ressources limitées |

| CI/CD | \*\*GitHub Actions\*\* | Lint, validation et plan Terraform automatiques à chaque push |

| Déploiement continu | \*\*ArgoCD\*\* | GitOps — le repo Git est la source de vérité du cluster |

| Secrets | \*\*SOPS + age\*\* | Chiffrement des secrets avant commit, jamais de clé en clair sur GitHub |

| Observabilité | \*\*Prometheus + Grafana\*\* (kube-prometheus-stack) | Monitoring temps réel du cluster |

| Scripting | \*\*Python\*\* | Outil custom de vérification de l'état de la plateforme |



\## Structure du repo



```

Infra-Platform/

├── terraform/              # Code d'infrastructure AWS

│   └── main.tf

├── .github/workflows/       # Pipeline CI/CD

│   └── terraform.yml

├── gitops/                  # Manifests Kubernetes surveillés par ArgoCD

│   ├── deployment.yaml

│   └── secrets/

│       └── demo-secret.yaml  # Chiffré avec SOPS

├── scripts/                  # Outillage

│   └── healthcheck.py

├── docs/

├── .sops.yaml                # Configuration du chiffrement des secrets

├── .gitignore

└── README.md

```



\## Comment reproduire ce projet



\### Prérequis

\- Compte AWS avec un utilisateur IAM dédié (accès programmatique uniquement)

\- Terraform, AWS CLI, kubectl, Helm, SOPS + age installés en local



\### 1. Provisionner l'infrastructure

```bash

aws configure

cd terraform

terraform init

terraform apply

```

Crée le VPC, le subnet public, le security group, la paire de clés SSH et l'instance EC2 avec k3s installé automatiquement au démarrage (via `user\_data`).



\### 2. Configurer l'accès au cluster

Récupérer le kubeconfig généré sur l'instance (`/etc/rancher/k3s/k3s.yaml`), l'adapter avec l'IP publique de l'instance, et l'utiliser en local pour piloter le cluster à distance avec `kubectl` — sans jamais avoir besoin de SSH pour les opérations Kubernetes.



\### 3. Installer ArgoCD

```bash

kubectl create namespace argocd

kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

```

Créer ensuite une Application ArgoCD pointant vers le dossier `gitops/` de ce repo, en synchronisation automatique.



\### 4. Installer le monitoring

```bash

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

kubectl create namespace monitoring

helm install monitoring prometheus-community/kube-prometheus-stack --namespace monitoring

```



\### 5. Gérer les secrets

```bash

age-keygen -o keys.txt   # génère une paire de clés

sops -e -i gitops/secrets/mon-secret.yaml   # chiffre avant de commit

```



\## Preuves visuelles



\*(voir dossier `docs/` — captures d'écran)\*



\- Pipeline CI/CD GitHub Actions en succès (lint, validate, plan Terraform automatiques)

\- Application `demo-app` `Healthy`/`Synced` dans ArgoCD, avec l'arbre de ressources déployées

\- Auto-réparation GitOps : suppression manuelle des pods, recréation automatique en quelques secondes

\- Secret Kubernetes chiffré avec SOPS (illisible sans la clé privée)

\- Dashboard Grafana affichant l'utilisation CPU/mémoire du cluster en temps réel

\- Liste des ressources Terraform gérées (`terraform state list`)

\- Structure organisée du repo



\## Choix techniques et compromis



\- \*\*k3s plutôt qu'EKS\*\* : EKS facture le control plane (\~73 €/mois) même à l'arrêt des workloads. k3s auto-hébergé sur une simple instance EC2 reste quasi-gratuit sous Free Tier, tout en étant une vraie distribution Kubernetes conforme (CNCF certified).

\- \*\*SOPS + age plutôt que Vault\*\* : Vault nécessite un serveur dédié à faire tourner et administrer en plus du reste. SOPS chiffre directement les fichiers versionnés, sans infrastructure supplémentaire — plus adapté à un projet à cette échelle.

\- \*\*`terraform destroy` entre les sessions de travail\*\* : pour limiter les coûts, l'infrastructure n'est pas maintenue en permanence. Chaque session de travail commence par un `terraform apply` et se termine par un `terraform destroy`.



\## Limites connues (points d'amélioration identifiés)



\- Le security group autorise le SSH (port 22) depuis `0.0.0.0/0` — à restreindre à une IP spécifique en conditions réelles.

\- Le certificat TLS de l'API Kubernetes n'inclut pas l'IP publique dans ses SAN (`--tls-san` non configuré à l'installation de k3s), nécessitant `insecure-skip-tls-verify` côté client — à corriger pour un usage en production.

\- Le déchiffrement des secrets SOPS est manuel ; en production, un opérateur dédié (SOPS Operator, ou intégration ArgoCD/Vault) automatiserait le déchiffrement au moment du déploiement.

\- Instance unique (pas de haute disponibilité) — cohérent avec un objectif d'apprentissage, pas un environnement de production.



\## Ce que ce projet démontre



\- Infrastructure as Code de bout en bout (Terraform)

\- Automatisation CI/CD (GitHub Actions)

\- GitOps et déploiement continu (ArgoCD)

\- Gestion sécurisée des secrets (SOPS/age)

\- Observabilité (Prometheus/Grafana)

\- Scripting d'automatisation (Python)

\- Rigueur sur la maîtrise des coûts cloud (Free Tier, destroy systématique)

