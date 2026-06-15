from ultralytics import YOLO
import time

start = time.time()

# Smallest YOLOv11 classification model
model = YOLO("yolo11n-cls.pt")

model.train(
    data=r"C:\STUDY\IoT\Dataset",
    epochs=20,
    imgsz=224,
    batch=16,
    workers=4,
    verbose=True
)

end = time.time()

print(f"\nTraining time: {end - start:.2f} seconds")