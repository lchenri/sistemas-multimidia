import numpy as np
import dlib
import cv2
from keras.models import load_model
from imutils import face_utils
from django.shortcuts import render
import os
import csv
import time
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import StopConsumer
import asyncio
from typing import Optional, Tuple

# Configurações e constantes
DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMOTIONS = ["angry", "disgust", "scared", "happy", "sad", "surprised", "neutral"]
CSV_FILE_PATH = os.path.join(DIR, 'server', 'static', 'server', 'data', 'fps.csv')

# Configurações dos modelos
MODELS_DIR = os.path.join(DIR, 'server', 'models')
SHAPE_PREDICTOR_PATH = os.path.join(MODELS_DIR, 'shape_predictor_68_face_landmarks.dat')
EMOTION_MODEL_PATH = os.path.join(MODELS_DIR, '_mini_XCEPTION.102-0.66.hdf5')

# Configurações de processamento
EMOTION_INPUT_SIZE = (64, 64)
FPS_DISPLAY_POSITION = (310, 40)
EMOTION_DISPLAY_POSITION = (20, 40)
TEXT_FONT = cv2.FONT_HERSHEY_SIMPLEX
TEXT_SCALE = 0.5
TEXT_COLOR = (54, 161, 255)
TEXT_THICKNESS = 1


class ModelManager:
    """Gerencia o carregamento e acesso aos modelos de ML"""

    def __init__(self):
        self.detector = None
        self.predictor = None
        self.emotion_classifier = None
        self._load_models()

    def _load_models(self):
        """Carrega os modelos de ML"""
        try:
            self.detector = dlib.get_frontal_face_detector()
            self.predictor = dlib.shape_predictor(SHAPE_PREDICTOR_PATH)
            self.emotion_classifier = load_model(EMOTION_MODEL_PATH, compile=False)
        except Exception as e:
            print(f"Erro ao carregar modelos: {e}")
            raise


class FacialLandmarkExtractor:
    """Extrai e gerencia landmarks faciais"""

    def __init__(self):
        # Define os índices para extrair as partes do rosto dos 68 pontos detectados
        self.landmark_indices = {
            'left_eyebrow': face_utils.FACIAL_LANDMARKS_IDXS["right_eyebrow"],
            'right_eyebrow': face_utils.FACIAL_LANDMARKS_IDXS["left_eyebrow"],
            'mouth': face_utils.FACIAL_LANDMARKS_IDXS["mouth"],
            'inner_mouth': face_utils.FACIAL_LANDMARKS_IDXS["inner_mouth"],
            'left_eye': face_utils.FACIAL_LANDMARKS_IDXS["left_eye"],
            'right_eye': face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
        }

    def extract_landmarks(self, shape):
        """Extrai todos os landmarks relevantes"""
        landmarks = {}
        for name, (start, end) in self.landmark_indices.items():
            landmarks[name] = shape[start:end]
        return landmarks

    def create_hulls(self, landmarks):
        """Cria convex hulls para os landmarks"""
        hulls = {}
        for name, points in landmarks.items():
            hulls[f"{name}_hull"] = cv2.convexHull(points)
        return hulls


class EmotionDetector:
    """Detecta emoções em rostos"""

    def __init__(self, emotion_classifier):
        self.emotion_classifier = emotion_classifier

    def detect_emotion(self, face_rect, frame) -> Optional[str]:
        """
        Detecta emoção em um rosto.

        Args:
            face_rect: Retângulo do rosto detectado
            frame: Frame de vídeo em escala de cinza

        Returns:
            String da emoção detectada ou None se erro
        """
        try:
            x, y, w, h = face_utils.rect_to_bb(face_rect)
            roi = cv2.resize(frame[y:y + h, x:x + w], EMOTION_INPUT_SIZE)
            roi = roi / 255.0
            roi = np.array([roi])

            predictions = self.emotion_classifier.predict(roi)[0]
            emotion = EMOTIONS[predictions.argmax()]

            return emotion
        except Exception as e:
            print(f"Erro na detecção de emoção: {e}")
            return None


class FPSCounter:
    """Calcula FPS em tempo real"""

    def __init__(self):
        self.fps = 0
        self.prev_time = 0

    def update(self):
        """Atualiza o contador de FPS"""
        try:
            current_time = time.time()
            if self.prev_time > 0:
                self.fps = int(1 / (current_time - self.prev_time))
            self.prev_time = current_time
        except ZeroDivisionError:
            self.fps = 0

    def get_fps(self) -> int:
        """Retorna o FPS atual"""
        return self.fps


class CSVManager:
    """Gerencia operações do arquivo CSV"""

    @staticmethod
    def clear_fps_csv():
        """Limpa o arquivo CSV de FPS"""
        try:
            with open(CSV_FILE_PATH, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["FPS"])
        except Exception as e:
            print(f"Erro ao limpar CSV: {e}")


class FrameProcessor:
    """Processa frames de vídeo"""

    def __init__(self, model_manager):
        self.model_manager = model_manager
        self.landmark_extractor = FacialLandmarkExtractor()
        self.emotion_detector = EmotionDetector(model_manager.emotion_classifier)
        self.fps_counter = FPSCounter()

    def process_frame(self, frame) -> Tuple[np.ndarray, Optional[str], int]:
        """
        Processa um frame completo.

        Args:
            frame: Frame de vídeo colorido

        Returns:
            Tuple com (frame_processado, emoção_detectada, fps)
        """
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detections = self.model_manager.detector(gray_frame, 0)

        emotion = None

        if detections:
            detection = detections[0]

            # Extrai landmarks
            shape = self.model_manager.predictor(frame, detection)
            shape_np = face_utils.shape_to_np(shape)

            # Processa landmarks
            landmarks = self.landmark_extractor.extract_landmarks(shape_np)
            hulls = self.landmark_extractor.create_hulls(landmarks)

            # Detecta emoção
            emotion = self.emotion_detector.detect_emotion(detection, gray_frame)

        # Atualiza FPS
        self.fps_counter.update()
        fps = self.fps_counter.get_fps()

        # Adiciona informações no frame
        self._add_text_to_frame(frame, fps, emotion)

        return frame, emotion, fps

    def _add_text_to_frame(self, frame, fps: int, emotion: Optional[str]):
        """Adiciona texto informativo no frame"""
        cv2.putText(frame, f"FPS: {fps}", FPS_DISPLAY_POSITION,
                    TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)

        if emotion:
            cv2.putText(frame, f"Emoção: {emotion}", EMOTION_DISPLAY_POSITION,
                        TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)


# Instância global dos modelos
model_manager = ModelManager()


def index(request):
    """View principal da aplicação"""
    return render(request, 'server/index.html')


class VideoStreamConsumer(AsyncWebsocketConsumer):
    """Consumer WebSocket para streaming de vídeo"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_processor = None
        self.loop = None
        self.frame_count = 0

    async def connect(self):
        """Conecta o WebSocket"""
        self.frame_count = 0
        self.loop = asyncio.get_running_loop()
        self.frame_processor = FrameProcessor(model_manager)
        await self.accept()

    async def disconnect(self, close_code):
        """Desconecta o WebSocket"""
        self.frame_count = 0
        CSVManager.clear_fps_csv()
        raise StopConsumer()

    async def receive(self, bytes_data):
        """Recebe e processa dados do WebSocket"""
        if not bytes_data:
            await self._handle_empty_data()
            return

        try:
            # Decodifica a imagem
            frame = await self.loop.run_in_executor(
                None,
                cv2.imdecode,
                np.frombuffer(bytes_data, dtype=np.uint8),
                cv2.IMREAD_COLOR
            )

            # Processa o frame
            processed_frame, emotion, fps = await self.loop.run_in_executor(
                None,
                self.frame_processor.process_frame,
                frame
            )

            self.frame_count += 1

            # Codifica e envia de volta
            await self._send_processed_frame(processed_frame)

        except Exception as e:
            print(f"Erro no processamento do frame: {e}")
            await self.close()

    async def _handle_empty_data(self):
        """Lida com dados vazios (desconexão)"""
        self.frame_count = 0
        CSVManager.clear_fps_csv()
        print('Conexão fechada')
        await self.close()

    async def _send_processed_frame(self, frame):
        """Envia o frame processado de volta"""
        try:
            # Codifica o frame
            _, buffer = await self.loop.run_in_executor(
                None,
                cv2.imencode,
                '.jpeg',
                frame
            )

            # Converte para base64
            b64_img = base64.b64encode(buffer).decode('utf-8')

            # Pequeno delay para não sobrecarregar
            # await asyncio.sleep(0.1)

            # Envia
            await self.send(b64_img)

        except Exception as e:
            print(f"Erro ao enviar frame: {e}")