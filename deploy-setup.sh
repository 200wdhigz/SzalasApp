#!/bin/bash
# Skrypt pomocniczy do wdrożenia SzalasApp na serwerze produkcyjnym
# Użycie: ./deploy-setup.sh

set -e

echo "==================================="
echo "  SzalasApp - Production Setup"
echo "==================================="
echo ""

# Kolory
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funkcja sprawdzająca czy komenda istnieje
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo -e "${YELLOW}[1/8] Aktualizacja systemu...${NC}"
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git vim ufw software-properties-common ca-certificates gnupg lsb-release

echo -e "${GREEN}✓ System zaktualizowany${NC}"
echo ""

echo -e "${YELLOW}[2/8] Konfiguracja firewall...${NC}"
sudo ufw --force enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
echo -e "${GREEN}✓ Firewall skonfigurowany${NC}"
echo ""

echo -e "${YELLOW}[3/8] Instalacja Docker...${NC}"
if command_exists docker; then
    echo "Docker już zainstalowany"
else
    # Dodaj repozytorium Docker
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Dodaj użytkownika do grupy docker
    sudo usermod -aG docker $USER
fi
echo -e "${GREEN}✓ Docker zainstalowany: $(docker --version)${NC}"
echo ""

echo -e "${YELLOW}[4/8] Instalacja Nginx...${NC}"
if command_exists nginx; then
    echo "Nginx już zainstalowany"
else
    sudo apt install -y nginx
    sudo systemctl start nginx
    sudo systemctl enable nginx
fi
echo -e "${GREEN}✓ Nginx zainstalowany${NC}"
echo ""

echo -e "${YELLOW}[5/8] Instalacja Certbot...${NC}"
if command_exists certbot; then
    echo "Certbot już zainstalowany"
else
    sudo apt install -y certbot python3-certbot-nginx
fi
echo -e "${GREEN}✓ Certbot zainstalowany: $(certbot --version)${NC}"
echo ""

echo -e "${YELLOW}[6/8] Konfiguracja Nginx dla SzalasApp...${NC}"
read -p "Wprowadź swoją domenę (np. szalasapp.kawak.uk): " DOMAIN

# Utwórz konfigurację Nginx
sudo tee /etc/nginx/sites-available/szalasapp > /dev/null <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Aktywuj konfigurację
sudo ln -sf /etc/nginx/sites-available/szalasapp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Sprawdź i przeładuj Nginx
sudo nginx -t
sudo systemctl reload nginx

echo -e "${GREEN}✓ Nginx skonfigurowany dla ${DOMAIN}${NC}"
echo ""

echo -e "${YELLOW}[7/8] Klonowanie repozytorium...${NC}"
if [ -d "$HOME/SzalasApp" ]; then
    echo "Katalog SzalasApp już istnieje. Pomijam klonowanie."
else
    read -p "Wprowadź URL repozytorium Git (lub naciśnij Enter aby pominąć): " REPO_URL
    if [ ! -z "$REPO_URL" ]; then
        cd $HOME
        git clone $REPO_URL SzalasApp
        cd SzalasApp
        echo -e "${GREEN}✓ Repozytorium sklonowane${NC}"
    else
        echo "Klonowanie pominięte. Skopiuj pliki ręcznie do ~/SzalasApp"
    fi
fi
echo ""

echo -e "${YELLOW}[8/8] Uzyskiwanie certyfikatu SSL...${NC}"
read -p "Wprowadź swój email dla Let's Encrypt: " EMAIL

sudo certbot --nginx -d ${DOMAIN} --email ${EMAIL} --agree-tos --no-eff-email --non-interactive

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Certyfikat SSL uzyskany${NC}"
else
    echo -e "${RED}✗ Błąd podczas uzyskiwania certyfikatu SSL${NC}"
    echo "Sprawdź czy DNS jest poprawnie skonfigurowane"
fi
echo ""

echo -e "${GREEN}==================================="
echo "  Setup zakończony!"
echo "===================================${NC}"
echo ""
echo "Następne kroki:"
echo "1. Przejdź do ~/SzalasApp: cd ~/SzalasApp"
echo "2. Skopiuj plik .env.example do .env: cp .env.example .env"
echo "3. Edytuj plik .env i wypełnij wszystkie wartości: vim .env"
echo "4. Skopiuj credentials/service-account.json"
echo "5. Uruchom aplikację: docker compose up -d --build"
echo "6. Sprawdź logi: docker compose logs -f"
echo ""
echo "Twoja aplikacja będzie dostępna pod: https://${DOMAIN}"
echo ""

