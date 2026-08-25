FROM python:3.12-alpine
WORKDIR /app
COPY app.py /app/app.py
COPY templates /app/templates
ENV PYTHONUNBUFFERED=1
EXPOSE 3000
USER nobody
CMD ["python", "/app/app.py"]
