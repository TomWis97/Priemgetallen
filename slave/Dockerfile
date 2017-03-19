FROM alpine
RUN apk update && \
    apk add python3 py3-requests && \
    adduser -S slave
USER slave
COPY slave.py /slave.py
ENV MASTERADDRESS="http://localhost:5000"
CMD python3 slave.py
