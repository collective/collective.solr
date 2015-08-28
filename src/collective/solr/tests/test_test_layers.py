from collective.solr.testing import SolrLayer
from unittest import TestCase
import random
import socket


class TestLayerTests(TestCase):

    expected_random_values = [
        5485,
        29409,
        10547,
        21141,
        28218,
        3939,
        22352,
        20724,
        19392,
        9443]

    def testRandomPorts(self):
        random.seed('Reproducable randomness')
        for random_port in self.expected_random_values:
            layer = SolrLayer()
            self.assertEqual(random_port, layer.solr_port)

    def testRandomPortsSkipUsedPorts(self):
        random.seed('Reproducable randomness')
        for random_port in self.expected_random_values[:8]:
            layer = SolrLayer()
            self.assertEqual(random_port, layer.solr_port)
        a_socket = socket.socket(socket.AF_INET)
        try:
            a_socket.bind(('127.0.0.1', self.expected_random_values[8]))
            layer = SolrLayer()
            self.assertEqual(self.expected_random_values[9], layer.solr_port)
        finally:
            a_socket.close()
