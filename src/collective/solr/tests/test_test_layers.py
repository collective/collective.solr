from collective.solr.testing import SolrLayer
from unittest import TestCase
import random
import socket


class TestLayerTests(TestCase):

    expected_random_values = [
        10090,
        58709,
        20377,
        41907,
        56288,
        6948,
        44367,
        41059,
        38351,
        18133]

    def testRandomPorts(self):
        random.seed('Reproducable randomness')
        for random_port in self.expected_random_values:
            layer = SolrLayer(solr_port='RANDOM')
            self.assertEqual(random_port, layer.solr_port)

    def testRandomPortsSkipUsedPorts(self):
        random.seed('Reproducable randomness')
        for random_port in self.expected_random_values[:8]:
            layer = SolrLayer(solr_port='RANDOM')
            self.assertEqual(random_port, layer.solr_port)
        a_socket = socket.socket(socket.AF_INET)
        try:
            a_socket.bind(('127.0.0.1', self.expected_random_values[8]))
            layer = SolrLayer(solr_port='RANDOM')
            self.assertEqual(self.expected_random_values[9], layer.solr_port)
        finally:
            a_socket.close()
