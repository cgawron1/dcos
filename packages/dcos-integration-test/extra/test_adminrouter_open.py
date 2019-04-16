import logging
import re

import pytest


log = logging.getLogger(__name__)


@pytest.mark.security
class TestRedirectSecurity:

    @pytest.mark.parametrize(
        'path,expected', (
            ('/exhibitor', 301),
            ('/exhibitor/', 302),
            ('/marathon', 307),
            ('/mesos', 301),
            ('/mesos/master/redirect', 307),
            ('/mesos_dns', 301),
            ('/net', 301),
            ('/pkgpanda/repository', 301),
            ('/service/marathon', 301),
            ('/service/test-service', 301),
            ('/system/v1/logs', 301),
            ('/system/v1/metrics', 301),
        )
    )
    def test_redirect_host(
        self,
        dcos_api_session,
        path,
        expected,
    ) -> None:
        """
        Redirection does not propagate a bad Host header
        """
        r = dcos_api_session.get(
            path,
            headers={'Host': 'bad.host'},
            allow_redirects=False
        )

        r.raise_for_status()

        assert r.status_code == expected
        assert 'bad.host' not in r.headers['Location']


class TestEncodingGzip:

    pat = re.compile(r'/assets/index\.[^"]+')

    def test_accept_gzip(self, dcos_api_session):
        """
        Clients that send "Accept-Encoding: gzip" get gzipped responses
        for some assets.
        """
        r = dcos_api_session.get('/')
        r.raise_for_status()
        filenames = self.pat.findall(r.text)
        assert len(filenames) > 0
        for filename in set(filenames):
            log.info('Load %s', filename)
            log.info('%s', repr(r.headers))
            r = dcos_api_session.get(filename, headers={'Accept-Encoding': 'gzip'})
            r.raise_for_status()
            assert r.headers.get('content-encoding') == 'gzip'

    def test_not_accept_gzip(self, dcos_api_session):
        """
        Clients that do not send "Accept-Encoding: gzip" do not get gzipped
        responses.
        """
        r = dcos_api_session.get('/')
        r.raise_for_status()
        filenames = self.pat.findall(r.text)
        assert len(filenames) > 0
        for filename in set(filenames):
            log.info('Load %s', filename)
            log.info('%s', repr(r.headers))
            # Set a benign `Accept-Encoding` header to prevent underlying
            # libraries setting their own header based on their capabilities.
            r = dcos_api_session.get(filename, headers={'Accept-Encoding': 'identity'})
            r.raise_for_status()
            assert 'content-encoding' not in r.headers
