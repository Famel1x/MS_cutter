import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from tqdm import tqdm
import re

def split_text_into_sentences(text):
    """
    Разделяет текст на предложения.
    """
    sentences = re.split(r'(?<=[.!?]) +', text)
    return sentences

def clean_text(text):
    """
    Очищает текст от ненужных символов.
    """
    # Удаляем все не-русские и не-английские символы, кроме основных знаков препинания
    clean_text = re.sub(r'[^а-яА-ЯёЁa-zA-Z0-9\s,.!?]', '', text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def add_subtitles_to_video(video_path, subtitle_text, output_path, fontsize=24, color='white', bg_color='black', margin=10):
    """
    Добавляет субтитры к видео.

    :param video_path: Путь к исходному видео.
    :param subtitle_text: Текст субтитров.
    :param output_path: Путь для сохранения видео с субтитрами.
    :param fontsize: Размер шрифта субтитров.
    :param color: Цвет текста субтитров.
    :param bg_color: Цвет фона субтитров.
    :param margin: Отступ от нижней части видео.
    """
    # Разделяем текст на предложения
    sentences = split_text_into_sentences(subtitle_text)
    num_sentences = len(sentences)
    
    # Загружаем видео
    video = VideoFileClip(video_path)
    duration = video.duration

    if num_sentences == 0:
        print(f"No subtitles found for {video_path}")
        return

    # Рассчитываем длительность каждого субтитра
    subtitle_duration = duration / num_sentences

    # Создаем текстовые клипы для субтитров
    subtitle_clips = []
    for i, sentence in enumerate(sentences):
        start = i * subtitle_duration
        end = (i + 1) * subtitle_duration

        txt_clip = (TextClip(sentence, fontsize=fontsize, color=color, font="Arial", method='caption', size=(video.w*0.8, None))
                    .set_position(('center', video.h - fontsize - margin))
                    .set_start(start)
                    .set_duration(subtitle_duration)
                    .on_color(color=bg_color, col_opacity=0.6, padding=10))
        
        subtitle_clips.append(txt_clip)
    
    # Объединяем видео и субтитры
    final = CompositeVideoClip([video, *subtitle_clips])

    # Сохраняем видео с субтитрами
    final.write_videofile(output_path, codec="libx264", audio_codec="aac")

def process_videos_with_subtitles(videos_dir, subtitles_dir, output_dir):
    """
    Обрабатывает все видео в директории, добавляя к ним субтитры.

    :param videos_dir: Директория с видео.
    :param subtitles_dir: Директория с текстовыми файлами субтитров (с тем же именем, но .txt).
    :param output_dir: Директория для сохранения видео с субтитрами.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    video_files = [f for f in os.listdir(videos_dir) if f.endswith(('.mp4', '.avi', '.mov', '.mkv'))]
    
    for video_file in tqdm(video_files, desc="Adding subtitles to videos"):
        video_path = os.path.join(videos_dir, video_file)
        subtitle_file = os.path.splitext(video_file)[0] + '.txt'
        subtitle_path = os.path.join(subtitles_dir, subtitle_file)
        
        if not os.path.exists(subtitle_path):
            print(f"Subtitle file not found for {video_file}, skipping.")
            continue
        
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            subtitle_text = f.read()
        
        output_path = os.path.join(output_dir, f"subtitled_{video_file}")
        add_subtitles_to_video(video_path, subtitle_text, output_path)

if __name__ == "__main__":
    # Пример использования
    videos_directory = "clips"            # Директория с видео файлами
    subtitles_directory = "subtitles"      # Директория с текстовыми файлами субтитров
    output_directory = "clips_with_subtitles"  # Директория для сохранения видео с субтитрами

    process_videos_with_subtitles(videos_directory, subtitles_directory, output_directory)
