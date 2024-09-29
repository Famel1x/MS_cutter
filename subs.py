import moviepy.editor as mp
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.VideoClip import TextClip
import whisper
import pysrt
import os


# Функция для извлечения аудио из видео
def extract_audio(video_path):
    video = mp.VideoFileClip(video_path)
    audio_path = video_path.replace('.mp4', '.wav')
    video.audio.write_audiofile(audio_path)
    return audio_path

# Функция для распознавания речи с помощью Whisper и генерации субтитров
def transcribe_audio_to_srt(audio_path, srt_output_path):
    model = whisper.load_model("small")
    result = model.transcribe(audio_path, language="ru")
    segments = result['segments']

    # Создаём файл .srt
    with open(srt_output_path, "w", encoding="utf-8") as srt_file:
        for i, seg in enumerate(segments):
            start = seg['start']
            end = seg['end']
            text = seg['text']

            # Преобразование времени в формат SRT
            def format_time(seconds):
                hours, remainder = divmod(seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                milliseconds = int((seconds - int(seconds)) * 1000)
                return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02},{milliseconds:03}"

            srt_file.write(f"{i + 1}\n")
            srt_file.write(f"{format_time(start)} --> {format_time(end)}\n")
            srt_file.write(f"{text}\n\n")

    print(f"Субтитры сохранены в: {srt_output_path}")

# Функция для чтения субтитров из SRT файла
def read_subtitles(srt_file):
    subtitles = pysrt.open(srt_file)
    
    # Возвращаем список пар (время начала, текст)
    return [(sub.start.ordinal / 1000, sub.text) for sub in subtitles]

# Функция для создания клипа с отображением субтитров
def add_subtitles_to_video(video_path, srt_file, output_path):
    # Чтение видеофайла
    video = mp.VideoFileClip(video_path)

    # Чтение субтитров
    subtitles = read_subtitles(srt_file)

    # Проверка, пуст ли список субтитров
    if not subtitles:
        raise ValueError("Список субтитров пуст. Проверьте файл .srt.")

    # Функция для создания текстового клипа для каждого субтитра
    def subtitle_generator(txt):
        return TextClip(txt, font='Arial', fontsize=40, color='white', bg_color='black').on_color(col_opacity=0.6)

    # Создание клипа субтитров (используем только время начала и текст)
    subs = SubtitlesClip(subtitles)

    # Наложение субтитров на видео
    video_with_subs = mp.CompositeVideoClip([video, subs.set_position(('center', 'bottom'))])

    # Сохранение нового видео
    video_with_subs.write_videofile(output_path, codec='libx264', fps=video.fps)
    print(f"Видео с субтитрами сохранено в: {output_path}")

# Основная функция: извлекаем аудио, распознаём речь, создаём субтитры и накладываем их на видео
def process_video_with_subtitles(video_path):
    audio_path = extract_audio(video_path)
    
    # Путь для временного SRT файла
    srt_output_path = video_path.replace('.mp4', '.srt')

    # Генерация субтитров
    transcribe_audio_to_srt(audio_path, srt_output_path)

    # Создание видео с наложенными субтитрами
    output_video_path = video_path.replace('.mp4', '_with_subtitles.mp4')
    add_subtitles_to_video(video_path, srt_output_path, output_video_path)

    # Удаление временного аудио файла
    if os.path.exists(audio_path):
        os.remove(audio_path)

    # Удаление временного файла субтитров
    if os.path.exists(srt_output_path):
        os.remove(srt_output_path)

# Пример использования:
if __name__ == "__main__":
    video_path = "output_clips\clip_1.mp4"  # Укажите путь к вашему видео
    process_video_with_subtitles(video_path)
