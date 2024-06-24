import requests
import json
import sys
import time

def call_api(question):
    url = "http://localhost:8000/v1/chat/completions"
    # api 端口
    payload = {
        "model": "string",
        "messages": [
            {"role": "user", "content": question}
        ],
        "do_sample": True,
        "temperature": 0.5,
        "top_p": 0.4,
        "n": 1,
        "max_tokens": 2048,
        "stream": True  # 启用流式传输
    }
    try:
        with requests.post(url, json=payload, stream=True) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith('data:'):
                            try:
                                json_data = json.loads(decoded_line[len('data:'):].strip())
                                content = json_data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                for char in content:
                                    sys.stdout.write(char) 
                                    sys.stdout.flush()
                                    time.sleep(0.05) 
                            except json.JSONDecodeError:
                                continue
            else:
                print(f"API调用失败，状态码: {response.status_code}, 响应: {response.text}")
    except requests.RequestException as e:
        print(f"请求异常，异常信息: {e}")

def main():
    while True:
        question = input("\n请输入您的问题 (输入'exit'结束对话): ")
        if question == 'exit':
            break
        print("\n回答：")
        call_api(question)

if __name__ == "__main__":
    main()
