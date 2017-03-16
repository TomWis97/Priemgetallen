FROM alpine
RUN apk update && \
    apk add python3 py3-requests
COPY slave.py /slave.py
CMD /slave.py
