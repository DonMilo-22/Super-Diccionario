#!/bin/bash
set -e

echo "Word Helper - instalacion para macOS"

if ! command -v python3 >/dev/null 2>&1; then
  echo "No se encontro Python 3."
  exit 1
fi

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

cat > "Word Helper.command" <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
exec .venv/bin/python main.py
EOF

chmod +x "Word Helper.command"

echo
echo "Listo. Abre 'Word Helper.command' para iniciar la app."
