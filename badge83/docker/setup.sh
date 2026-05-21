#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
CERT_DIR="$ROOT_DIR/docker/nginx/certs"

prompt() {
  question="$1"
  default_value="${2:-}"
  if [ -n "$default_value" ]; then
    printf "%s [%s]: " "$question" "$default_value" >&2
  else
    printf "%s: " "$question" >&2
  fi
  read -r answer
  if [ -n "$answer" ]; then
    printf "%s" "$answer"
  else
    printf "%s" "$default_value"
  fi
}

prompt_secret() {
  question="$1"
  printf "%s: " "$question" >&2
  stty -echo 2>/dev/null || true
  read -r answer
  stty echo 2>/dev/null || true
  printf "\n" >&2
  printf "%s" "$answer"
}

random_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    date +%s | sha256sum | awk '{print $1}'
  fi
}

write_env() {
  domain="$1"
  base_url="$2"
  username="$3"
  password="$4"
  auth_secret="$5"
  search_pepper="$6"

  cat > "$ENV_FILE" <<ENV
BADGE83_ENV=production
BADGE83_DOMAIN=$domain

BADGE83_HOST=0.0.0.0
BADGE83_PORT=8000
BADGE83_BASE_URL=$base_url
BADGE83_REGISTRY_DB=/app/data/registry.db

BADGE83_AUTH_USERNAME=$username
BADGE83_AUTH_PASSWORD=$password
BADGE83_AUTH_SECRET=$auth_secret
BADGE83_SEARCH_PEPPER=$search_pepper

BADGE83_MAX_PNG_UPLOAD_BYTES=52428800
BADGE83_MAX_CSV_UPLOAD_BYTES=10485760
BADGE83_MAX_IMAGE_PIXELS=50000000
ENV
}

make_self_signed_cert() {
  domain="$1"
  mkdir -p "$CERT_DIR"
  openssl req -x509 -nodes -newkey rsa:4096 -days 365 \
    -keyout "$CERT_DIR/privkey.pem" \
    -out "$CERT_DIR/fullchain.pem" \
    -subj "/CN=$domain" \
    >/dev/null 2>&1
}

obtain_letsencrypt_cert() {
  domain="$1"
  email="$2"
  mkdir -p "$CERT_DIR"
  docker run --rm \
    -p 80:80 \
    -v "$CERT_DIR:/etc/letsencrypt/live/$domain" \
    certbot/certbot certonly \
      --standalone \
      --non-interactive \
      --agree-tos \
      --email "$email" \
      -d "$domain"
}

main() {
  cd "$ROOT_DIR"

  if [ -e "$ENV_FILE" ]; then
    overwrite="$(prompt ".env already exists. Overwrite? yes/no" "no")"
    case "$overwrite" in
      yes|YES|y|Y) ;;
      *) echo "Setup cancelled."; exit 0 ;;
    esac
  fi

  domain="$(prompt "Public domain" "badge83.example.com")"
  base_url="$(prompt "Public base URL embedded into badges" "https://$domain")"
  username="$(prompt "Admin username" "admin83")"
  password="$(prompt_secret "Admin password (leave empty to generate)")"
  if [ -z "$password" ]; then
    password="$(random_secret)"
    echo "Generated admin password: $password"
  fi

  auth_secret="$(random_secret)"
  search_pepper="$(random_secret)"

  write_env "$domain" "$base_url" "$username" "$password" "$auth_secret" "$search_pepper"
  chmod 600 "$ENV_FILE"

  echo
  echo "Certificate options:"
  echo "  1) Use existing certs in docker/nginx/certs/fullchain.pem and privkey.pem"
  echo "  2) Generate self-signed cert for test/demo"
  echo "  3) Try Let's Encrypt standalone via certbot Docker image"
  cert_choice="$(prompt "Choose certificate option" "1")"

  case "$cert_choice" in
    2)
      make_self_signed_cert "$domain"
      echo "Self-signed certificate generated in $CERT_DIR"
      ;;
    3)
      email="$(prompt "Let's Encrypt contact email")"
      if [ -z "$email" ]; then
        echo "Email is required for Let's Encrypt." >&2
        exit 1
      fi
      obtain_letsencrypt_cert "$domain" "$email"
      echo "Let's Encrypt certificate command completed. Verify files in $CERT_DIR."
      ;;
    *)
      mkdir -p "$CERT_DIR"
      echo "Place certificates here:"
      echo "  $CERT_DIR/fullchain.pem"
      echo "  $CERT_DIR/privkey.pem"
      ;;
  esac

  echo
  echo "Setup complete. Start Badge83 with:"
  echo "  docker-compose -f docker-compose.prod.yml up -d --build"
}

main "$@"