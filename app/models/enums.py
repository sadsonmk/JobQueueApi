import enum


class JobType(str, enum.Enum):
    CSV_PROCESS = "csv_process"
    TEXT_ANALYZE = "text_analyze"
    GENERATE_REPORT = "generate_report"
    ALWAYS_FAIL = "always_fail"      # for testing retry behavior


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"