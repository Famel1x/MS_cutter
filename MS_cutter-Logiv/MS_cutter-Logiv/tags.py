import random
import spacy
import whisper
from transformers import pipeline
from transformers import T5ForConditionalGeneration, T5Tokenizer
import re
from moviepy.editor import VideoFileClip

# Загрузка модели для русского языка
nlp = spacy.load("ru_core_news_sm")

def extract_audio(video_path):
    video = VideoFileClip(video_path)
    audio_path = video_path.replace(".mp4", ".wav")  # Сохраняем аудио как .wav
    video.audio.write_audiofile(audio_path, codec='pcm_s16le')  # Сохраняем аудио в формате .wav
    return audio_path

# Функция для распознавания речи
def transcribe_audio_for_tags(audio_path):
    model = whisper.load_model("medium", device= 'cuda')
    result = model.transcribe(audio_path, language="ru")
    return result['text']

# Фильтрация стоп-слов и выбор значимых слов для тегов
def generate_tags_from_text(transcribed_text, num_tags=5):
    # Анализируем текст через spacy
    doc = nlp(transcribed_text)

    # Извлекаем только значимые слова (существительные, глаголы и т.д.)
    significant_words = [token.lemma_ for token in doc if token.pos_ in ["NOUN", "VERB", "PROPN", "ADJ"]]

    # Если значимых слов меньше, чем нужно тегов, уменьшаем количество тегов
    if len(significant_words) < num_tags:
        num_tags = len(significant_words)

    # Выбираем случайные слова из списка
    selected_tags = random.sample(significant_words, num_tags)

    return selected_tags

# Очистка текста от лишних символов и ошибок
def clean_transcribed_text(text):
    # Удалим все не буквенные символы, кроме пробелов
    cleaned_text = re.sub(r'[^а-яА-ЯёЁ\s]', '', text)
    
    # Удалим лишние пробелы
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text

# Функция для разбиения текста на предложения
def split_into_sentences(text):
    # Убираем лишние символы, оставляем только текст
    text = re.sub(r'\s+', ' ', text).strip()  # Удалим лишние пробелы
    
    # Разбиваем текст на предложения по знакам препинания (точка, воскл., вопрос.)
    sentences = re.split(r'[.!?]', text)
    
    # Очищаем предложения от пустых строк
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    
    return sentences

# Функция для генерации случайного описания
def generate_random_description(transcribed_text):
    sentences = split_into_sentences(transcribed_text)
    
    # Если предложений нет, возвращаем сообщение об ошибке
    if not sentences:
        return "Не удалось сгенерировать описание, текст слишком короткий."
    
    # Выбираем случайное предложение
    random_sentence = random.choice(sentences)
    
    # Разбиваем предложение на слова
    words = random_sentence.split()
    
    # Если слов меньше 11, возвращаем полное предложение
    if len(words) < 11:
        return random_sentence
    
    # Если слов больше, выбираем случайный отрезок в 11-13 слов
    start_index = random.randint(0, len(words) - 11)  # Начинаем с позиции, чтобы хватило на 11 слов
    end_index = min(start_index + random.randint(11, 13), len(words))  # Конец - это 11-13 слов
    
    # Возвращаем выбранное сочетание слов как описание
    return ' '.join(words[start_index:end_index])

# Основная функция, которая обрабатывает видео и добавляет теги и описание
def generate_tags_and_description_for_video(video_path, audio_path, num_tags=5):
    # 1. Распознаем текст из аудио
    transcribed_text = transcribe_audio_for_tags(audio_path)

    # 2. Генерируем теги из распознанного текста
    tags = generate_tags_from_text(transcribed_text, num_tags)

    # 3. Генерируем описание (суммаризацию) текста
    description = generate_random_description(transcribed_text)

    # 4. Возвращаем список сгенерированных тегов и описание
    return tags, description

# Пример использования:
if __name__ == "__main__":
      # Укажите путь к аудио, полученному из видео
    video_path = "clip_13.mp4"  # Укажите путь к видео\
    audio_path = extract_audio(video_path)
    tags, description = generate_tags_and_description_for_video(video_path, audio_path, num_tags=8)  # Получаем 5 случайных тегов и описание
    print(f"Сгенерированные теги для видео: {tags}")
    print(f"Описание видео: {description}")