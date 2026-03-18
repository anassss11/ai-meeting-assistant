@echo off
set KMP_DUPLICATE_LIB_OK=TRUE
echo Starting server with no timeout configuration...
python -m uvicorn main:app --host 127.0.0.1 --port 8000