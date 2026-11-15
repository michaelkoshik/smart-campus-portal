import json
import sys
import time
sys.path.insert(0, "api/generated")
import service_pb2
from google.protobuf.timestamp_pb2 import Timestamp

# 1. ормування ідентичного набору даних для CourseSummaryResponse (5 результатів тестів)
items_data = [
    {"test_id": f"7c9e6679-7425-40de-944b-e07fc1f90ae{i}", "test_title": f"одульний контроль {i}: рхітектурні стилі та шаблони", "score": 18.5 + i * 0.25, "status": 3, "seconds": 1763280000 + i * 3600}
    for i in range(1, 6)
]

json_payload = {
    "student_id": "550e8400-e29b-41d4-a716-446655440001",
    "course_id": "550e8400-e29b-41d4-a716-446655440000",
    "completed_tests_count": 5,
    "total_earned_points": 96.25,
    "max_possible_points": 100.0,
    "is_passing_threshold_met": True,
    "results": [
        {
            "test_id": x["test_id"],
            "test_title": x["test_title"],
            "score": x["score"],
            "status": "ATTEMPT_SYNC_STATUS_GRADED",
            "completed_at": "2026-11-16T09:00:00Z"
        }
        for x in items_data
    ]
}

# Серіалізація у компактний JSON (без пробілів)
json_bytes = json.dumps(json_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

# 2. Серіалізація у бінарний Protobuf (з використанням згенерованого service_pb2.py)
proto_msg = service_pb2.CourseSummaryResponse(
    student_id=json_payload["student_id"],
    course_id=json_payload["course_id"],
    completed_tests_count=json_payload["completed_tests_count"],
    total_earned_points=json_payload["total_earned_points"],
    max_possible_points=json_payload["max_possible_points"],
    is_passing_threshold_met=json_payload["is_passing_threshold_met"],
)

for x in items_data:
    ts = Timestamp(seconds=x["seconds"], nanos=0)
    proto_msg.results.add(
        test_id=x["test_id"],
        test_title=x["test_title"],
        score=x["score"],
        status=service_pb2.ATTEMPT_SYNC_STATUS_GRADED,
        completed_at=ts
    )

proto_bytes = proto_msg.SerializeToString()

# енчмарк швидкості 10 000 ітерацій серіалізації
t0 = time.perf_counter()
for _ in range(10000):
    json.dumps(json_payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
json_ms = (time.perf_counter() - t0) * 1000

t1 = time.perf_counter()
for _ in range(10000):
    proto_msg.SerializeToString()
proto_ms = (time.perf_counter() - t1) * 1000

ratio = len(json_bytes) / len(proto_bytes)
saving = (1 - len(proto_bytes) / len(json_bytes)) * 100

print(f"JSON (compact UTF-8) size : {len(json_bytes)} bytes")
print(f"Protobuf (binary) size    : {len(proto_bytes)} bytes")
print(f"Wire Efficiency ratio     : {ratio:.2f}x (economy: {saving:.1f}%)")
print(f"10k serializations time   : JSON = {json_ms:.2f} ms | Protobuf = {proto_ms:.2f} ms")
