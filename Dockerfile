FROM python:3.8.13-bullseye

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

CMD ["python", "-m" , "flask", "run", "--host=0.0.0.0", "--port=8080"]