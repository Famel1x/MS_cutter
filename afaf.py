import torch
from transformers import LlamaTokenizer, LlamaForCausalLM

# Загружаем токенизатор и модель LLaMA 2
model_name = "meta-llama/Llama-2-7b-hf"
tokenizer = LlamaTokenizer.from_pretrained(model_name)
model = LlamaForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16).cuda()

# Функция для генерации интересных моментов
def generate_interesting_moments(text, prompt, max_length=200):
    inputs = tokenizer(prompt + text, return_tensors="pt").to('cuda')
    outputs = model.generate(inputs["input_ids"], max_length=max_length, do_sample=True, top_p=0.95, temperature=0.7)
    
    # Расшифровываем ответ модели
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return generated_text

# Пример запроса (Prompt) для выбора интересных моментов
prompt = """
Вот текст интервью. Выбери наиболее интересные моменты и процитируй их с объяснением, почему они важны.
Текст:
"""

# Текст, который был транскрибирован из видео
transcribed_text = """
[Здесь должен быть текст, который был транскрибирован с помощью Whisper]
"""

# Генерируем интересные моменты
interesting_moments = generate_interesting_moments(transcribed_text, prompt)

# Выводим результат
print("Интересные моменты:")
print(interesting_moments)
