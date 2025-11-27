import os
import grpc
from protos import model_pb2, model_pb2_grpc

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = model_pb2_grpc.PredictionServiceStub(channel)

    # Health check
    health_response = stub.Health(model_pb2.HealthRequest())
    print("Health:", health_response)

    # Predict
    predict_request = model_pb2.PredictRequest(features=[5.1, 3.5, 1.4, 0.2])  # Пример для Iris
    predict_response = stub.Predict(predict_request)
    print("Predict:", predict_response)

if __name__ == "main":
    run()