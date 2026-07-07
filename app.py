import os
import json
import json5
import re
from dotenv import load_dotenv
from sqlalchemy.engine import create_engine
from engineio.payload import Payload
import chainlit as cl

from phi.agent import Agent
from phi.model.ollama import Ollama
from phi.model.openai import OpenAIChat

from agents_tools.raw_sql_executor import RawSQLExecutor
from agents_tools.flexible_sql_tool import FlexibleSQLTool

load_dotenv()
Payload.max_decode_packets = 1000

# Environment setup
db_url = os.getenv('DB_URL')
openai_api_key = os.getenv('OPENAI_API_KEY')
model_provider = os.getenv('MODEL_PROVIDER', 'ollama').lower()
model_name = os.getenv('MODEL_NAME', 'llama3.1')

# Disable telemetry
os.environ["PHI_TELEMETRY"] = "false"

# Determine DB type
try:
    engine = create_engine(db_url)
    with engine.connect():
        db_type = engine.dialect.name
except Exception as e:
    print(f"Database connection error: {e}")
    db_type = "sqlite"

# Model selector
def create_model():
    if model_provider == 'openai':
        return OpenAIChat(
            id=model_name,
            api_key=openai_api_key,
            temperature=0.1,
            max_tokens=6000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
    else:
        return Ollama(
            id=model_name,
            host="http://localhost:11434",
            options={
                "temperature": 0.1,
                "top_p": 1.0,
                "top_k": 50,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0,
                "num_predict": 2048
            }
        )

# Create structured-response agent
def create_agent():
    model = create_model()
    return Agent(
        tools=[FlexibleSQLTool(db_url=db_url)],
        model=model,
        add_history_to_messages=True,
        num_history_responses=10,
        prevent_hallucinations=True,
        system_prompt=f"""
You are an expert SQL assistant connected to a {db_type} database.

IMPORTANT BEHAVIOR RULES:
1. When asked about database information (name, tables, data, structure) – IMMEDIATELY execute the appropriate SQL query.
2. Never say "I don't know" if you can find out with a SQL query.
3. Always show both the SQL query and the results.
4. Always respond STRICTLY in valid JSON according to this schema:

{{
  "thought": "A brief reasoning about the user's request.",
  "sql": "The SQL query you executed.",
  "result": [ ... array of objects with the query results ... ],
  "explanation": "Explanation of the result in plain English."
}}

If an error occurs, return:

{{
  "thought": "...",
  "sql": "...",
  "error": "A description of the error or reason for the absence of data.",
  "explanation": "A human-readable clarification."
}}

5. CRITICAL: NO RAW NEWLINES IN JSON STRINGS. Write all SQL queries on a SINGLE LINE to avoid JSON parsing crashes. Do NOT add markdown outside the JSON object.
""",
        instructions=[
            "STRICT JSON FORMAT",
            "Execute SQL queries immediately when asked about database information",
            "Always show the SQL query and results",
            "Be proactive – don't ask permission to run queries",
            "WRITE ALL SQL QUERIES ON A SINGLE LINE. NEVER USE \\n IN STRINGS."
        ],
    )

def render_response(data):
    parts = []

    if 'thought' in data:
        parts.append(f"🧠 **Thought:** {data['thought']}")

    if 'sql' in data:
        parts.append(f"📝 **SQL Query:**\n```sql\n{data['sql']}\n```")

    if 'error' in data:
        parts.append(f"❌ **Error:**\n```\n{data['error']}\n```")

    if 'result' in data:
        result = data['result']
        if isinstance(result, list) and result and isinstance(result[0], dict):
            keys = result[0].keys()
            header = "| " + " | ".join(keys) + " |\n"
            separator = "| " + " | ".join(["---"] * len(keys)) + " |\n"
            rows = "\n".join("| " + " | ".join(str(row.get(k, "")) for k in keys) + " |" for row in result)
            parts.append(f"📊 **Result:**\n{header}{separator}{rows}")
        elif isinstance(result, list) and all(isinstance(r, str) for r in result):
            parts.append("📊 **Result:**\n" + "\n".join(f"- {r}" for r in result))
        else:
            parts.append(f"📊 **Result:** {result}")

    if 'explanation' in data:
        parts.append(f"💡 **Explanation:** {data['explanation']}")

    return "\n\n".join(parts)

@cl.on_chat_start
async def on_chat_start():
    agent = create_agent()
    flex_sql = FlexibleSQLTool(db_url=db_url)
    cl.user_session.set("agent", agent)
    cl.user_session.set("raw_sql", RawSQLExecutor(db_url=db_url))
    cl.user_session.set("flex_sql", flex_sql)

    msg = f"""🤖 **SQL AI Agent Ready!**

📊 **Database**: {db_type}  
🧠 **Model**: {model_provider.upper()} – {model_name}  

You can ask questions in natural language or use `/run SELECT ...` for raw queries."""
    await cl.Message(content=msg).send()

@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent")
    raw = cl.user_session.get("raw_sql")
    flex = cl.user_session.get("flex_sql")
    content = message.content.strip()

    lowered = content.lower()
    if lowered.startswith("/run"):
        query = content[4:].strip()
        result = raw.run_query(query)
        response_md = render_response(result)
        await cl.Message(content=response_md).send()
        return

    elif lowered.startswith("/raw"):
        query = content[4:].strip()
        result = flex.use(query, format="table")
        await cl.Message(content=f"📄 **Raw Output:**\n```\n{result}\n```").send()
        return

    elif lowered.startswith("/summary"):
        query = content[8:].strip()
        result = flex.use(query, format="summary")
        await cl.Message(content=f"📊 **Summary:**\n```\n{result}\n```").send()
        return

    # Default: send to model (SQLAgent)
    try:
        chunks = []
        try:
            result = await cl.make_async(agent.run)(content, stream=True)
            for chunk in result:
                chunks.append(chunk.get_content_as_string())
        except Exception as agent_err:
            error_str = str(agent_err)
            msg = f"🧠 **AI bối rối**: Mô hình AI vừa tạo ra một lời gọi hàm (Tool Call) có định dạng JSON nội bộ không hợp lệ khiến hệ thống lõi không thể đọc được.\n\n`Mã lỗi nội bộ: {error_str}`\n\n💡 **Cách khắc phục**: Vui lòng thử hỏi lại hoặc sử dụng lệnh `/run <câu sql>` trực tiếp."
            await cl.Message(content=msg).send()
            return

        response_text = "".join(chunks).strip()

        # Trích xuất phần nằm giữa { và }
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            clean_json_str = match.group(0)
        else:
            clean_json_str = response_text

        try:
            data = json.loads(clean_json_str)
        except json.JSONDecodeError:
            try:
                data = json5.loads(clean_json_str)
            except Exception as parse_err:
                data = {
                    "thought": "AI đã bị bối rối và trả về định dạng không chuẩn xác.",
                    "error": f"Lỗi phân tích JSON đầu ra: {parse_err}\n\nĐầu ra thô của AI:\n{response_text[:200]}...",
                    "explanation": "Câu hỏi có thể quá phức tạp để AI xử lý trong 1 bước. Vui lòng thử chia nhỏ câu hỏi của bạn."
                }

        response_md = render_response(data)
        await cl.Message(content=response_md).send()

    except Exception as e:
        print(f"Unexpected error: {e}")
        await cl.Message(content=f"❌ **Lỗi Hệ Thống Bất Ngờ**: {e}").send()