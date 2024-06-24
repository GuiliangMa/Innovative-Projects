# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
from pymongo import MongoClient
import time
import random
import requests
import json
import sys

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置MongoDB连接
client = MongoClient("mongodb://localhost:27017/")  # 根据实际MongoDB地址和端口配置
db = client["legaldb"]  # 替换为你的数据库名称
collection = db["legaldb"]  # 替换为你的集合名称

# 定义一个数组用于存储当前对话的记录便于将对话存储到数据库之中
messages = []


def call_api(question):
    url = "http://localhost:8000/v1/chat/completions"
    payload = {
        "model": "string",
        "messages": [
            {"role": "user", "content": question}
        ],
        "do_sample": True,
        "temperature": 0.9,
        "top_p": 0.7,
        "n": 1,
        "max_tokens": 2048,
        "stream": False
    }

    def generate():
        with requests.post(url, json=payload, stream=True) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line.startswith('data:'):
                            try:
                                json_data = json.loads(decoded_line[len('data:'):].strip())
                                content = json_data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                yield content
                            except json.JSONDecodeError:
                                continue
            else:
                yield f"API调用失败，状态码: {response.status_code}"

    print(generate())
    return Response(generate(), mimetype='text/plain')

    # payload = {
    #     "model": "string",
    #     "messages": [{"role": "user", "content": question}],
    #     "do_sample": True,
    #     "temperature": 0.5,
    #     "top_p": 0.4,
    #     "n": 1,
    #     "max_tokens": 2048,
    #     "stream": False  # 根据需要改为非流式传输
    # }
    #
    # try:
    #     # 发送请求
    #     with requests.post(url, json=payload) as response:
    #         if response.status_code == 200:
    #             # 将响应内容转换为JSON
    #             response_json = response.json()
    #             # 从响应中提取回答内容
    #             content = response_json.get('choices', [{}])[0].get('delta', {}).get('content', '')
    #             return content
    #         else:
    #             # 处理错误情况
    #             return f"API调用失败，状态码: {response.status_code}, 响应: {response.text}"
    # except requests.RequestException as e:
    #     return f"请求异常，异常信息: {e}"


with open('./front/public/assistance.json', 'r', encoding="utf-8") as file:
    # 加载JSON到Python变量
    responses = json.load(file)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/histories', methods=['GET'])
def getHistories():
    # 执行聚合查询
    pipeline = [
        {
            '$project': {
                '_id': 0,  # 排除默认的 _id 字段
                'messages': '$messages'  # 保留 messages 字段
            }
        },
        {
            '$addFields': {
                'messages': {
                    '$map': {
                        'input': '$messages',
                        'as': 'msg',
                        'in': {
                            'content': '$$msg.content',  # 提取每个 message 的 content 字段
                            'type': '$$msg.type'  # 提取每个 message 的 type 字段
                        }
                    }
                }
            }
        }
    ]

    cursor = collection.aggregate(pipeline)

    # 处理结果
    result = []
    for doc in cursor:
        result.append(doc['messages'])

    # 返回 JSON 响应
    return jsonify(result)


@app.route('/save', methods=['POST'])
def saveHistories():
    try:
        global messages  # 引用全局变量 messages

        if messages:  # 如果 messages 列表非空
            print(messages)
            # 存储整个 messages 列表到 MongoDB
            result = collection.insert_one({'messages': messages})
            messages = []  # 清空 messages 列表
            print(messages)
            return jsonify({'inserted_id': str(result.inserted_id)}), 201
        else:
            return jsonify({'message': 'No messages to save'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/query', methods=['POST'])
def call_api():
    def generate():
        try:
            with requests.post(url, json=payload, stream=True) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8').strip()  # 在后端解码
                            if decoded_line.startswith('data:'):
                                temp = decoded_line[len('data:'):].strip()
                                # print(temp)
                                if temp == "[DONE]":
                                    break
                                json_data = json.loads(decoded_line[len('data:'):].strip())
                                content = json_data.get('choices', [{}])[0].get('delta', {}).get('content', '')
                                # print(content)
                                if content != "":
                                    yield content  # 发送已解码和清洗后的内容
                                time.sleep(0.1)
                        # else:
                        #     yield "No data\n"
                else:
                    yield f"API调用失败，状态码: {response.status_code}\n"
        except requests.RequestException as e:
            yield f"请求异常，异常信息: {str(e)}\n"


    question = request.json['question']
    print(question)
    messages.append({'type': 'user', 'content': question})



    url = "http://localhost:8000/v1/chat/completions"  # 保证 URL 正确，包括 http://
    payload = {
        "model": "string",
        "messages": [{"role": "user", "content": question}],
        "do_sample": True,
        "temperature": 0.5,
        "top_p": 0.4,
        "n": 1,
        "max_tokens": 2048,
        "stream": True
    }
    return Response(generate(), mimetype='text/plain')


@app.route('/receive_data', methods=['POST'])
def receive_data():
    # 获取 JSON 数据
    data = request.get_json()
    print("Received data:", data)

    # 可以在这里处理数据，例如存储到数据库、进行计算等操作
    messages.append(data)
    # 响应前端
    return jsonify({"status": "success", "message": "Data received successfully"})


# @app.route('/respond', methods=['GET'])
# def respond():
#     # data = request.get_json()
#     data = request.args  # 使用 request.args 来获取 GET 请求参数
#     input_string = data.get("message", "").lower()  # 获取并转换为小写
#     print(input_string)
#     # 停顿2秒以模拟思考
#     sleep_time = random.uniform(1, 5)
#     time.sleep(sleep_time)
#
#     # 模糊匹配关键字
#     response = None
#     audio = None
#     for key in responses:
#         if key in input_string:
#             response = random.choice(responses[key]["messages"])
#             audio = responses[key]["audio"]
#             return jsonify({"response": response, "audio": audio})
#         else:
#             return call_api(input_string)


if __name__ == '__main__':
    app.run(debug=True)
