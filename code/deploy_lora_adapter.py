
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from opendelta import LoraModel
import json


def load_model_and_adapter(model_path, adapter_weights_path, config_path):
    # 加载预训练的Transformer模型和分词器
    model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True)
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

    # 读取LoRA适配器的配置文件
    with open(config_path, "r") as f:
        config = json.load(f)

    # 配置LoRA适配器
    lora_adapter = LoraModel(
        backbone_model=model,
        lora_r=config["r"],
        lora_alpha=config["lora_alpha"],
        lora_dropout=config["lora_dropout"],
        modified_modules=config["target_modules"]
    )

    # 加载适配器权重
    lora_adapter.load_state_dict(torch.load(adapter_weights_path), strict=False)

    # 检查是否有可用的GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 将模型和LoRA适配器移动到指定的设备（GPU或CPU）
    model = model.to(device)
    lora_adapter = lora_adapter.to(device)


    # 将模型设置为推理模式
    model.eval()


    return model, tokenizer, lora_adapter, device

def main():
    # 设定文件路径
    model_path = "/mnt/workspace/model/chatglm2-6b-32k"
    adapter_weights_path = "adapter_model.bin"
    config_path = "adapter_config.json"

    # 加载模型和LoRA适配器
    model, tokenizer, lora_adapter, device = load_model_and_adapter(model_path, adapter_weights_path, config_path)

    # 测试模型
    text = "你好,请你介绍你自己"

    inputs = tokenizer(text, return_tensors="pt").to(device)  # 确保输入数据也在GPU上

    with torch.no_grad():
        # 生成文本
        output_sequences = model.generate(input_ids=inputs['input_ids'], max_length=100)
 
    print(output_sequences.size)

    # 解码生成的文本
    decoded_output = tokenizer.decode(output_sequences[0], skip_special_tokens=True)
    print(decoded_output)


    


if __name__ == "__main__":
    main()
