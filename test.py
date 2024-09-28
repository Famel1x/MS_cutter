from moviepy.editor import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from pyannote.audio import Pipeline
import whisper
import spacy
import os
import torch


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


# 2. Разделение речи на спикеров
def diarize_audio(audio_path):
    try:
        # Попытка загрузить модель
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization",use_auth_token="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")
        if pipeline is None:
            raise ValueError("Модель не загружена. Проверьте корректность пути к модели.")
    except Exception as e:
        print(f"Ошибка при загрузке модели pyannote: {e}")
        return None

    try:
        diarization = pipeline(audio_path)
        return [(turn.start, turn.end, speaker) for turn, _, speaker in diarization.itertracks(yield_label=True)]
    except Exception as e:
        print(f"Ошибка во время ра зделения речи: {e}")
        return None

# 3. Распознавание речи (поддержка русского языка)
def transcribe_audio(audio_path):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    log_stage(f"Распознавание речи. Путь к аудио: {audio_path}")
    model = whisper.load_model("small", device=device)
    result = model.transcribe(audio_path, language="ru")
    return result['text'], result['segments']

# 4. Определение, является ли сегмент вопросом
def is_question(text):
    doc = nlp(text)
    # Простая проверка на наличие вопросительных слов (что, почему, как, зачем и т.д.)
    question_words = {"что", "почему", "как", "зачем", "когда", "где", "кто", "сколько", "какой"}
    return any(token.text.lower() in question_words for token in doc)



from moviepy.editor import VideoFileClip
from moviepy.video.fx.all import crop

def cut_video(video_path, question_answer_segments):
    log_stage("Нарезка видео по сегментам вопрос-ответ")

    # Создание папки для сохранения нарезанных видео
    output_dir = "output_clips"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    video = VideoFileClip(video_path)
    
    # Обрезаем видео до вертикального формата (9:16), например, до 1080x1920
    # Получаем ширину и высоту оригинального видео
    video_width, video_height = video.size
    target_width = 1080  # Целевая ширина для вертикального видео
    target_height = 1920  # Целевая высота для вертикального видео

    # Обрезаем по центру, чтобы сохранить вертикальное видео
    vertical_video = crop(
        video,
        width=target_width,  # Ширина после обрезки
        height=target_height,  # Высота после обрезки
        x_center=video_width / 2,  # Центрируем по горизонтали
        y_center=video_height / 2  # Центрируем по вертикали
    )
    
    clip_count = 0
    i = 0
    total_segments = len(question_answer_segments)

    while i < total_segments:
        start = question_answer_segments[i][0]  # Начало текущего сегмента (вопроса)
        label = question_answer_segments[i][2]
        
        # Убедимся, что это сегмент с вопросом
        if label != "question":
            i += 1
            continue

        # Начинаем искать окончание сегмента (до следующего вопроса)
        end = question_answer_segments[i][1]  # Изначально конец текущего сегмента
        j = i + 1
        while j < total_segments:
            next_label = question_answer_segments[j][2]
            next_start = question_answer_segments[j][0]
            
            # Проверяем, если следующий сегмент — вопрос или ответ, объединяем их
            if next_label == "question" or next_label == "answer":
                end = question_answer_segments[j][1]  # Расширяем текущий клип

            # Ограничение на длину в 120 секунд
            if end - start > 120:
                end = start + 120  # Ограничиваем длину клипа 120 секундами
                break

            # Если длина клипа превысила 40 секунд, завершаем текущий клип
            if end - start >= 40:
                break

            j += 1

        # Проверяем окончательную длину фрагмента
        final_duration = end - start

        # Если длина клипа меньше 40 секунд, пропускаем его
        if final_duration < 40:
            print(f"Пропуск фрагмента: слишком короткий ({final_duration:.2f} секунд)")
        else:
            # Генерация имени для нарезанного клипа
            clip_count += 1
            output_filename = os.path.join(output_dir, f"clip_{clip_count}.mp4")

            # Нарезка и обрезка видеофрагмента
            print(f"Создание клипа {clip_count}: с {start:.2f} до {end:.2f} секунд (длительность {final_duration:.2f} секунд)")
            clip = vertical_video.subclip(start, end)  # Нарезаем клип
            clip.write_videofile(output_filename, codec="libx264", audio_codec="aac")

        i = j  # Переходим к следующему сегменту

    print("Нарезка завершена.")

def delete_small_files(directory, keep_largest=12):
    # Получаем список всех .mp4 файлов в директории
    mp4_files = [f for f in os.listdir(directory) if f.endswith('.mp4')]
    
    # Получаем полный путь к каждому файлу
    mp4_files_with_paths = [os.path.join(directory, f) for f in mp4_files]
    
    # Сортируем файлы по размеру в порядке убывания (от большего к меньшему)
    mp4_files_with_paths.sort(key=lambda x: os.path.getsize(x), reverse=True)
    
    # Оставляем только 12 самых больших файлов
    files_to_keep = mp4_files_with_paths[:keep_largest]
    
    # Файлы, которые нужно удалить
    files_to_delete = mp4_files_with_paths[keep_largest:]
    
    # Удаляем файлы
    for file in files_to_delete:
        try:
            os.remove(file)
            print(f"Удалён файл: {file}")
        except Exception as e:
            print(f"Не удалось удалить файл {file}: {e}")


# 6. Основная функция обработки видео
def process_video(video_path, count,directory = 'output_clips'):
    log_stage("Запуск обработки видео")

    # Загрузка русской языковой модели SpaCy
    global nlp
    log_stage("Загрузка русской модели NLP")
    nlp = spacy.load("ru_core_news_sm")

    # 1. Извлечение аудио и сохранение его в папке "output"
    audio_path = extract_audio(video_path)

    # 2. Разделение речи на спикеров
    diarization_segments = diarize_audio(audio_path)

    # 3. Распознавание речи и сегментов
    log_stage(f"Распознавание речи. Путь к аудио: {audio_path}")
    _, transcribed_segments = transcribe_audio(audio_path)
    
    # 4. Классификация сегментов на вопросы и ответы
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

    # 5. Нарезка видео по классифицированным сегментам
    cut_video(video_path, question_answer_segments)
    delete_small_files(directory,  count)

    log_stage("Завершение обработки видео")


# Пример использования:
if __name__ == "__main__":
    video_path = "interview.mp4"  # Укажите путь к вашему видео
    directory = 'output_clips'
    process_video(video_path, 14, directory = 'output_clips')
