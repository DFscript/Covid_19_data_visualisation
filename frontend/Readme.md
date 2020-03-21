# How to start

1) Feel free to change the first template for dash which was uploaded to
[application.py](https://github.com/DFscript/Covid_19_data_visualisation/blob/master/frontend/application.py)
2) start your docker with:

```
docker build -t frontend:latest .
docker run -v "$(pwd):/frontend" -p 8050:8050 frontend
```
