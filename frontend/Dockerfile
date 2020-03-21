FROM python:3
 
COPY requirements.txt /
RUN pip install -r /requirements.txt
 
EXPOSE 8050
WORKDIR /repo/frontend
CMD ["python", "application.py"]
