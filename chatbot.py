from llama_index.llms.openai import OpenAI
from llama_index.core.agent import FunctionCallingAgentWorker
from llama_index.core.agent import AgentRunner
from tools import initial_tools, init_tools
from config import OPENAI_API_KEY
import sys
from io import StringIO
from contextlib import redirect_stdout
import re
import json


llm = OpenAI(model="gpt-4o-mini", temperature=0)

agent_worker = FunctionCallingAgentWorker.from_tools(
    initial_tools,
    llm=llm,
    system_prompt="""You are a helpful assistant. Answer what the user says. Try to response as short and meaning full as possible, and remove all the bullet points""",
    verbose=False
)
agent1= AgentRunner(agent_worker)

agent_worker2 = FunctionCallingAgentWorker.from_tools(
    init_tools,
    llm=llm,
    system_prompt="""You are a helpful assistant. Answer what the user says. Try to response as short and meaning full as possible, and remove all the bullet points""",
    verbose=True
)

agent2 = AgentRunner(agent_worker2)

queries = "iphone 16 pro"



def get_response(query, agent) -> str:
    print(query)
    response = agent.query(query)
    return str(response)


def capture_verbose_output(query, agent):
    # Tạo bộ đệm để lưu output
    buffer = StringIO()
    
    # Chuyển hướng stdout vào buffer
    with redirect_stdout(buffer):
        response = agent.query(query)  # Gọi agent.query, verbose output sẽ được ghi vào buffer
    
    # Lấy nội dung verbose từ buffer
    verbose_output = buffer.getvalue()
    return verbose_output

def parse_function_output(verbose_text):
    pattern = r'=== Function Output ===\n(.*?)(?=\n={3,}|\Z)'
    matches = re.findall(pattern, verbose_text, re.DOTALL)
    
    names = []
    for output_text in matches:
        cleaned_output = output_text.strip()
        cleaned_output = cleaned_output.replace("'", "\"")  # nếu cần

        # Cố gắng trích xuất phần JSON thực sự nếu nó bị lẫn noise
        start = cleaned_output.find('[')
        end = cleaned_output.rfind(']')
        if start != -1 and end != -1:
            json_str = cleaned_output[start:end+1]
            try:
                output = json.loads(json_str)
                for item in output:
                    if isinstance(item, dict) and 'product_id' in item:
                        names.append(item['product_id'])
            except json.JSONDecodeError as e:
                print(f"JSON error: {e}")
                print(json_str)
                continue
    return names if names else 'Không tìm thấy tên sản phẩm'

def get_mentioned(query, agent) -> str:
    # Lấy verbose output và response
    verbose_text = capture_verbose_output(query, agent)
    print("Verbose output:", verbose_text)
    
    # Trích xuất tên sản phẩm từ Function Output
    return  parse_function_output(verbose_text)

# query = "iPhone 16 Pro và Samsung Galaxy S25 Ultra"
# res = get_mentioned(query, agent2)
# # response = get_response(query, agent1)
# print(res)
