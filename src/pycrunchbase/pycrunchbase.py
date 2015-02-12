import requests
import six
from requests.exceptions import HTTPError

from .resource import (
    Acquisition,
    FundingRound,
    Organization,
    Person,
    Product,
    Relationship,
)


class CrunchBase(object):
    """Class that manages talking to CrunchBase API"""
    BASE_URL = 'https://api.crunchbase.com/v/2/'
    ORGANIZATIONS_URL = BASE_URL + 'organizations'
    ORGANIZATION_URL = BASE_URL + 'organization'
    PEOPLE_URL = BASE_URL + 'people'
    PERSON_URL = BASE_URL + 'person'
    FUNDING_ROUND_URL = BASE_URL + 'funding-round'

    def __init__(self, api_key=None):
        if not api_key:
            raise ValueError('API key for CrunchBase not supplied')
        self.api_key = api_key

    def organizations(self, name):
        """
        Search for a organization given a name, returns details of first match

        Returns:
            :class:`Organization` or None
        """
        url = self.ORGANIZATIONS_URL
        data = self._make_request(url, {'name': name})
        if not data or data.get('error'):
            return None
        return self._get_first_organization_match(data.get('items'))

    def organization(self, permalink):
        """Get the details of a organization given a organization's permalink.

        Returns:
            Organization or None
        """
        node_data = self.get_node('organization', permalink)
        return Organization(node_data) if node_data else None

    def person(self, permalink):
        """Get the details of a person given a person's permalink

        Returns:
            Person or None
        """
        node_data = self.get_node('person', permalink)
        return Person(node_data) if node_data else None

    def funding_round(self, uuid):
        """Get the details of a FundingRound given the uuid.

        Returns
            FundingRound or None
        """
        node_data = self.get_node('funding-round', uuid)
        return FundingRound(node_data) if node_data else None

    def acquisition(self, uuid):
        """Get the details of a acquisition given a uuid.

        Returns:
            Acquisition or None
        """
        node_data = self.get_node('acquisition', uuid)
        return Acquisition(node_data) if node_data else None

    def product(self, permalink):
        """Get the details of a product given a product permalink.

        Returns:
            Product or None
        """
        node_data = self.get_node('product', permalink)
        return Product(node_data) if node_data else None

    def get_node(self, node_type, uuid, params={}):
        """Get the details of a Node from CrunchBase.
        The node_type must match that of CrunchBase's, and the uuid
        is either the {uuid} or {permalink} as stated on their docs.
        Returns:
            A dict containing the data describing this node.
            It has the keys: uuid, type, properties, relationships.

            Or None if there's an error.
        """
        node_url = self.BASE_URL + node_type + '/' + uuid
        data = self._make_request(node_url, params=params)
        if not data or data.get('error'):
            return None
        return data

    def more(self, relationship):
        """Given a Relationship, tries to get more data using the
        next_page_url given in the response.

        Returns:
            None if there is no more data to get or if you have all the data
            :class:`Relationship` with the new data
        """
        if relationship.total_items <= len(relationship):
            return None

        if relationship.first_page_url:
            url_to_call = relationship.first_page_url
            return self._relationship(relationship.name, url_to_call)
        elif relationship.next_page_url:
            url_to_call = relationship.next_page_url
            return self._relationship(relationship.name, url_to_call)
        else:
            return None

    def _relationship(self, name, url):
        """Loads a relationship for a Node

        Args:
            name (str): name of relationship we are getting
            url (str): url of the relationship to make the call to

        Returns:
            :class:`Relationship` if we can get the data
            None if we have an error
        """
        data = self._make_request(url)
        if not data or data.get('error'):
            return None
        return Relationship(name, data)

    def _get_first_organization_match(self, list_of_result=[None]):
        """Returns:
            :class:`Organization` or None
        """
        first_match = list_of_result[0] or {}
        crunchbase_organization_path = first_match.get('path', '')
        organization_name = crunchbase_organization_path.split('/')[1]
        return self.organization(organization_name)

    def _build_url(self, base_url, params={}):
        """Helper to build urls by appending all queries and the API key
        """
        base_url = '{url}?user_key={api_key}'.format(
            url=base_url, api_key=self.api_key)
        query_list = ['%s=%s' % (k, v) for k, v in six.iteritems(params)]
        if query_list:
            base_url += '&' + '&'.join(query_list)
        return base_url

    def _make_request(self, url, params={}):
        """Makes the actual API call to CrunchBase
        """
        final_url = self._build_url(url, params)
        try:
            response = requests.get(final_url)
            response.raise_for_status()
        except HTTPError:
            return None
        return response.json().get('data')
