from mock import patch
from skills_ml.job_postings.geography_queriers import job_posting_search_strings
from skills_ml.job_postings.geography_queriers.cbsa import JobCBSAFromCrosswalkQuerier, JobCBSAFromGeocodeQuerier
import json
import unittest

place_ua_lookup = {
    'IL': {'elgin': '123', 'gilberts': '234'},
    'MA': {'elgin': '823'}
}
cousub_ua_lookup = {
    'ND': {'elgin': '623'}
}
ua_cbsa_lookup = {
    '123': [['456', 'Chicago, IL Metro Area']],
    '234': [['678', 'Rockford, IL Metro Area']],
    '823': [
        ['987', 'Springfield, MA Metro Area'],
        ['876', 'Worcester, MA Metro Area'],
    ],
    '623': [['345', 'Fargo, ND Metro Area']]
}


class CrosswalkTest(unittest.TestCase):
    def setUp(self):
        place_patch = patch(
            'skills_ml.job_postings.geography_queriers.cbsa.place_ua',
            return_value=place_ua_lookup
        )
        cousub_patch = patch(
            'skills_ml.job_postings.geography_queriers.cbsa.cousub_ua',
            return_value=cousub_ua_lookup
        )
        cbsa_patch = patch(
            'skills_ml.job_postings.geography_queriers.cbsa.ua_cbsa',
            return_value=ua_cbsa_lookup
        )
        self.addCleanup(cousub_patch.stop)
        self.addCleanup(place_patch.stop)
        self.addCleanup(cbsa_patch.stop)
        cousub_patch.start()
        place_patch.start()
        cbsa_patch.start()
        self.querier = JobCBSAFromCrosswalkQuerier()

    def test_querier_one_hit(self):
        sample_job = {
            "description": "We are looking for someone for a job",
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "addressLocality": "Elgin",
                    "addressRegion": "IL",
                    "@type": "PostalAddress"
                }
            },
            "@context": "http://schema.org",
            "alternateName": "Customer Service Representative",
            "datePosted": "2013-03-07",
            "@type": "JobPosting",
            "id": 5
        }

        assert self.querier.query(sample_job) == ('456', 'Chicago, IL Metro Area')

    def test_querier_multiple_hits(self):
        sample_job = {
            "description": "We are looking for someone for a job",
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "addressLocality": "Elgin",
                    "addressRegion": "MA",
                    "@type": "PostalAddress"
                }
            },
            "@context": "http://schema.org",
            "alternateName": "Customer Service Representative",
            "datePosted": "2013-03-07",
            "@type": "JobPosting",
            "id": 5
        }

        assert self.querier.query(sample_job) == ('987', 'Springfield, MA Metro Area')

    def test_querier_no_hits(self):
        sample_job = {
            "description": "We are looking for someone for a job",
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "addressLocality": "Elgin",
                    "addressRegion": "TX",
                    "@type": "PostalAddress"
                }
            },
            "@context": "http://schema.org",
            "alternateName": "Customer Service Representative",
            "datePosted": "2013-03-07",
            "@type": "JobPosting",
            "id": 5
        }

        assert self.querier.query(sample_job) == (None, None)

    def test_querier_hit_in_alternate(self):
        sample_job = {
            "description": "We are looking for someone for a job",
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "addressLocality": "Elgin",
                    "addressRegion": "ND",
                    "@type": "PostalAddress"
                }
            },
            "@context": "http://schema.org",
            "alternateName": "Customer Service Representative",
            "datePosted": "2013-03-07",
            "@type": "JobPosting",
            "id": 5
        }

        assert self.querier.query(sample_job) == ('345', 'Fargo, ND Metro Area')

    def test_querier_blank(self):
        assert self.querier.query({'id': 5}) == (None, None)


# note: this is not actually what the output of the
# geocoder looks like.
# what's important is that the geocoder outputs
# in a form that the cbsa finder understands.
# That is what this geography querier cares about
class MockGeocoder(object):
    def geocode(self, search_string):
        if search_string == 'Elgin, Illinois':
            return '456'
        else:
            return None

class MockCBSAFinder(object):
    def query(self, geocode_result):
        if geocode_result:
            return ['456', 'Chicago, IL Metro Area']
        else:
            return None


class GeocodeTest(unittest.TestCase):
    def setUp(self):
        self.querier = JobCBSAFromGeocodeQuerier(geocoder=MockGeocoder(), cbsa_finder=MockCBSAFinder())

    def test_querier_one_hit(self):
        sample_job = {
            "description": "We are looking for someone for a job",
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "addressLocality": "Elgin",
                    "addressRegion": "IL",
                    "@type": "PostalAddress"
                }
            },
            "@context": "http://schema.org",
            "alternateName": "Customer Service Representative",
            "datePosted": "2013-03-07",
            "@type": "JobPosting",
            "id": 5
        }

        assert self.querier.query(sample_job) == \
            ('456', 'Chicago, IL Metro Area')

    def test_querier_hit_no_cbsa(self):
        sample_job = {
            "description": "We are looking for someone for a job",
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "addressLocality": "Elgin",
                    "addressRegion": "TX",
                    "@type": "PostalAddress"
                }
            },
            "@context": "http://schema.org",
            "alternateName": "Customer Service Representative",
            "datePosted": "2013-03-07",
            "@type": "JobPosting",
            "id": 5
        }

        assert self.querier.query(sample_job) == (None, None)

    def test_querier_not_present(self):
        sample_job = {
            "description": "We are looking for someone for a job",
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "addressLocality": "Elgin",
                    "addressRegion": "ND",
                    "@type": "PostalAddress"
                }
            },
            "@context": "http://schema.org",
            "alternateName": "Customer Service Representative",
            "datePosted": "2013-03-07",
            "@type": "JobPosting",
            "id": 5
        }

        assert self.querier.query(sample_job) == (None, None)



def test_job_posting_search_strings():
    with open('sample_job_listing.json') as f:
        sample_job_posting = json.load(f)

    assert sorted(job_posting_search_strings(sample_job_posting)) == sorted(['Salisbury, Pennsylvania', 'Salisbury, PA'])


def test_job_posting_weird_region():
    fake_job = {'jobLocation': {'address': {
        'addressLocality': 'Any City',
        'addressRegion': 'Northeastern USA'
    }}}

    assert job_posting_search_strings(fake_job) ==\
        ['Any City, Northeastern USA']


def test_job_posting_search_string_only_city():
    fake_job = {'jobLocation': {'address': {'addressLocality': 'City'}}}
    assert job_posting_search_strings(fake_job) == ['City']


def test_job_posting_search_string_bad_address():
    fake_job = {'jobLocation': {'address': {}}}
    assert job_posting_search_strings(fake_job) == []


def test_job_posting_search_string_no_location():
    assert job_posting_search_strings({}) == []
