FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
COPY token.pickle ./
RUN mkdir downloaded \
 && pip install --no-cache-dir -r requirements.txt
COPY . .
CMD [ "python", "./process.py" ]

