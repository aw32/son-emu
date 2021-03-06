from flask_restful import Resource
from flask import request, Response
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
import logging
import json


class KeystoneDummyApi(BaseOpenstackDummy):
    def __init__(self, in_ip, in_port):
        super(KeystoneDummyApi, self).__init__(in_ip, in_port)

        self.api.add_resource(KeystoneListVersions, "/", resource_class_kwargs={'api': self})
        self.api.add_resource(Shutdown, "/shutdown")
        self.api.add_resource(KeystoneShowAPIv2, "/v2.0", resource_class_kwargs={'api': self})
        self.api.add_resource(KeystoneGetToken, "/v2.0/tokens", resource_class_kwargs={'api': self})

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class Shutdown(Resource):
    """
    A get request to /shutdown will shut down this endpoint.
    """

    def get(self):
        logging.debug(("%s is beeing shut down") % (__name__))
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()


class KeystoneListVersions(Resource):
    """
    List all known keystone versions.
    Hardcoded for our version!
    """

    def __init__(self, api):
        self.api = api

    def get(self):
        """
        List API versions.

        :return: Returns the api versions.
        :rtype: :class:`flask.response` containing a static json encoded dict.
        """
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        resp = dict()
        resp['versions'] = dict()

        version = [{
            "id": "v2.0",
            "links": [
                {
                    "href": "http://%s:%d/v2.0" % (self.api.ip, self.api.port),
                    "rel": "self"
                }
            ],
            "media-types": [
                {
                    "base": "application/json",
                    "type": "application/vnd.openstack.identity-v2.0+json"
                }
            ],
            "status": "stable",
            "updated": "2014-04-17T00:00:00Z"
        }]
        resp['versions']['values'] = version

        return Response(json.dumps(resp), status=200, mimetype='application/json')


class KeystoneShowAPIv2(Resource):
    """
    Entrypoint for all openstack clients.
    This returns all current entrypoints running on son-emu.
    """

    def __init__(self, api):
        self.api = api

    def get(self):
        """
        List API entrypoints.

        :return: Returns an openstack style response for all entrypoints.
        :rtype: :class:`flask.response`
        """
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))

        neutron_port = self.api.port + 4696
        heat_port = self.api.port + 3004

        resp = dict()
        resp['version'] = {
            "status": "stable",
            "media-types": [
                {
                    "base": "application/json",
                    "type": "application/vnd.openstack.identity-v2.0+json"
                }
            ],
            "id": "v2.0",
            "links": [
                {
                    "href": "http://%s:%d/v2.0" % (self.api.ip, self.api.port),
                    "rel": "self"
                },
                {
                    "href": "http://%s:%d/v2.0/tokens" % (self.api.ip, self.api.port),
                    "rel": "self"
                },
                {
                    "href": "http://%s:%d/v2.0/networks" % (self.api.ip, neutron_port),
                    "rel": "self"
                },
                {
                    "href": "http://%s:%d/v2.0/subnets" % (self.api.ip, neutron_port),
                    "rel": "self"
                },
                {
                    "href": "http://%s:%d/v2.0/ports" % (self.api.ip, neutron_port),
                    "rel": "self"
                },
                {
                    "href": "http://%s:%d/v1/<tenant_id>/stacks" % (self.api.ip, heat_port),
                    "rel": "self"
                }
            ]
        }

        return Response(json.dumps(resp), status=200, mimetype='application/json')


class KeystoneGetToken(Resource):
    """
    Returns a static keystone token.
    We don't do any validation so we don't care.
    """

    def __init__(self, api):
        self.api = api

    def post(self):
        """
        List API entrypoints.

        This is hardcoded. For a working "authentication" use these ENVVARS:
        `OS_AUTH_URL`=http://<ip>:<port>/v2.0
        `OS_IDENTITY_API_VERSION`=2.0
        `OS_TENANT_ID`=fc394f2ab2df4114bde39905f800dc57
        `OS_REGION_NAME`=RegionOne
        `OS_USERNAME`=bla
        `OS_PASSWORD`=bla

        :return: Returns an openstack style response for all entrypoints.
        :rtype: :class:`flask.response`
        """

        logging.debug("API CALL: %s POST" % str(self.__class__.__name__))
        try:
            ret = dict()
            req = json.loads(request.data)
            ret['access'] = dict()
            ret['access']['token'] = dict()
            token = ret['access']['token']

            token['issued_at'] = "2014-01-30T15:30:58.819Z"
            token['expires'] = "2999-01-30T15:30:58.819Z"
            token['id'] = req['auth'].get('token', {'id': 'fc394f2ab2df4114bde39905f800dc57'}).get('id')
            token['tenant'] = dict()
            token['tenant']['description'] = None
            token['tenant']['enabled'] = True
            token['tenant']['id'] = req['auth'].get('tenantId', 'fc394f2ab2df4114bde39905f800dc57')
            token['tenant']['name'] = "tenantName"

            ret['access']['user'] = dict()
            user = ret['access']['user']
            user['username'] = "username"
            user['name'] = "tenantName"
            user['roles_links'] = list()
            user['id'] = token['tenant']['id']
            user['roles'] = [{'name': 'Member'}]

            ret['access']['region_name'] = "RegionOne"

            ret['access']['serviceCatalog'] = [{
                "endpoints": [
                    {
                        "adminURL": "http://%s:%s/v2.1/%s" % (self.api.ip, self.api.port + 3774, user['id']),
                        "region": "RegionOne",
                        "internalURL": "http://%s:%s/v2.1/%s" % (self.api.ip, self.api.port + 3774, user['id']),
                        "id": "2dad48f09e2a447a9bf852bcd93548ef",
                        "publicURL": "http://%s:%s/v2.1/%s" % (self.api.ip, self.api.port + 3774, user['id'])
                    }
                ],
                "endpoints_links": [],
                "type": "compute",
                "name": "nova"
            },
                {
                    "endpoints": [
                        {
                            "adminURL": "http://%s:%s/v2.0" % (self.api.ip, self.api.port),
                            "region": "RegionOne",
                            "internalURL": "http://%s:%s/v2.0" % (self.api.ip, self.api.port),
                            "id": "2dad48f09e2a447a9bf852bcd93543fc",
                            "publicURL": "http://%s:%s/v2" % (self.api.ip, self.api.port)
                        }
                    ],
                    "endpoints_links": [],
                    "type": "identity",
                    "name": "keystone"
                },
                {
                    "endpoints": [
                        {
                            "adminURL": "http://%s:%s" % (self.api.ip, self.api.port + 4696),
                            "region": "RegionOne",
                            "internalURL": "http://%s:%s" % (self.api.ip, self.api.port + 4696),
                            "id": "2dad48f09e2a447a9bf852bcd93548cf",
                            "publicURL": "http://%s:%s" % (self.api.ip, self.api.port + 4696)
                        }
                    ],
                    "endpoints_links": [],
                    "type": "network",
                    "name": "neutron"
                },
                {
                    "endpoints": [
                        {
                            "adminURL": "http://%s:%s" % (self.api.ip, self.api.port + 4242),
                            "region": "RegionOne",
                            "internalURL": "http://%s:%s" % (self.api.ip, self.api.port + 4242),
                            "id": "2dad48f09e2a447a9bf852bcd93548cf",
                            "publicURL": "http://%s:%s" % (self.api.ip, self.api.port + 4242)
                        }
                    ],
                    "endpoints_links": [],
                    "type": "image",
                    "name": "glance"
                },
                {
                    "endpoints": [
                        {
                            "adminURL": "http://%s:%s/v1/%s" % (self.api.ip, self.api.port + 3004, user['id']),
                            "region": "RegionOne",
                            "internalURL": "http://%s:%s/v1/%s" % (self.api.ip, self.api.port + 3004, user['id']),
                            "id": "2dad48f09e2a447a9bf852bcd93548bf",
                            "publicURL": "http://%s:%s/v1/%s" % (self.api.ip, self.api.port + 3004, user['id'])
                        }
                    ],
                    "endpoints_links": [],
                    "type": "orchestration",
                    "name": "heat"
                }
            ]

            ret['access']["metadata"] = {
                                            "is_admin": 0,
                                            "roles": [
                                                "7598ac3c634d4c3da4b9126a5f67ca2b"
                                            ]
                                        },
            ret['access']['trust'] = {
                "id": "394998fa61f14736b1f0c1f322882949",
                "trustee_user_id": "269348fdd9374b8885da1418e0730af1",
                "trustor_user_id": "3ec3164f750146be97f21559ee4d9c51",
                "impersonation": False
            }
            return Response(json.dumps(ret), status=200, mimetype='application/json')

        except Exception as ex:
            logging.exception("Keystone: Get token failed.")
            return ex.message, 500
