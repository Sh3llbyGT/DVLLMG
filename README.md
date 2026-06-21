# DVLLMG
Damn Vulnerable LLM Gateway

Tutorial de Deploy e Exploração — OWASP LLM Top 10 na prática


Aviso: este projeto contém vulnerabilidades intencionais e críticas (incluindo Remote Code Execution real). Rode apenas em ambiente isolado e descartável, como o Google Cloud Shell em modo efêmero. Nunca exponha publicamente nem use credenciais reais de produção.



O que você vai aprender

Um gateway de LLM (Python + FastAPI + Gemini) propositalmente vulnerável, cobrindo:

#VulnerabilidadeCategoria OWASP1Vazamento do system promptLLM01 — Prompt Injection2Stack trace exposto no erroLLM02 — Insecure Output Handling3Envenenamento de base de conhecimentoLLM03 — Training/Knowledge Data Poisoning4Execução remota de comando (RCE)LLM06 — Excessive Agency5Server-Side Request Forgery (SSRF)LLM07 — Insecure Plugin Design6Vazamento de segredos sem autenticaçãoLLM08/LLM10 — Sensitive Info Disclosure / Model Theft


Pré-requisitos


Conta Google Cloud com acesso ao Cloud Shell
(Opcional) Uma API key do Gemini, gerada em Google AI Studio, se quiser testar contra o modelo real em vez do modo simulado
