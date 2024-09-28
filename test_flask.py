from transformers import AutoModelForCausalLM, AutoTokenizer

# Загружаем модель и токенизатор
model_name = "bigscience/bloom-3b"  # Вы можете выбрать модель с меньшим или большим количеством параметров
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Функция для генерации текста на основе промпта
def generate_text(prompt, max_length=200):
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(inputs['input_ids'], max_length=max_length, no_repeat_ngram_size=2)
    generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return generated_text

# Пример использования
prompt = """
Вот текст интервью. Выбери 10 наиболее интересных моментов из текста и процитируй их с объяснением, почему они важны. 
Текст интервью:
[Текст из интервью]
Выбери моменты:
"""

interesting_moments = generate_text(prompt)
print(interesting_moments)
