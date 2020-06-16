FROM alpine

ADD . /slate

RUN ["apk", "add", "python3"]

RUN ["apk", "add", "python3-tkinter"]

CMD ["cd", "slate"]