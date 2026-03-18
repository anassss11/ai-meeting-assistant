@echo off
set KMP_DUPLICATE_LIB_OK=TRUE
uvicorn main:app --host 0.0.0.0 --port 8000 --reload