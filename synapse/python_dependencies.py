# Copyright 2015, 2016 OpenMarket Ltd
# Copyright 2017 Vector Creations Ltd
# Copyright 2018 New Vector Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from pkg_resources import (
    DistributionNotFound,
    Requirement,
    VersionConflict,
    get_provider,
)

logger = logging.getLogger(__name__)


# REQUIREMENTS is a simple list of requirement specifiers[1], and must be
# installed. It is passed to setup() as install_requires in setup.py.
#
# CONDITIONAL_REQUIREMENTS is the optional dependencies, represented as a dict
# of lists. The dict key is the optional dependency name and can be passed to
# pip when installing. The list is a series of requirement specifiers[1] to be
# installed when that optional dependency requirement is specified. It is passed
# to setup() as extras_require in setup.py
#
# [1] https://pip.pypa.io/en/stable/reference/pip_install/#requirement-specifiers.

REQUIREMENTS = [
    "jsonschema>=2.5.1",
    "frozendict>=1",
    "unpaddedbase64>=1.1.0",
    "canonicaljson>=1.1.3",
    "signedjson>=1.0.0",
    "pynacl>=1.2.1",
    "idna>=2.5",
    # validating SSL certs for IP addresses requires service_identity 18.1.
    "service_identity>=18.1.0",
    # our logcontext handling relies on the ability to cancel inlineCallbacks
    # (https://twistedmatrix.com/trac/ticket/4632) which landed in Twisted 18.7.
    "Twisted>=18.7.0",
    "treq>=15.1",
    # Twisted has required pyopenssl 16.0 since about Twisted 16.6.
    "pyopenssl>=16.0.0",
    "pyyaml>=3.11",
    "pyasn1>=0.1.9",
    "pyasn1-modules>=0.0.7",
    "daemonize>=2.3.1",
    "bcrypt>=3.1.0",
    "pillow>=4.3.0",
    "sortedcontainers>=1.4.4",
    "psutil>=2.0.0",
    "pymacaroons>=0.13.0",
    "msgpack>=0.5.2",
    "phonenumbers>=8.2.0",
    "six>=1.10",
    "prometheus_client>=0.0.18,<0.8.0",
    # we use attr.s(slots), which arrived in 16.0.0
    # Twisted 18.7.0 requires attrs>=17.4.0
    "attrs>=17.4.0",
    "netaddr>=0.7.18",
    "Jinja2>=2.9",
    "bleach>=1.4.3",
    "sdnotify>=0.3",
]

CONDITIONAL_REQUIREMENTS = {
    "matrix-synapse-ldap3": ["matrix-synapse-ldap3>=0.1"],
    # we use execute_batch, which arrived in psycopg 2.7.
    "postgres": ["psycopg2>=2.7"],
    # ConsentResource uses select_autoescape, which arrived in jinja 2.9
    "resources.consent": ["Jinja2>=2.9"],
    # ACME support is required to provision TLS certificates from authorities
    # that use the protocol, such as Let's Encrypt.
    "acme": [
        "txacme>=0.9.2",
        # txacme depends on eliot. Eliot 1.8.0 is incompatible with
        # python 3.5.2, as per https://github.com/itamarst/eliot/issues/418
        'eliot<1.8.0;python_version<"3.5.3"',
    ],
    "saml2": ["pysaml2>=4.5.0"],
    "systemd": ["systemd-python>=231"],
    "url_preview": ["lxml>=3.5.0"],
    "test": ["mock>=2.0", "parameterized"],
    "sentry": ["sentry-sdk>=0.7.2"],
    "opentracing": ["jaeger-client>=4.0.0", "opentracing>=2.2.0"],
    "jwt": ["pyjwt>=1.6.4"],
}

ALL_OPTIONAL_REQUIREMENTS = set()

for name, optional_deps in CONDITIONAL_REQUIREMENTS.items():
    # Exclude systemd as it's a system-based requirement.
    if name not in ["systemd"]:
        ALL_OPTIONAL_REQUIREMENTS = set(optional_deps) | ALL_OPTIONAL_REQUIREMENTS


def list_requirements():
    return list(set(REQUIREMENTS) | ALL_OPTIONAL_REQUIREMENTS)


class DependencyException(Exception):
    @property
    def message(self):
        return "\n".join(
            [
                "Missing Requirements: %s" % (", ".join(self.dependencies),),
                "To install run:",
                "    pip install --upgrade --force %s" % (" ".join(self.dependencies),),
                "",
            ]
        )

    @property
    def dependencies(self):
        for i in self.args[0]:
            yield "'" + i + "'"


def check_requirements(for_feature=None):
    deps_needed = []
    errors = []

    if for_feature:
        reqs = CONDITIONAL_REQUIREMENTS[for_feature]
    else:
        reqs = REQUIREMENTS

    for dependency in reqs:
        try:
            _check_requirement(dependency)
        except VersionConflict as e:
            deps_needed.append(dependency)
            errors.append(
                "Needed %s, got %s==%s"
                % (dependency, e.dist.project_name, e.dist.version)
            )
        except DistributionNotFound:
            deps_needed.append(dependency)
            errors.append("Needed %s but it was not installed" % (dependency,))

    if not for_feature:
        # Check the optional dependencies are up to date. We allow them to not be
        # installed.
        OPTS = sum(CONDITIONAL_REQUIREMENTS.values(), [])

        for dependency in OPTS:
            try:
                _check_requirement(dependency)
            except VersionConflict as e:
                deps_needed.append(dependency)
                errors.append(
                    "Needed optional %s, got %s==%s"
                    % (dependency, e.dist.project_name, e.dist.version)
                )
            except DistributionNotFound:
                # If it's not found, we don't care
                pass

    if deps_needed:
        for e in errors:
            logging.error(e)

        raise DependencyException(deps_needed)


def _check_requirement(dependency_string):
    """Parses a dependency string, and checks if the specified requirement is installed

    Raises:
        VersionConflict if the requirement is installed, but with the the wrong version
        DistributionNotFound if nothing is found to provide the requirement
    """
    req = Requirement.parse(dependency_string)

    # first check if the markers specify that this requirement needs installing
    if req.marker is not None and not req.marker.evaluate():
        # not required for this environment
        return

    get_provider(req)


if __name__ == "__main__":
    import sys

    sys.stdout.writelines(req + "\n" for req in list_requirements())
