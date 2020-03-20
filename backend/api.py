from flask import Flask, Blueprint, url_for, session
from flask_restplus import Api, Resource, fields,apidoc
from flask_cors import CORS
import os, uuid

app = Flask(__name__)
CORS(app, supports_credentials=True)


#if 'REVERSE_PROXY_REQUIRED' in os.environ:
#    from myProxyFix import ReverseProxied
#    app.wsgi_app = ReverseProxied(app.wsgi_app)


api=Api(app, 
        title="framework_flaskapi",
        default="Endpoint",
        default_label=""
)

@api.route('/ping')
class Ping(Resource):
    def get(self):
        """
        A simple GET endpoint
        """
        return {'ping':'PONG'}

if __name__ == "__main__":
    app.run(debug=True)
