import os
from moviepy.editor import VideoFileClip, concatenate_videoclips
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from pyannote.audio import Pipeline
import whisper
import spacy
from tqdm import tqdm

# Логирование
def log_stage(stage):
    print(f"[{stage}] Этап обработки")

# 1. Извлечение аудио из видео и сохранение его в папку "output"
def extract_audio(video_path):
    log_stage("Извлечение аудио из видео")

    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    audio_filename = os.path.basename(video_path).replace('.mp4', '.wav')
    audio_path = os.path.join(output_dir, audio_filename)

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Видео не найдено: {video_path}")

    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Не удалось создать аудиофайл: {audio_path}")

    print(f"Создан аудиофайл: {audio_path}")
    
    return audio_path

# 3. Распознавание речи (поддержка русского языка)
def transcribe_audio(audio_path):
    log_stage(f"Распознавание речи. Путь к аудио: {audio_path}")
    model = whisper.load_model("small")
    result = model.transcribe(audio_path, language="ru")
    return result['text'], result['segments']

# 4. Определение, является ли сегмент вопросом
def is_question(text):
    doc = nlp(text)
    question_words = {"что", "почему", "как", "зачем", "когда", "где", "кто", "сколько", "какой"}
    return any(token.text.lower() in question_words for token in doc)

# 5. Нарезка видео по сегментам вопрос-ответ
def cut_video(video_path, question_answer_segments):
    log_stage("Нарезка видео по сегментам вопрос-ответ")

    output_dir = "output_clips"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    video = VideoFileClip(video_path)
    
    clip_count = 0
    i = 0
    total_segments = len(question_answer_segments)

    while i < total_segments:
        start = question_answer_segments[i][0]
        label = question_answer_segments[i][2]
        
        if label != "question":
            i += 1
            continue

        end = question_answer_segments[i][1]
        j = i + 1
        while j < total_segments:
            next_label = question_answer_segments[j][2]
            next_start = question_answer_segments[j][0]
            
            if next_label == "question":
                duration = next_start - start
                if duration >= 10:
                    end = next_start
                    break
                else:
                    end = question_answer_segments[j][1]
            else:
                end = question_answer_segments[j][1]

            if end - start > 120:
                end = start + 120
                break

            j += 1

        final_duration = end - start

        if final_duration <= 20 and j < total_segments:
            next_segment_duration = question_answer_segments[j][1] - question_answer_segments[j][0]
            if next_segment_duration <= 20:
                end = question_answer_segments[j][1]
                final_duration = end - start
                j += 1

        if final_duration < 10:
            print(f"Пропуск фрагмента: слишком короткий ({final_duration:.2f} секунд)")
        else:
            clip_count += 1
            output_filename = os.path.join(output_dir, f"clip_{clip_count}.mp4")

            print(f"Создание клипа {clip_count}: с {start:.2f} до {end:.2f} секунд (длительность {final_duration:.2f} секунд)")
            ffmpeg_extract_subclip(video_path, start, end, targetname=output_filename)

        i = j

    print("Нарезка завершена.")

# 6. Объединение нарезанных клипов
def combine_clips(output_dir, min_length=40, max_length=120):
    log_stage("Объединение клипов")
    
    video_files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
    video_files.sort()

    current_clips = []
    current_duration = 0
    clip_counter = 1

    for video_file in tqdm(video_files, desc="Объединение видео"):
        video_path = os.path.join(output_dir, video_file)
        clip = VideoFileClip(video_path)
        clip_duration = clip.duration

        if current_duration + clip_duration <= max_length:
            current_clips.append(clip)
            current_duration += clip_duration
        else:
            if current_duration >= min_length:
                combined_clip = concatenate_videoclips(current_clips)
                combined_clip.write_videofile(os.path.join(output_dir, f"combined_clip_{clip_counter}.mp4"), codec="libx264", audio_codec="aac")
                combined_clip.close()
                clip_counter += 1

            current_clips = [clip]
            current_duration = clip_duration

    if current_clips and current_duration >= min_length:
        combined_clip = concatenate_videoclips(current_clips)
        combined_clip.write_videofile(os.path.join(output_dir, f"combined_clip_{clip_counter}.mp4"), codec="libx264", audio_codec="aac")
        combined_clip.close()

    print("Объединение клипов завершено.")

# 7. Основная функция обработки видео
def process_video(video_path):
    log_stage("Запуск обработки видео")

    global nlp
    log_stage("Загрузка русской модели NLP")
    nlp = spacy.load("ru_core_news_sm")

    audio_path = extract_audio(video_path)
    _, transcribed_segments = transcribe_audio(audio_path)

    log_stage("Классификация сегментов на вопросы и ответы")
    question_answer_segments = []
    for seg in transcribed_segments:
        start = seg['start']
        end = seg['end']
        text_segment = seg['text']

        if is_question(text_segment):
            label = "question"
        else:
            label = "answer"

        question_answer_segments.append((start, end, label))

    cut_video(video_path, question_answer_segments)

    # Объединяем нарезанные клипы
    combine_clips("output_clips")

    log_stage("Завершение обработки видео")

# Пример использования:
if __name__ == "__main__":
    video_path = "interview.mp4"  # Укажите путь к вашему видео
    process_video(video_path)
