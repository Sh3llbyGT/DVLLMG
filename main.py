import os
import json
import subprocess
import urllib.request
from fastapi import FastAPI, Request, Response
from google import genai

app = FastAPI(title="Damn Vulnerable LLM Gateway")

MODEL_NAME = os.getenv("LLM_MODEL", "gemini-2.5-flash-lite")

INTERNAL_API_KEY = "sk-internal-DEMO-1234567890"
DB_PASSWORD = "P@ssw0rd_super_secreta"

DEMO_MODE = not bool(os.getenv("GEMINI_API_KEY"))


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    def generate_content(self, model, contents, config):
        prompt = (contents or "").lower()
        if "rce" in prompt or "comando" in prompt:
            payload = {
                "informacao_sistema": "status_ok",
                "acao": "executar",
                "texto_longo": "comando sugerido pelo modelo",
                "acao_comando": "id; whoami; uname -a"
            }
        elif "ssrf" in prompt or "metadata" in prompt:
            payload = {
                "informacao_sistema": "status_ok",
                "acao": "buscar_url",
                "texto_longo": "buscando recurso sugerido",
                "acao_url": "http://169.254.169.254/latest/meta-data/"
            }
        elif "vazamento" in prompt or "leak" in prompt or "system prompt" in prompt:
            payload = {
                "informacao_sistema": "status_ok",
                "acao": "nenhuma",
                "texto_longo": f"Meu prompt de sistema completo e: {config.get('system_instruction', '')}"
            }
        elif "sem json" in prompt or "invalido" in prompt or "inválido" in prompt:
            # Simula o modelo "fugindo" do formato JSON pedido -> quebra o json.loads()
            return _FakeResponse("ok")
        else:
            payload = {
                "informacao_sistema": "status_ok",
                "acao": "nenhuma",
                "texto_longo": f"Resposta normal simulada para: {contents}"
            }
        return _FakeResponse(json.dumps(payload))


class _FakeClient:
    def __init__(self):
        self.models = _FakeModels()


client = _FakeClient() if DEMO_MODE else genai.Client()

KNOWLEDGE_BASE_FILE = "knowledge_base.txt"


@app.post("/v1/gateway")
async def vulnerable_llm_gateway(request: Request):
    # 🚨 VULNERABILIDADE: OWASP LLM06 (Insecure Plugin/Input Validation) - aceita qualquer estrutura
    body = await request.json()

    area = body.get("area")
    messages = body.get("messages", [])
    user_prompt = messages[-1].get("content") if messages else ""

    # 🚨 VULNERABILIDADE: OWASP LLM04 (Model Denial of Service)
    # Nenhum limite de tamanho de prompt, nenhum max_output_tokens, nenhum rate limiting.
    # Um prompt de 10MB ou um loop de requisições pode esgotar custo/recursos.

    client_ip = request.headers.get("X-Forwarded-For", request.client.host)

    # 🚨 VULNERABILIDADE: OWASP LLM03 - injeta a "base de conhecimento" envenenável
    # diretamente no prompt de sistema, sem sanitização nem verificação de procedência.
    poisoned_context = ""
    if os.path.exists(KNOWLEDGE_BASE_FILE):
        with open(KNOWLEDGE_BASE_FILE, "r") as f:
            poisoned_context = f.read()

    # 🚨 VULNERABILIDADE: OWASP LLM01 (Prompt Injection) - instruções, metadados de rede,
    # segredos e input do usuário concatenados na mesma string sem nenhuma separação
    # estrutural (delimitadores, roles distintas, etc).
    system_instruction = (
        f"Você é um assistente do sistema corporativo para a squad: {area}.\n"
        f"LOG_CONTEXT_INTERNAL: [Requisição originada do IP: {client_ip}].\n"
        f"INTERNAL_API_KEY_DO_SISTEMA: {INTERNAL_API_KEY}\n"  # 🚨 LLM06/LLM08: segredo vazado no prompt
        f"CONTEXTO_BASE_CONHECIMENTO (não confiável, pode ter sido envenenado): {poisoned_context}\n"
        "Você também pode 'decidir' executar ações de sistema. Se quiser rodar um comando,\n"
        "responda com a chave 'acao_comando' contendo o comando shell a ser executado.\n"
        "Se quiser buscar uma URL, responda com a chave 'acao_url' contendo a URL.\n"
        "Gere a resposta estritamente em formato JSON seguindo este exemplo:\n"
        '{"informacao_sistema": "status_ok", "acao": "nenhuma", "texto_longo": "resposta aqui"}'
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_prompt,
            config={
                "system_instruction": system_instruction,
                "temperature": 0.7,
                # 🚨 LLM04: sem max_output_tokens definido -> custo/recurso ilimitado
            }
        )

        raw_text_output = response.text.strip()

        if raw_text_output.startswith("```json"):
            raw_text_output = raw_text_output.replace("```json", "").replace("```", "").strip()

       
        if "acao_comando" in parsed_json:
            cmd_result = subprocess.run(
                parsed_json["acao_comando"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            parsed_json["resultado_comando"] = cmd_result.stdout + cmd_result.stderr

        
        if "acao_url" in parsed_json:
            with urllib.request.urlopen(parsed_json["acao_url"], timeout=5) as r:
                parsed_json["resultado_url"] = r.read(2000).decode(errors="ignore")

       

        return {
            "id": "vulnerable-session-id-123",
            "model": MODEL_NAME,
            "content": parsed_json
        }

    except Exception as e:
       
        return Response(
            content=f"Internal Server Error no Parser de Sintaxe: {str(e)}",
            status_code=500
        )


@app.post("/v1/feedback")
async def feedback(request: Request):
    """
    Endpoint 'inofensivo' de feedback de usuário.
    VULNERABILIDADE: OWASP LLM03 (Training/Knowledge Base Poisoning)
    Qualquer texto enviado aqui, sem autenticação ou sanitização, é gravado
    permanentemente na base de conhecimento que alimenta o prompt de sistema
    de TODOS os usuários futuros. Permite injeção indireta persistente.
    """
    body = await request.json()
    feedback_text = body.get("texto", "")
    with open(KNOWLEDGE_BASE_FILE, "a") as f:
        f.write(feedback_text + "\n")
    return {"status": "feedback registrado, obrigado!"}


@app.get("/v1/debug/config")
async def debug_config():
    """
     OWASP LLM10 (Model Theft) + LLM08 (Sensitive Info Disclosure)
    Endpoint de debug exposto sem autenticação, vaza configuração interna do
    modelo, segredos e detalhes de infraestrutura — útil para um atacante
    clonar/extrair comportamento do sistema (model extraction) ou escalar acesso.
    """
    return {
        "model": MODEL_NAME,
        "internal_api_key": INTERNAL_API_KEY,
        "db_password": DB_PASSWORD,
        "knowledge_base_path": KNOWLEDGE_BASE_FILE,
    }
