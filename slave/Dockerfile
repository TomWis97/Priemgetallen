FROM alpine
RUN apk update && \
    apk add python3 py3-requests
COPY slave.py /slave.py
ENV MASTERADDRESS="http://localhost:5000"
CMD /slave.py
