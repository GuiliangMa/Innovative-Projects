<template>

  <el-header class="custom-header">
    <div class="header-content">
      <div class="title">
        <div class="title-text">裁判文书大模型</div>
      </div>
    </div>
  </el-header>
  <div class="background">

    <div class="chat-container">
      <div class="chat-history-wrapper" id="message">
        <div class="chat-history" ref="chatHistory">
          <div v-for="(message, index) in messages" :key="index" :class="['message-item', message.type]">
            <div id="" :class="['message-content', message.type]" v-html="formatMessage(message.content)"></div>
          </div>
          <div ref="bottomMarker"></div>
        </div>
      </div>
      <div class="chat-input">
        <textarea ref="userInput"
                  id="userInput"
                  :disabled="sending||isOld"
                  v-model="userMessage"
                  @input="adjustTextareaHeight"
                  @keydown.enter.prevent="handleEnterKey"
                  placeholder="请输入消息..."
                  :style="{ height: '1em', lineHeight: '1em', backgroundColor: '#inputBackgroundColor', border: '1px solid #ccc', padding: '10px', borderRadius: '5px', resize: 'none' }"
        ></textarea>
        <!--        <button @click="sendMessage" :disabled="sending" :style="{ backgroundColor: sending ? '#ccc' : '#4CAF50' }" style="margin-left: 30px">发送</button>-->
        <button :disabled="sending||isOld" @click="sendMessage"
                :style="{ backgroundColor: sending||isOld ? '#ccc' : '#4CAF50' }"
                style=" color: white; border: none; padding: 10px 15px; cursor: pointer; display: flex; align-items: center;">
          <svg width="32" height="28" style="margin-right: 0px;">
            <path fill="currentColor"
                  d="M15.192 8.906a1.143 1.143 0 0 1 1.616 0l5.143 5.143a1.143 1.143 0 0 1-1.616 1.616l-3.192-3.192v9.813a1.143 1.143 0 0 1-2.286 0v-9.813l-3.192 3.192a1.143 1.143 0 1 1-1.616-1.616z"></path>
          </svg>
        </button>

      </div>
    </div>

    <div style="display: flex">
      <div style="width: 20%; border-right: 1px solid #aaaaaa; min-height: calc(100vh - 60px)">
        <div class="history-item" style="border-bottom: 1px solid #ddd; white-space: nowrap;" @click="newQuery()">
          <card>
            <div class="new-query">
              <i class="icon el-icon-circle-plus-outline"></i>
              创建新对话
            </div>

          </card>
        </div>

        <div class="history-item">
          <card>
            <div class="history-content">
              {{ messages[0] ? messages[0].content : '您还没有提问问题' }}
            </div>
          </card>
        </div>
        <h6 style="margin-left: 10px">历史</h6>
        <div v-for="(history, index) in sortedHistories" :key="index" class="history-item"
             @click="handleHistoryClick(history)">
          <div class="history-content"> {{ history[0] ? history[0].content : 'No content available' }}</div>
        </div>
      </div>
    </div>
  </div>

</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      userMessage: '',
      messages: [],
      histories: [],
      sending: false,
      inputBackgroundColor: '#f0f0f0',// 默认输入框内部背景色
      isOld: false,//判断是否为历史信息
      passOld: false,//判断是否是历史消息来判定是否存储，关键在于前一个状态
    };
  },
  computed: {
    sortedHistories() {
      return this.histories.slice().reverse();
    }
  },
  created() {
    // 监听窗口即将关闭的事件
    window.addEventListener('beforeunload', this.handlePageClose);
  },
  methods: {
    handlePageClose() {
      // 在此处执行保存操作，例如调用保存历史数据的方法
      this.saveHistoryToMongo();
    }
    ,
    async sendMessage() {
      if (this.userMessage.trim() !== '') {
        this.messages.push({type: 'user', content: this.userMessage});
        this.userMessage = ''; // 清空输入框
        this.sending = true;

        // 模拟机器人回复
        await this.sendToBackend(this.messages[this.messages.length - 1].content);

        this.sending = false; // 恢复发送按钮的可用状态
        this.inputBackgroundColor = '#f0f0f0'; // 恢复输入框内部背景色

        // 发送消息后立即滚动到底部,写到信息请求回答的函数里面
        this.$nextTick(() => {
          this.scrollToBottom('message');
        });
      }
    }
    ,
    async getHistories() { // 获取历史数据
      try {
        console.log("Fetching histories..."); // 添加一个日志以确保函数调用正常

        const response = await axios.get('http://127.0.0.1:5000/histories');

        // 假设后端返回的数据在response.data中
        this.histories = response.data; // 将返回的数据存储在组件的 histories 属性中
      } catch (error) {
        console.error('Error fetching histories:', error); // 如果出现错误，打印错误信息
        // 可以添加更详细的错误处理逻辑，比如显示错误信息到界面上
        console.log("Failed to fetch histories."); // 日志记录数据获取失败
      }
    }
    ,
    async sendToBackend(question) {
      const url = "http://localhost:5000/query"; // 确保这是正确的后端URL
      this.messages.push({'content': "请稍等……", 'type': 'bot'});
      this.sending = true;

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({question: question})
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let result = '';
        console.log("jinru")
        // 读取数据流
        while (this.sending) {
          const {done, value} = await reader.read();
          if (done) {
            this.updateMessagesFromStreams(result); // 最后一次更新消息
            break;
          }

          const chunk = decoder.decode(value, {stream: true});
          console.log(chunk); // 输出接收到的每个部分
          result += chunk; // 累积完整的消息

          // 如果你需要实时更新每个接收到的片段
          this.updateMessagesFromStreams(result); // 逐个更新界面
        }

        // 标记发送完成
        this.sending = false;
        this.sendDataToBackend();//将完整的回复传递给后端
      } catch (error) {
        console.error('Error sending to backend:', error);
        this.sending = false;
      }
    },


    updateMessagesFromStreams(result) {
      if (result) {
        // 检查 messages 数组是否为空，避免在空数组上执行无效操作
        if (this.messages.length > 0) {
          // 直接修改 messages 数组的最后一个元素
          this.messages[this.messages.length - 1] = {content: result, type: 'bot'};

        } else {
          // 如果 messages 数组为空，则添加新的消息
          this.messages.push({content: result, type: 'bot'});
        }
      } else {
        console.error('Streams is not defined or not an array');
      }
    },
    sendDataToBackend() {
      const url = "http://localhost:5000/receive_data";  // 后端 URL
      const dataToSend = this.messages[this.messages.length - 1];

      axios.post(url, dataToSend)
          .then(response => {
            console.log('Success:', response.data);
          })
          .catch(error => {
            console.error('Error:', error);
          });
    },
    newQuery() {
      this.saveHistoryToMongo();
      this.passOld = this.isOld;
      this.isOld = false;
      this.messages = [];
      this.getHistories();
      this.scrollToBottom('message');
    }
    ,
    async saveHistoryToMongo() { //在创建新对话或者关闭界面的时候调用
      try {
        const response = await axios.post('http://127.0.0.1:5000/save');

        // 假设后端返回的数据在response.data中
        console.log(response.data)
      } catch (error) {
        console.error('Error getHistory message:', error);
        // 可以添加错误处理逻辑
        console.log("数据获取失败")
      }
    },
    saveHistory() {
      if (this.messages && this.messages.length > 0 && !this.passOld) {
        this.histories.push(this.messages);
      }
    }
    ,
    scrollToBottom(id) { //实现了输入框和对话框保持在最底部
      var div = document.getElementById(id);
      div.scrollTop = div.scrollHeight;
    }
    ,
    adjustTextareaHeight() {
      const textarea = this.$refs.userInput;
      textarea.style.height = 'auto'; // 重置高度
      textarea.style.height = `${Math.min(textarea.scrollHeight, window.innerHeight / 4)}px`; // 限制高度为视窗的四分之一
    }
    ,
    handleHistoryClick(history) {
      // 点击历史记录的处理函数
      console.log('Clicked history:', history);
      this.passOld = this.isOld;
      this.isOld = true;
      this.saveHistory();
      this.messages = history;
      if (!this.passOld) {
        this.saveHistoryToMongo();
      }
      // 可以在这里添加其他处理逻辑，例如加载历史记录等
    }
    ,
    handleEnterKey(event) {
      if (event.key === 'Enter') {
        event.preventDefault(); // 阻止默认的回车换行行为

        if (event.shiftKey) {
          // 如果按下 Shift 键，则在输入框中插入换行符
          const textarea = this.$refs.userInput;
          const start = textarea.selectionStart;
          const end = textarea.selectionEnd;
          const oldValue = this.userMessage;
          this.userMessage = `${oldValue.substring(0, start)}\n${oldValue.substring(end)}`;


          this.$nextTick(() => {
            textarea.selectionStart = textarea.selectionEnd = start + 1;
            this.adjustTextareaHeight(); // 调整输入框高度
            this.scrollToBottom('userInput')
          });
        } else {
          // 如果没有按下 Shift 键，则发送消息
          if (!(this.sending || this.isOld))
            this.sendMessage();
        }
      }
    }
    ,
    formatMessage(message) {
      return message.replace(/\n/g, '<br>');
    }
  }
  ,
  mounted() { //数据初始化的时候会调用
    this.getHistories();
    this.scrollToBottom('massage'); // 初始化时滚动到底部
    this.adjustTextareaHeight(); // 调整文本框高度
  }
}
;
</script>

<style scoped>
@import url("//unpkg.com/element-ui@2.13.2/lib/theme-chalk/index.css");

:global(body) {
  margin: 0; /* 去除页面的默认边距 */
  padding: 0; /* 去除页面的默认内边距 */
  overflow: hidden; /* 隐藏所有内容的滚动条 */
}

.background {
  background-image: url('./assets/background.jpg');
  background-size: cover; /* 调整背景图片大小以覆盖整个区域 */
  background-position: center; /* 设置背景图片位置为中心 */
  /* 其他样式属性可以根据需求自行添加，比如背景颜色、高度等 */
  min-height: 500px; /* 设置最小高度，确保背景图显示 */
}

.custom-header {
  background-color: #45a049;
  height: 50px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #ddd;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 50px; /* 左右边距调整 */
}

.add-icon {
  font-size: 20px; /* 调整图标大小 */
  margin-left: 10px; /* 调整图标与文字之间的间距 */
  color: #4CAF50;
}

.title {
  flex: 1; /* 自动撑开剩余空间 */
  display: flex;
  align-items: center;
}

.title-text {
  font-weight: bold;
  color: white;
  font-size: 20px;
  margin-left: 2%;
}

.button-group {
  padding-right: 12%;
  display: flex;
  align-items: center;
}

.chat-container {
  position: absolute; /* 使用绝对定位 */
  top: 50px;
  right: 0; /* 让容器靠右 */
  height: 100vh; /* 占据整个视口高度 */
  width: 75%; /* 占据屏幕宽度的 75% */

  display: flex;
  flex-direction: column;
}


.chat-history-wrapper {
  flex: 1; /* 占据剩余空间 */
  overflow-y: auto; /* 允许垂直滚动 */
  padding-right: 20px; /* 留出一些空间以避免滚动条覆盖内容 */
}

.chat-history {
  width: 100%; /* 宽度占满父容器 */
  max-width: 100%;
  padding: 10px;
  box-sizing: border-box;
}

.message-item {
  margin-right: 9%;
  margin-left: 7%;
  display: flex;
  justify-content: flex-end; /* 将用户消息放在右侧 */
  margin-bottom: 10px;
  margin-top: 10px;
}

.message-item.bot {
  justify-content: flex-start; /* 将机器人消息放在左侧 */
}


.message-content {
  padding: 10px;
  border-radius: 10px;
  background-color: #DCF8C6; /* 用户消息背景色 */
  max-width: 100%;
  word-wrap: break-word;
}

.message-content.bot {
  background-color: #E0E0E0; /* 机器人消息背景色 */
}

.chat-input {
  margin-bottom: 6%;
  display: flex;
  margin-left: 8%;
  margin-right: 10%;
  align-items: center;
  padding: 10px;


}

.chat-input textarea {
  flex: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  font-size: 18px;
  margin-right: 18px;
  resize: none; /* 禁止用户调整文本框大小 */
  overflow-y: auto; /* 允许垂直滚动 */
  min-height: 40px; /* 设置最小高度 */
  background-color: #f0f0f0; /* 内部背景色 */
}

button {
  margin-left: 10px;
  padding: 10px 20px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s ease;
}

button:hover {
  background-color: #45a049;
}

@media (max-width: 600px) {
  .chat-history {
    padding: 10px 20px;
  }

  .message-content {
    max-width: 100%;
  }

  .chat-input {
    padding: 0px;
  }
}

.button-group button {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 0px 0px;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.button-group button[disabled] {
  background-color: #ccc;
  cursor: not-allowed;
}

.history-item {
  border-radius: 10%; /* 设置圆角的大小，单位可以是像素(px)或百分比(%) */
  cursor: pointer;
  padding: 10px;
  min-height: 25px;
//border-bottom: 1px solid #ddd; white-space: nowrap; /* 防止内容换行 */ overflow: hidden; /* 隐藏超出部分 */ text-overflow: ellipsis; /* 使用省略号表示溢出内容 */ margin-left: 2%; margin-right: 2%;
}

.history-item:hover {
  background-color: #f0f0f0; /* 悬停效果 */
}

.history-content {
  min-height: 20px;
  margin-top: 1px;
  white-space: nowrap; /* 防止内容换行 */
  overflow: hidden; /* 隐藏超出部分 */
  text-overflow: ellipsis; /* 使用省略号表示溢出内容 */
  margin-left: 5px;
}

.icon {
  font-weight: bold;
  font-size: 23px;
}

.new-query {
  font-weight: bold;
  display: flex;
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
}
</style>