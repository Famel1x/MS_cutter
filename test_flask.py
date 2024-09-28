from moviepy.editor import VideoFileClip
import cv2

def crop_to_face(video_path, output_path):
    video = VideoFileClip(video_path)

    # Загружаем каскад для обнаружения лиц
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Обрабатываем каждый кадр видео
    def process_frame(frame):
        # Преобразуем кадр в черно-белое изображение
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

        # Обнаруживаем лица на кадре
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Если найдено лицо, обрезаем кадр так, чтобы лицо было в центре
        if len(faces) > 0:
            (x, y, w, h) = faces[0]
            face_center_x = x + w // 2
            face_center_y = y + h // 2

            # Обрезаем кадр по координатам (x1, y1, x2, y2)
            # где (x1, y1) - координаты верхнего левого угла,
            # а (x2, y2) - координаты нижнего правого угла
            cropped_frame = frame[face_center_y - 240:face_center_y + 240, face_center_x - 320:face_center_x + 320]

            return cropped_frame

        # Если не найдено лицо, возвращаем исходный кадр
        return frame

    # Обрезаем видео по координатам
    cropped_video = video.fl_image(process_frame)

    # Сохраняем обрезанное видео в файл
    cropped_video.write_videofile(output_path)

crop_to_face("output_clips/clip_1.mp4",  "cropped_interview.mp4")
