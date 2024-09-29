from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import whisper
import os

# Логирование
def log_stage(stage):
    print(f"[{stage}] Этап обработки")

# 1. Извлечение аудио из видео и сохранение его в папку "output"
def extract_audio(video_path):
    log_stage("Извлечение аудио из видео")

    # Создание папки "output", если её нет
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Генерация пути для аудиофайла в папке "output"
    audio_filename = os.path.basename(video_path).replace('.mp4', '.wav')  # Имя файла
    audio_path = os.path.join(output_dir, audio_filename)  # Путь к аудиофайлу

    # Проверка существования видеофайла
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Видео не найдено: {video_path}")

    # Извлечение аудио
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)

    # Проверка успешного создания аудиофайла
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Не удалось создать аудиофайл: {audio_path}")

    print(f"Создан аудиофайл: {audio_path}")
    
    return audio_path  # Возвращаем путь к аудиофайлу


# 3. Распознавание речи (поддержка русского языка)
def transcribe_audio(audio_path):
    log_stage(f"Распознавание речи. Путь к аудио: {audio_path}")
    model = whisper.load_model("small")
    result = model.transcribe(audio_path, language="ru")
    return result['text'], result['segments']

# 5. Нарезка видео по сегментам и создание субтитров
def cut_video_and_generate_subtitles(video_path, transcribed_segments):
    log_stage("Нарезка видео и генерация субтитров")

    # Создание папок для сохранения нарезанных видео и субтитров
    output_clips_dir = "output_clips"
    subtitles_dir = "subtitles"
    if not os.path.exists(output_clips_dir):
        os.makedirs(output_clips_dir)
    if not os.path.exists(subtitles_dir):
        os.makedirs(subtitles_dir)

    video = VideoFileClip(video_path)
    
    clip_count = 0

    for seg in transcribed_segments:
        start = seg['start']
        end = seg['end']
        text_segment = seg['text']

        # Генерация имени для нарезанного клипа
        clip_count += 1
        clip_filename = os.path.join(output_clips_dir, f"clip_{clip_count}.mp4")
        subtitle_filename = os.path.join(subtitles_dir, f"clip_{clip_count}.srt")

        # Нарезка видеофрагмента
        ffmpeg_extract_subclip(video_path, start, end, targetname=clip_filename)

        # Создание файла субтитров
        with open(subtitle_filename, 'w', encoding='utf-8') as f:
            f.write(f"1\n{start} --> {end}\n{text_segment}\n")

        print(f"Создан клип: {clip_filename} и субтитры: {subtitle_filename}")

    print("Нарезка и генерация субтитров завершена.")


# 6. Основная функция обработки видео
def process_video(video_path):
    log_stage("Запуск обработки видео")

    # 1. Извлечение аудио и сохранение его в папке "output"
    audio_path = extract_audio(video_path)

    # 3. Распознавание речи и сегментов
    log_stage(f"Распознавание речи. Путь к аудио: {audio_path}")
    transcribed_text, transcribed_segments = transcribe_audio(audio_path)
    
    # 5. Нарезка видео по сегментам и создание субтитров
    cut_video_and_generate_subtitles(video_path, transcribed_segments)

    log_stage("Завершение обработки видео")


# Пример использования:
if __name__ == "__main__":
    video_path = "interview.mp4"  # Укажите путь к вашему видео
    process_video(video_path)
