import whisper
import torch
from transformers import pipeline
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip
from tqdm import tqdm
import re

# Функция для извлечения аудио из видео
def extract_audio(video_path):
    video = VideoFileClip(video_path)
    audio_path = video_path.replace(".mp4", ".wav")  # Сохраняем аудио как .wav
    video.audio.write_audiofile(audio_path, codec='pcm_s16le')  # Сохраняем аудио в формате .wav
    return audio_path

# Функция для транскрибации аудио с Whisper
def transcribe_audio(audio_path):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model("base", device=device)
    
    # Транскрибируем аудио
    result = model.transcribe(audio_path, language="ru")
    
    segments = result["segments"]
    
    # Отображаем прогресс по мере обработки сегментов
    transcribed_segments = []
    for segment in tqdm(segments, desc="Transcribing Audio"):
        transcribed_segments.append(segment)
    
    return result["text"], transcribed_segments

def select_interesting_segments(text, num_segments):
    # Отключим GPU для суммаризации временно, если возникли ошибки с CUDA
    # device = 0 if torch.cuda.is_available() else -1
    device = -1  # Запуск модели на CPU для устранения ошибок
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=device)
    
    # Разбиваем текст на блоки длиной не более 1024 символов для предотвращения ошибок
    max_block_size = 1024
    text_blocks = [text[i:i+max_block_size] for i in range(0, len(text), max_block_size)]
    
    interesting_segments = []
    
    # Отображаем прогресс при обработке текста
    for i, block in enumerate(tqdm(text_blocks, desc="Summarizing Text")):
        # Проверяем блок на наличие текста
        if not block.strip():
            print(f"Блок {i} пуст, пропускаем...")
            continue
        
        try:
            # Если блок слишком короткий, пропускаем
            if len(block) < 50:
                print(f"Блок {i} слишком короткий, пропускаем...")
                continue
            
            summary = summarizer(block, max_length=150, min_length=30, do_sample=False)
            interesting_segments.append(summary[0]['summary_text'])
        except Exception as e:
            print(f"Ошибка суммаризации блока {i}: {e}")
            print(f"Проблемный блок: {block}")
            continue  # Продолжаем, даже если какой-то блок вызывает ошибку
    
    return interesting_segments[:num_segments]


# Функция для генерации названия файла из текста
def generate_filename(text):
    # Оставляем только алфавитные символы и цифры, убираем все лишнее
    clean_text = re.sub(r'\W+', ' ', text).strip()
    # Ограничим название файла первыми несколькими словами
    filename = "_".join(clean_text.split()[:5])
    return filename[:50]  # Ограничим длину названия файла 50 символами

# Функция для нарезки видео с ограничением длины и созданием осмысленных названий файлов
def cut_video(video_path, segments, num_clips=12):
    max_clip_length = 120  # Максимальная длина клипа (в секундах)
    min_clip_length = 40  # Минимальная длина клипа (в секундах)
    
    total_duration = sum([seg['end'] - seg['start'] for seg in segments])
    avg_clip_length = total_duration // num_clips

    current_clip = []
    total_clips = []
    
    for i, segment in tqdm(enumerate(segments), desc="Processing Clips"):
        start_time = segment['start']
        end_time = segment['end']
        duration = end_time - start_time
        
        # Если текущий сегмент слишком короткий, добавляем следующий
        if duration < min_clip_length:
            current_clip.append(segment)
        else:
            # Заканчиваем текущий клип, если он превышает максимальную длину
            if sum([seg['end'] - seg['start'] for seg in current_clip]) > max_clip_length:
                total_clips.append(current_clip)
                current_clip = [segment]
            else:
                current_clip.append(segment)
        
        # Если у нас есть нужное количество клипов, выходим
        if len(total_clips) >= num_clips:
            break
    
    # Если остались необработанные клипы
    if current_clip:
        total_clips.append(current_clip)
    
    for i, clip_segments in enumerate(total_clips):
        start_time = clip_segments[0]['start']
        end_time = clip_segments[-1]['end']
        summary_text = " ".join([seg['text'] for seg in clip_segments])
        
        # Генерируем название файла
        filename = generate_filename(summary_text)
        output_file = f"{filename}_clip_{i}.mp4"
        
        # Вырезаем видео клип
        ffmpeg_extract_subclip(video_path, start_time, end_time, targetname=output_file)
        print(f"Клип сохранен как {output_file}")

# Основная функция обработки видео
def process_video(video_path):
    # 1. Извлечение аудио из видео
    print("Извлечение аудио...")
    audio_path = extract_audio(video_path)
    
    # 2. Транскрибирование речи с прогрессом
    print("Транскрибирование аудио...")
    text, segments = transcribe_audio(audio_path)
    
    # 3. Выбор интересных моментов с учётом прогресса
    print("Выбор интересных моментов...")
    interesting_segments = select_interesting_segments(text, 10)  # Убираем 10 сегментов текста для анализа
    
    # 4. Нарезка видео по интересным сегментам с прогрессом
    print("Нарезка видео...")
    cut_video(video_path, segments)

# Пример использования
process_video("interview.mp4")
