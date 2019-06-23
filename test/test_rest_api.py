import pytest
import unittest
import binascii
import syft as sy
from syft import codes, TorchHook
import torch as th
from grid.app import create_app, db
from grid.app.models import Worker as WorkerMDL
from grid.app.models import WorkerObject
from grid.client import GridClient
from flask_testing import LiveServerTestCase
import requests

import time
import os


class RestAPITests(LiveServerTestCase):
    def create_app(self):
        BASEDIR = os.path.dirname(os.path.dirname(__file__))
        app = create_app(
            {
                "SQLALCHEMY_DATABASE_URI": "sqlite:///"
                + os.path.join(BASEDIR, "app_test.db")
            }
        )
        return app

    def setUp(self):
        db.create_all()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_empty_db(self):
        rv = requests.get(self.get_server_url())
        assert "Howdy World" in rv.text

    def test_identity(self):
        rv = requests.get(f"{self.get_server_url()}/identity/")
        assert "OpenGrid" in rv.text

    def test_create_worker_send_tensor(self):
        x = th.tensor([1, 2, 3, 4])
        msg_type = codes.MSGTYPE.OBJ
        message = (msg_type, x)
        bin_message = sy.serde.serialize(message)
        bin_message = str(binascii.hexlify(bin_message))
        rv = requests.post(
            f"{self.get_server_url()}/cmd/", data={"message": bin_message}
        )
        worker_mdl = WorkerMDL.query.filter_by(public_id="worker").first()
        assert worker_mdl.worker_objects[0].object.sum() == x.sum()

    def test_send_receive_tensors(self):
        db.create_all()
        db.session.commit()
        hook = TorchHook(th)
        grid = GridClient(self.get_server_url())
        tensor = th.tensor([1, 2, 3, 4])
        pointer_tensor = tensor.send(grid)
        assert tensor.sum() == pointer_tensor.sum().get()
