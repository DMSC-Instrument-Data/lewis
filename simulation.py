#!/usr/bin/env python
#  -*- coding: utf-8 -*-
# *********************************************************************
# plankton - a library for creating hardware device simulators
# Copyright (C) 2016 European Spallation Source ERIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *********************************************************************

import argparse
from core.utils import get_available_submodules
from core.control_server import ControlServer, ExposedObject
from core.environment import SimulationEnvironment

from adapters import import_adapter
from setups import import_device, import_bindings

parser = argparse.ArgumentParser(
    description='Run a simulated device and expose it via a specified communication protocol.')
parser.add_argument('-d', '--device', help='Name of the device to simulate.', default='chopper',
                    choices=get_available_submodules('setups'))
parser.add_argument('-r', '--rpc-host', help='HOST:PORT format string for exposing the device via JSON-RPC over ZMQ.')
parser.add_argument('-s', '--setup', help='Name of the setup to load.', default='default')
parser.add_argument('-b', '--bindings', help='Bindings to import from setups.device.bindings. '
                                             'If not specified, this defaults to the value of --protocol.')
parser.add_argument('-p', '--protocol', help='Communication protocol to expose devices.', default='epics',
                    choices=get_available_submodules('adapters'))
parser.add_argument('-a', '--adapter',
                    help='Name of adapter class. If not specified, the loader will choose '
                         'the first adapter it discovers.')
parser.add_argument('-t', '--processing-time',
                    help='Approximate time to spend in each cycle of the simulation. Must be greater than 0.',
                    type=float, default=0.1)
parser.add_argument('-w', '--time-warp', type=float, default=1.0,
                    help='Time warp factor for the simulation. The actually elapsed time '
                         'between two cycles is multiplied with this factor to determine the simulated time.')
parser.add_argument('adapter_args', nargs='*', help='Arguments for the adapter.')

arguments = parser.parse_args()

CommunicationAdapter = import_adapter(arguments.protocol, arguments.adapter)

bindings = import_bindings(arguments.device, arguments.protocol if arguments.bindings is None else arguments.bindings)
device = import_device(arguments.device, arguments.setup)

environment = SimulationEnvironment(
    adapter=CommunicationAdapter(device, bindings, arguments.adapter_args))

environment.cycle_delay = arguments.cycle_delay
environment.time_warp = arguments.time_warp

if arguments.rpc_host:
    environment.control_server = ControlServer(
        {'device': device,
         'simulation': ExposedObject(environment, exclude=('start', 'control_server'))},
        *arguments.rpc_host.split(':'))

environment.start()
