FROM python:3
 
COPY requirements.txt /
COPY application.py /
RUN pip install -r /requirements.txt
 
RUN mkdir /frontend
WORKDIR /frontend
 
EXPOSE 8050
CMD ["python", "./application.py"]
