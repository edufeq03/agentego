#!/bin/bash

# Configurações
DB_NAME=${POSTGRES_DB:-atendimento}
DB_USER=${POSTGRES_USER:-user}
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

# Cria diretório de backup se não existir
mkdir -p $BACKUP_DIR

# Executa o dump (assume que o script roda onde o PGPASSWORD está no env ou via docker)
echo "Iniciando backup do banco de dados $DB_NAME..."

if [ -f /.dockerenv ]; then
    # Se estiver dentro do container
    pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE
else
    # Se estiver fora (host), tenta via docker compose
    docker compose exec -t db pg_dump -U $DB_USER $DB_NAME > $BACKUP_FILE
fi

if [ $? -eq 0 ]; then
    echo "Backup concluído com sucesso: $BACKUP_FILE"
    # Remove backups com mais de 7 dias
    find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete
    echo "Backups antigos removidos."
else
    echo "Erro ao realizar backup!"
    exit 1
fi
