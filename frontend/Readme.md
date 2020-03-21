# How to start

1) Feel free to change the first template for dash which was uploaded to
[application.py](https://github.com/DFscript/Covid_19_data_visualisation/blob/master/frontend/application.py)
2) start your docker with:

```
<<<<<<< HEAD
docker build -t frontend:latest .
docker run -v "$(pwd):/frontend" -p 8050:8050 frontend
=======
sudo docker build -t frontend:latest .
sudo docker run -d -p 8050:8050 frontend
>>>>>>> 71791222d4d61db47c7d45cbc5c589e952c7700e
```
