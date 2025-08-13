FROM python:3.9-slim
WORKDIR /source
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["sh", "-c", "if [ \"$FLASK_ENV\" = \"production\" ]; then gunicorn -w 3 --timeout 30 --error-logfile - -b 0.0.0.0:5000 app.main:app; else python run.py; fi"]