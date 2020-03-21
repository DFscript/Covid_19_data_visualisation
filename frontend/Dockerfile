FROM python:3
 
COPY requirements.txt /
RUN pip install -r /requirements.txt
 
RUN mkdir /frontend
WORKDIR /frontend
COPY ./ ./
 
EXPOSE 8050
CMD ["python", "./application.py"]