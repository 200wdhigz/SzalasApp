#!/bin/bash
# Skrypt backupu dla SzalasApp
# Użycie: ./backup.sh

BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="szalasapp_backup_${DATE}.tar.gz"

# Kolory
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Tworzenie backupu SzalasApp...${NC}"

# Utwórz katalog backup jeśli nie istnieje
mkdir -p ${BACKUP_DIR}

# Backup plików aplikacji
cd ~/SzalasApp
tar -czf ${BACKUP_DIR}/${BACKUP_FILE} \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    --exclude='venv' \
    .env credentials/ app/ docker-compose.yml Dockerfile

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup utworzony: ${BACKUP_DIR}/${BACKUP_FILE}${NC}"

    # Rozmiar backupu
    SIZE=$(du -h ${BACKUP_DIR}/${BACKUP_FILE} | cut -f1)
    echo "Rozmiar: ${SIZE}"
else
    echo "✗ Błąd podczas tworzenia backupu"
    exit 1
fi

# Usuń backupy starsze niż 30 dni
DELETED=$(find ${BACKUP_DIR} -name "szalasapp_backup_*.tar.gz" -mtime +30 -delete -print | wc -l)
if [ $DELETED -gt 0 ]; then
    echo "Usunięto ${DELETED} starych backupów (>30 dni)"
fi

# Lista wszystkich backupów
echo ""
echo "Wszystkie backupy:"
ls -lh ${BACKUP_DIR}/szalasapp_backup_*.tar.gz 2>/dev/null || echo "Brak innych backupów"

