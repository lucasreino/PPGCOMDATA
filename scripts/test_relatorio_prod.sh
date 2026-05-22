#!/bin/bash
set -e
RESP=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@ppgcom.edu&password=Admin123!")
echo "LOGIN: ${RESP:0:80}..."
TOKEN=$(echo "$RESP" | grep -o '"access_token":"[^"]*"' | head -1 | cut -d'"' -f4)
if [ -z "$TOKEN" ]; then
  echo "LOGIN_FAILED"
  exit 1
fi
echo "TOKEN_OK len=${#TOKEN}"
HTTP=$(curl -s -o /tmp/rel_out.json -w "%{http_code}" -X POST http://127.0.0.1:8000/api/v1/analises/relatorio/gerar \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"instrucoes_usuario":"teste rapido","professor_id":null,"linha_pesquisa_id":null,"ano_inicio":2020,"ano_fim":2026}')
echo "HTTP $HTTP"
head -c 500 /tmp/rel_out.json
echo
