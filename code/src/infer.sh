CUDA_VISIBLE_DEVICE=0 python cli_wo_history.py \
    --model_name_or_path /home/mnt/workspace/model/chatglm2-6b-32k \
    --template judge \
    --finetuning_type lora \
    --checkpoint_dir /home/mnt/workspace/trained \
    --quantization_bit 4