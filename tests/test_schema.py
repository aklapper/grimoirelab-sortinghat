#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2018 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

import datetime

import dateutil

import django.core.exceptions
import django.test
import graphene
import graphene.test

from sortinghat.core.models import (Organization,
                                    Domain,
                                    Country,
                                    UniqueIdentity,
                                    Identity,
                                    Profile,
                                    Enrollment)
from sortinghat.core.schema import SortingHatQuery, SortingHatMutations


DUPLICATED_ORG_ERROR = "Organization 'Example' already exists in the registry"
NAME_EMPTY_ERROR = "'name' cannot be an empty string"
ORG_DOES_NOT_EXIST_ERROR = "Organization matching query does not exist."


# Test queries
SH_ORGS_QUERY = """{
  organizations {
    name
    domains {
      domain
      isTopDomain
    }
  }
}"""
SH_UIDS_QUERY = """{
  uidentities {
    uuid
    profile {
      name
      email
      gender
      isBot
      country {
        code
        name
      }
    }
    identities {
      id
      name
      email
      username
      source
    }
    enrollments {
      organization {
        name
      }
      start
      end
    }
  }
}"""


class TestQuery(SortingHatQuery, graphene.ObjectType):
    pass


class TestMutations(SortingHatMutations):
    pass


schema = graphene.Schema(query=TestQuery,
                         mutation=TestMutations)


class TestQueryOrganizations(django.test.TestCase):
    """Unit tests for organization queries"""

    def test_organizations(self):
        """Check if it returns the registry of organizations"""

        org = Organization.objects.create(name='Example')
        Domain.objects.create(domain='example.com', organization=org)
        Domain.objects.create(domain='example.org', organization=org)
        org = Organization.objects.create(name='Bitergia')
        Domain.objects.create(domain='bitergia.com', organization=org)
        _ = Organization.objects.create(name='LibreSoft')

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_ORGS_QUERY)

        orgs = executed['data']['organizations']
        self.assertEqual(len(orgs), 3)

        org1 = orgs[0]
        self.assertEqual(org1['name'], 'Bitergia')
        self.assertEqual(len(org1['domains']), 1)

        org2 = orgs[1]
        self.assertEqual(org2['name'], 'Example')
        self.assertEqual(len(org2['domains']), 2)

        org3 = orgs[2]
        self.assertEqual(org3['name'], 'LibreSoft')
        self.assertEqual(len(org3['domains']), 0)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_ORGS_QUERY)

        orgs = executed['data']['organizations']
        self.assertListEqual(orgs, [])


class TestUniqueIdentities(django.test.TestCase):
    """Unit tests for unique identities queries"""

    def test_unique_identities(self):
        """Check if it returns the registry of unique identities"""

        cn = Country.objects.create(code='US',
                                    name='United States of America',
                                    alpha3='USA')

        org_ex = Organization.objects.create(name='Example')
        org_bit = Organization.objects.create(name='Bitergia')

        uid = UniqueIdentity.objects.create(uuid='a9b403e150dd4af8953a52a4bb841051e4b705d9')
        Profile.objects.create(name=None,
                               email='jsmith@example.com',
                               is_bot=True,
                               gender='M',
                               country=cn,
                               uidentity=uid)
        Identity.objects.create(id='A001',
                                name='John Smith',
                                email='jsmith@example.com',
                                username='jsmith',
                                source='scm',
                                uidentity=uid)
        Identity.objects.create(id='A002',
                                name=None,
                                email='jsmith@bitergia.com',
                                username=None,
                                source='scm',
                                uidentity=uid)
        Identity.objects.create(id='A003',
                                name=None,
                                email='jsmith@bitergia.com',
                                username=None,
                                source='mls',
                                uidentity=uid)
        Enrollment.objects.create(uidentity=uid, organization=org_ex)
        Enrollment.objects.create(uidentity=uid, organization=org_bit,
                                  start=datetime.datetime(1999, 1, 1, 0, 0, 0,
                                                          tzinfo=dateutil.tz.tzutc()),
                                  end=datetime.datetime(2000, 1, 1, 0, 0, 0,
                                                        tzinfo=dateutil.tz.tzutc()))

        uid = UniqueIdentity.objects.create(uuid='c6d2504fde0e34b78a185c4b709e5442d045451c')
        Profile.objects.create(email=None,
                               is_bot=False,
                               gender='M',
                               country=None,
                               uidentity=uid)
        Identity.objects.create(id='B001',
                                name='John Doe',
                                email='jdoe@example.com',
                                username='jdoe',
                                source='scm',
                                uidentity=uid)
        Identity.objects.create(id='B002',
                                name=None,
                                email='jdoe@libresoft.es',
                                username=None,
                                source='scm',
                                uidentity=uid)

        # Tests
        client = graphene.test.Client(schema)
        executed = client.execute(SH_UIDS_QUERY)

        uidentities = executed['data']['uidentities']
        self.assertEqual(len(uidentities), 2)

        # Test John Smith unique identity
        uid = uidentities[0]
        self.assertEqual(uid['uuid'], 'a9b403e150dd4af8953a52a4bb841051e4b705d9')

        self.assertEqual(uid['profile']['name'], None)
        self.assertEqual(uid['profile']['email'], 'jsmith@example.com')
        self.assertEqual(uid['profile']['isBot'], True)
        self.assertEqual(uid['profile']['country']['code'], 'US')
        self.assertEqual(uid['profile']['country']['name'], 'United States of America')

        identities = uid['identities']
        identities.sort(key=lambda x: x['id'])
        self.assertEqual(len(identities), 3)

        id1 = identities[0]
        self.assertEqual(id1['email'], 'jsmith@example.com')

        id2 = identities[1]
        self.assertEqual(id2['email'], 'jsmith@bitergia.com')
        self.assertEqual(id2['source'], 'scm')

        id3 = identities[2]
        self.assertEqual(id3['email'], 'jsmith@bitergia.com')
        self.assertEqual(id3['source'], 'mls')

        enrollments = uid['enrollments']
        enrollments.sort(key=lambda x: x['organization']['name'])
        self.assertEqual(len(enrollments), 2)

        rol1 = enrollments[0]
        self.assertEqual(rol1['organization']['name'], 'Bitergia')
        self.assertEqual(rol1['start'], '1999-01-01T00:00:00+00:00')
        self.assertEqual(rol1['end'], '2000-01-01T00:00:00+00:00')

        rol2 = enrollments[1]
        self.assertEqual(rol2['organization']['name'], 'Example')
        self.assertEqual(rol2['start'], '1900-01-01T00:00:00+00:00')
        self.assertEqual(rol2['end'], '2100-01-01T00:00:00+00:00')

        # Test John Doe unique identity
        uid = uidentities[1]
        self.assertEqual(uid['uuid'], 'c6d2504fde0e34b78a185c4b709e5442d045451c')

        self.assertEqual(uid['profile']['name'], None)
        self.assertEqual(uid['profile']['email'], None)

        identities = uid['identities']
        identities.sort(key=lambda x: x['id'])
        self.assertEqual(len(identities), 2)

        id1 = identities[0]
        self.assertEqual(id1['email'], 'jdoe@example.com')

        id2 = identities[1]
        self.assertEqual(id2['email'], 'jdoe@libresoft.es')

        enrollments = uid['enrollments']
        self.assertEqual(len(enrollments), 0)

    def test_empty_registry(self):
        """Check whether it returns an empty list when the registry is empty"""

        client = graphene.test.Client(schema)
        executed = client.execute(SH_UIDS_QUERY)

        uids = executed['data']['uidentities']
        self.assertListEqual(uids, [])


class TestAddOrganizationMutation(django.test.TestCase):
    """Unit tests for mutation to add organizations"""

    SH_ADD_ORG = """
      mutation addOrg {
        addOrganization(name: "Example") {
          organization {
            name
            domains {
              domain
              isTopDomain
            }
          }
        }
      }
    """

    SH_ADD_ORG_NAME_EMPTY = """
      mutation addOrg {
        addOrganization(name: "") {
          organization {
            name
            domains {
              domain
              isTopDomain
            }
          }
        }
      }
    """

    def test_add_organization(self):
        """Check if a new organization is added"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG)

        # Check result
        org = executed['data']['addOrganization']['organization']
        self.assertEqual(org['name'], 'Example')
        self.assertListEqual(org['domains'], [])

        # Check database
        org = Organization.objects.get(name='Example')
        self.assertEqual(org.name, 'Example')

    def test_name_empty(self):
        """Check whether organizations with empty names cannot be added"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG_NAME_EMPTY)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, NAME_EMPTY_ERROR)

        # Check database
        orgs = Organization.objects.all()
        self.assertEqual(len(orgs), 0)

    def test_integrity_error(self):
        """Check whether organizations with the same name cannot be inserted"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG)

        # Check database
        org = Organization.objects.get(name='Example')
        self.assertEqual(org.name, 'Example')

        # Try to insert it twice
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_ADD_ORG)

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, DUPLICATED_ORG_ERROR)


class TestDeleteOrganizationMutation(django.test.TestCase):
    """Unit tests for mutation to delete organizations"""

    SH_DELETE_ORG = """
      mutation delOrg {
        deleteOrganization(name: "Example") {
          organization {
            name
          }
        }
      }
    """

    def test_delete_organization(self):
        """Check whether it deletes an organization"""

        org_ex = Organization.objects.create(name='Example')
        Domain.objects.create(domain='example.org',
                              organization=org_ex)
        org_bit = Organization.objects.create(name='Bitergia')

        jsmith = UniqueIdentity.objects.create(uuid='AAAA')
        Profile.objects.create(name='John Smith',
                               email='jsmith@example.net',
                               uidentity=jsmith)
        Enrollment.objects.create(uidentity=jsmith, organization=org_ex)

        jdoe = UniqueIdentity.objects.create(uuid='BBBB')
        Profile.objects.create(name='John Doe',
                               email='jdoe@bitergia.com',
                               uidentity=jdoe)
        Enrollment.objects.create(uidentity=jdoe, organization=org_ex)
        Enrollment.objects.create(uidentity=jdoe, organization=org_bit)

        # Delete organization
        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_ORG)

        # Check result
        org = executed['data']['deleteOrganization']['organization']
        self.assertEqual(org['name'], 'Example')

        # Tests
        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            Organization.objects.get(name='Example')

        with self.assertRaises(django.core.exceptions.ObjectDoesNotExist):
            Domain.objects.get(domain='example.org')

        enrollments = Enrollment.objects.filter(organization__name='Example')
        self.assertEqual(len(enrollments), 0)

        enrollments = Enrollment.objects.filter(organization__name='Bitergia')
        self.assertEqual(len(enrollments), 1)

    def test_not_found_organization(self):
        """Check if it returns an error when an organization does not exist"""

        client = graphene.test.Client(schema)
        executed = client.execute(self.SH_DELETE_ORG)

        # Check error
        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORG_DOES_NOT_EXIST_ERROR)

        # It should not remove anything
        Organization.objects.create(name='Bitergia')

        msg = executed['errors'][0]['message']
        self.assertEqual(msg, ORG_DOES_NOT_EXIST_ERROR)

        orgs = Organization.objects.all()
        self.assertEqual(len(orgs), 1)
