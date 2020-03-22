# How to start

1) Feel free to change the first template for dash which was uploaded to
[application.py](https://github.com/DFscript/Covid_19_data_visualisation/blob/master/frontend/application.py)
2) start your docker with:
As client:
sudo docker build -t frontend:latest .
sudo docker run -v "$(dirname "$(pwd)"):/repo" -p 8050:8050 frontend

As Server:
sudo docker build -t frontend:latest -f ./DockerfileServer .
sudo docker run -v "$(diame "$(pwd)"):/repo" -p 80:8050 frontend

