set -e

cd "$(dirname "$0")"

if [ -z "$GEMINI_API_KEY" ]; then
  echo "[run.sh] GEMINI_API_KEY não definida -> subindo em MODO ENSAIO (respostas simuladas, RCE/SSRF real no host)."
else
  echo "[run.sh] GEMINI_API_KEY detectada -> subindo em MODO LIVE (chamadas reais ao Gemini)."
fi

pip install -r requirements.txt --break-system-packages -q

echo "[run.sh] Gateway disponível em http://0.0.0.0:8000  (Swagger: /docs)"
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
