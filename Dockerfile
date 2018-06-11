FROM python:3.6-alpine

# Install dependencies for numpy
RUN apk --no-cache --update-cache add gcc musl-dev && \
      ln -s /usr/include/locale.h /usr/include/xlocale.h

WORKDIR /app

ADD requirements.txt .
RUN pip install -r requirements.txt

ADD . .

ENTRYPOINT ["python"]
CMD ["exporter.py"]
