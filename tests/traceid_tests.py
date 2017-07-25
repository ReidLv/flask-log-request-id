import flask
import unittest

from flask_traceid.traceid import TraceID, get_amzn_elb_trace_id, current_trace_id
from mock import patch


class AmazonELBTraceIDTestCase(unittest.TestCase):
    def setUp(self):
        self.app = flask.Flask(__name__)
        self.trace_id = TraceID(self.app)

    def test_with_header_only_root(self):
        with self.app.test_request_context(headers={'X-Amzn-Trace-Id': 'Root=1-67891233-abc'}):
            self.assertEqual('1-67891233-abc', get_amzn_elb_trace_id())

    def test_with_header_root_and_self(self):
        with self.app.test_request_context(headers={'X-Amzn-Trace-Id': 'Self=1-67891234-def;Root=1-67891233-abc'}):
            self.assertEqual('1-67891234-def', get_amzn_elb_trace_id())

    def test_with_header_root_self_and_custom_params(self):
        with self.app.test_request_context(headers={'X-Amzn-Trace-Id': 'Self=1-def;Root=1-abc;CalledFrom=app'}):
            self.assertEqual('1-def', get_amzn_elb_trace_id())

    def test_without_header(self):
        with self.app.test_request_context():
            self.assertIsNone(get_amzn_elb_trace_id())

    def test_with_invalid_header(self):
        with self.app.test_request_context(headers={'X-Amzn-Trace-Id': 'ohmythisisnotvalid'}):
            self.assertIsNone(get_amzn_elb_trace_id())


class TraceIDTestCase(unittest.TestCase):
    def setUp(self):
        self.app = flask.Flask(__name__)

    def test_default_trace_id_extractor(self):
        TraceID(self.app)
        with self.app.test_request_context(headers={'X-Amzn-Trace-Id': 'Self=1-67891234-def;Root=1-67891233-abc'}):
            self.app.preprocess_request()
            self.assertEqual('1-67891234-def', current_trace_id())

    def test_custom_trace_id_extractor(self):
        TraceID(self.app, trace_id_extractor=lambda: 'fixedid')
        with self.app.test_request_context():
            self.app.preprocess_request()
            self.assertEqual('fixedid', current_trace_id(None))

    @patch('flask_traceid.traceid.uuid.uuid4')
    def test_default_generator(self, mock_uuid4):
        mock_uuid4.return_value = 'abc-123'
        TraceID(self.app)
        with self.app.test_request_context():
            self.app.preprocess_request()
            self.assertEqual('abc-123', current_trace_id(None))

    def test_custom_generator(self):
        TraceID(self.app, trace_id_generator=lambda: 'def-456')
        with self.app.test_request_context():
            self.app.preprocess_request()
            self.assertEqual('def-456', current_trace_id(None))

    @patch('flask_traceid.traceid.logger')
    def test_log_request_when_enabled(self, mock_logger):
        self.app.config.update({
            'TRACEID_EMIT_REQUEST_LOG': True
        })
        TraceID(self.app)

        with self.app.test_request_context('/test'):
            pass

        mock_logger.info.assert_called_once_with('None - - "GET /test 200"')

    @patch('flask_traceid.traceid.logger')
    def test_log_request_disabled(self, mock_logger):
        TraceID(self.app)
        with self.app.test_request_context('/test'):
            pass

        mock_logger.info.assert_not_called()
