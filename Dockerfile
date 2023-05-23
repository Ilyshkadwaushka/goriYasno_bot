FROM python:3.10.5

EXPOSE 8000

# Environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir goriyasno
WORKDIR /goriyasno

COPY requirements.txt .

RUN pip install --upgrade pip &&  \
    pip install -r requirements.txt

COPY . .