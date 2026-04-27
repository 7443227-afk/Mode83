# Plan de sécurité pour le développement et la publication du projet Mode83

Date : 2026-04-27  
Serveur : `nvs-ampere-p`  
Objectif : continuer le développement du projet en toute sécurité, en n’exposant publiquement que les points d’entrée nécessaires et en réduisant les risques d’attaque sur les services.

---

## 1. Résumé de l’état actuel

D’après les premières vérifications :

- Le port SSH `22/tcp` est ouvert et accessible depuis l’extérieur.
- Les journaux `sshd` montrent de nombreuses tentatives de connexion et d’énumération d’utilisateurs : `root`, `admin`, `user`, `test`, `solv`, etc.
- Les connexions réussies visibles dans les journaux ont été faites par clé publique pour l’utilisateur `ubuntu`.
- L’authentification SSH par mot de passe est désactivée dans la configuration :
  - `/etc/ssh/sshd_config.d/60-cloudimg-settings.conf` : `PasswordAuthentication no`
  - `/etc/ssh/sshd_config` : `KbdInteractiveAuthentication no`
- Un fichier `/home/ubuntu/security2504.md` existe et décrit une politique de sécurité : conserver SSH, ICMP et loopback, puis rejeter les autres ports entrants.

Risque principal : dès que les ports `80`, `443`, `8000`, `8080`, `5000` ou d’autres ports applicatifs sont exposés, ils peuvent recevoir du scan, du brute-force, des attaques HTTP, des tentatives d’exploitation de vulnérabilités connues et du trafic malveillant automatisé.

---

## 2. Principe principal

Ne pas exposer directement les ports applicatifs sur Internet.

Schéma recommandé :

```text
Internet
   |
   | 80/tcp, 443/tcp
   v
Reverse proxy Nginx ou Caddy
   |
   | localhost / réseau interne
   v
Application Mode83 / validateur / code-server / services de développement
```

Les seuls ports publics nécessaires devraient être :

- `22/tcp` — SSH, idéalement limité à des adresses IP de confiance.
- `80/tcp` — redirection HTTP vers HTTPS et challenge Let’s Encrypt.
- `443/tcp` — point d’entrée HTTPS principal.

Tous les autres services doivent écouter uniquement sur :

- `127.0.0.1`, ou
- un réseau Docker/interne, ou
- une interface VPN.

---

## 3. Modèle recommandé pour les ports

### Ports publics

| Port | Usage | Accès |
| --- | --- | --- |
| `22/tcp` | SSH | De préférence uniquement IP de confiance |
| `80/tcp` | Redirection HTTP / Let’s Encrypt | Public |
| `443/tcp` | Reverse proxy HTTPS | Public |

### Ports non publics

| Port | Usage | Mode d’écoute recommandé |
| --- | --- | --- |
| `8000/tcp` | Backend / application / API | `127.0.0.1:8000` |
| `8080/tcp` | code-server / outils de développement | `127.0.0.1:8080` ou VPN uniquement |
| `5000/tcp` | validateur / service de test | `127.0.0.1:5000` |
| autres ports dev | services temporaires | localhost uniquement |

---

## 4. Politique firewall

Politique de base :

```text
ALLOW established,related
ALLOW loopback
ALLOW SSH depuis les IP de confiance
ALLOW 80/tcp
ALLOW 443/tcp
DROP/REJECT tout autre trafic entrant
```

Important : ne pas ajouter de règles publiques autorisant `8000`, `8080` ou `5000` si ces services ne sont pas destinés à être accessibles directement depuis Internet.

### Commandes de vérification

À exécuter avec les droits root/sudo :

```bash
sudo iptables -S
sudo iptables -L INPUT -n -v --line-numbers
sudo nft list ruleset
ss -ltnp
```

Vérifier quels services écoutent sur les ports sensibles :

```bash
ss -ltnp | grep -E ':(22|80|443|8000|8080|5000)\b'
```

Si un service affiche `0.0.0.0:8000` ou `[::]:8000`, il écoute sur toutes les interfaces et peut être exposé. Pour les services backend/dev, ce n’est pas souhaitable.

---

## 5. Durcissement SSH

Bonne pratique déjà en place : l’authentification par mot de passe est désactivée.

À vérifier et renforcer :

```text
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
X11Forwarding no
AllowUsers ubuntu
```

Vérifier la configuration effective :

```bash
sudo sshd -T | grep -Ei 'passwordauthentication|kbdinteractiveauthentication|permitrootlogin|pubkeyauthentication|allowusers'
```

Si une adresse IP fixe de confiance est disponible, limiter SSH à cette IP :

```bash
sudo iptables -I INPUT -p tcp -s TRUSTED_IP --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j DROP
```

Remplacer `TRUSTED_IP` par l’adresse réelle.

---

## 6. Reverse proxy

Pour publier le projet, utiliser Nginx ou Caddy.

Schéma recommandé :

```text
https://domain.example/         -> 127.0.0.1:8000
https://domain.example/verify   -> 127.0.0.1:8000/verify
https://admin.domain.example/   -> protégé par Basic Auth / IP allowlist / VPN
```

Exemple de configuration Nginx :

```nginx
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 7. Limitation de débit HTTP

Les API publiques et formulaires doivent avoir du rate limiting.

Exemple Nginx :

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=strict:10m rate=5r/m;

server {
    listen 443 ssl http2;
    server_name example.com;

    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
    }

    location /login {
        limit_req zone=strict burst=5 nodelay;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

---

## 8. Protection des accès admin/dev

`code-server`, les interfaces d’administration, les endpoints de debug et les services de test ne doivent pas être accessibles directement depuis Internet.

Options recommandées :

### Option A — Tunnel SSH

Recommandé pour le développement.

```bash
ssh -L 8080:127.0.0.1:8080 ubuntu@SERVER_IP
```

Puis ouvrir localement :

```text
http://127.0.0.1:8080
```

### Option B — VPN

Solutions possibles :

- WireGuard
- Tailscale
- ZeroTier

Avantage : les ports dev ne sont pas exposés publiquement.

### Option C — Nginx Basic Auth + liste blanche IP

Acceptable, mais moins robuste qu’un tunnel SSH ou un VPN.

---

## 9. Fail2ban / CrowdSec

Niveau minimal :

- `fail2ban` pour SSH ;
- `fail2ban` pour les échecs d’authentification Nginx Basic Auth ;
- règles supplémentaires pour les scans HTTP, si nécessaire.

Option plus avancée :

- `CrowdSec` ;
- firewall bouncer ;
- scénarios pour `sshd` et `nginx`.

Recommandation :

- commencer avec `fail2ban` ;
- envisager ensuite `CrowdSec` pour une protection plus complète.

Vérification :

```bash
sudo fail2ban-client status
sudo fail2ban-client status sshd
```

---

## 10. TLS et en-têtes de sécurité

Pour HTTPS, activer :

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

Pour l’API publique :

- limiter les méthodes HTTP à `GET`, `POST`, `HEAD` ;
- limiter la taille du body ;
- valider les données entrantes ;
- ne jamais exposer les stack traces ;
- désactiver le mode debug en production.

---

## 11. Sécurité applicative

Pour Mode83/API :

- ne pas lancer un serveur Flask/FastAPI dev sur `0.0.0.0` sans reverse proxy ;
- ne pas activer le debug mode en production ;
- valider toutes les entrées côté serveur ;
- journaliser les erreurs sans exposer de secrets ;
- conserver les fichiers `.env` hors du web root ;
- ne pas committer de secrets dans Git ;
- sauvegarder régulièrement la base et les badges émis ;
- utiliser un utilisateur systemd dédié au service.

---

## 12. Service systemd pour l’application

Il est recommandé de lancer l’application via systemd et de l’attacher à localhost.

Exemple :

```ini
[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/projects/Mode83/badge83
EnvironmentFile=/home/ubuntu/projects/Mode83/badge83/badge83.env
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
```

Vérification :

```bash
systemctl status mode83
ss -ltnp | grep 8000
```

Résultat attendu :

```text
127.0.0.1:8000
```

Résultat à éviter :

```text
0.0.0.0:8000
```

---

## 13. Scénarios opérationnels

### Ouvrir le site public en sécurité

1. Lancer le backend sur `127.0.0.1:8000`.
2. Configurer Nginx vers `443 -> 127.0.0.1:8000`.
3. Ouvrir uniquement `80` et `443` dans le firewall.
4. Vérifier `ss -ltnp`.
5. Vérifier les logs Nginx.

### Accès temporaire au développement

Préférer un tunnel SSH plutôt que l’ouverture d’un port :

```bash
ssh -L 8080:127.0.0.1:8080 ubuntu@SERVER_IP
```

Si un port doit être temporairement ouvert :

1. Le limiter par IP.
2. Fixer une date/heure de fermeture.
3. Documenter le changement dans un journal de sécurité.
4. Supprimer la règle après utilisation.

### Fermer rapidement les ports web publics

Exemple :

```bash
sudo iptables -D INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -D INPUT -p tcp --dport 443 -j ACCEPT
```

Les commandes exactes dépendent de l’ordre des règles. Avant toute suppression :

```bash
sudo iptables -L INPUT -n --line-numbers
```

---

## 14. Checklist avant d’ouvrir un nouveau service

- [ ] Le service écoute uniquement sur `127.0.0.1` ou sur un réseau privé.
- [ ] Seul le reverse proxy est exposé publiquement.
- [ ] HTTPS est activé.
- [ ] Le rate limiting est activé.
- [ ] Le mode debug est désactivé.
- [ ] Les secrets ne sont pas dans Git.
- [ ] Les données importantes sont sauvegardées.
- [ ] Les logs sont écrits et exploitables.
- [ ] Le firewall a été vérifié avec `sudo iptables -S` ou `sudo nft list ruleset`.
- [ ] L’authentification SSH par mot de passe est désactivée.
- [ ] Fail2ban/CrowdSec est activé ou planifié.

---

## 15. Feuille de route recommandée

### Étape 1 — Consolider la protection actuelle

1. Vérifier les règles firewall avec sudo.
2. Vérifier que `PermitRootLogin no` est effectif.
3. Installer et activer fail2ban pour SSH.
4. Documenter l’état réel des ports.

### Étape 2 — Préparer la publication production

1. Configurer le backend sur `127.0.0.1:8000`.
2. Configurer Nginx ou Caddy.
3. Obtenir un certificat TLS.
4. Ouvrir uniquement `80` et `443`.
5. Ajouter rate limits et en-têtes de sécurité.

### Étape 3 — Développement sécurisé

1. Garder code-server sur localhost.
2. Utiliser un tunnel SSH ou un VPN.
3. Ne pas exposer `8080` publiquement.
4. Documenter chaque ouverture temporaire de port.

### Étape 4 — Surveillance

1. Lire régulièrement les logs SSH et Nginx.
2. Vérifier les bannissements fail2ban.
3. Vérifier les ports ouverts une fois par semaine.
4. Mettre à jour ce document ou un journal de sécurité après chaque modification firewall.

---

## 16. Configuration cible minimale pour Mode83

```text
Internet public :
  22/tcp   SSH, idéalement IP de confiance uniquement
  80/tcp   Redirection HTTP / Let’s Encrypt
  443/tcp  HTTPS Nginx/Caddy

Localhost / interne uniquement :
  8000/tcp Backend Mode83
  8080/tcp code-server
  5000/tcp validateur / services de test
```

Conclusion : le projet peut être développé et publié via HTTPS sans exposer directement les ports backend ou développement sur Internet.
