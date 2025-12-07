import os
import pickle
import logging
import joblib
from concurrent import futures

import grpc
from protos import model_pb2, model_pb2_grpc

# Конфигурация логирования
logger = logging.getLogger(__name__)

MODEL_PATH = os.getenv("MODEL_PATH", "models/model.pkl")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0.0")

# Загрузка модели
try:
    model = joblib.load(MODEL_PATH)
    logger.info(f"Model loaded successfully using joblib")
except Exception as e:
    logger.error(f"Failed to load with joblib: {e}")
    # Пробуем pickle как запасной вариант
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f, encoding='latin1')
    except Exception as e2:
        logger.error(f"Failed to load with pickle too: {e2}")
        model = None


class PredictionService(model_pb2_grpc.PredictionServiceServicer):

    def Health(self, request, context):
        return model_pb2.HealthResponse(
            status="ok",
            model_version=MODEL_VERSION
        )

    def Predict(self, request, context):
        if model is None:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details("Model not loaded")
            return model_pb2.PredictResponse()

        try:
            features = [request.features]
            prediction = model.predict(features)[0]
            probabilities = model.predict_proba(features)[0]
            confidence = max(probabilities)

            return model_pb2.PredictResponse(
                prediction=str(int(prediction)),
                confidence=float(confidence),
                model_version=MODEL_VERSION
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return model_pb2.PredictResponse()


def serve():
    port = os.getenv("PORT", "50051")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_pb2_grpc.add_PredictionServiceServicer_to_server(PredictionService(), server)
    server.add_insecure_port(f"[::]:{port}")
    logger.info(f"Starting gRPC server on port {port}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()