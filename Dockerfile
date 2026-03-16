FROM python:3.14
RUN mkdir /app
WORKDIR /app/
ADD . /app/
RUN pip install flask
CMD ["python", "/app/fib.py"]
