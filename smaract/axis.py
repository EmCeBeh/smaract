# ------------------------------------------------------------------------------
# This file is part of smaract (https://github.com/ALBA-Synchrotron/smaract)
#
# Copyright 2008-2017 CELLS / ALBA Synchrotron, Bellaterra, Spain
#
# Distributed under the terms of the GNU General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
#
# You should have received a copy of the GNU General Public License
# along with smaract. If not, see <http://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------------


import weakref
from .constants import *


class SmaractBaseAxis(object):
    """
    Smaract Axis Base class. Contains the common Smaract ASCii API for any
    Smaract axis. The methods here implemented correspond to those
    at the axis level. The _send_cmd function wrappers the current controller
    _send_cmd method.
    """
    def __init__(self, ctrl, axis_nr=0):
        self._axis_nr = axis_nr
        ref = weakref.ref(ctrl)
        self._ctrl = ref()
        
    def _send_cmd(self, str_cmd, *pars):
        """
        Send command function used to retrieve controller information at the
        axis level.

        :param str_cmd: String command following the ASCii Smaract API.
        :param pars: optional parameters required by the command.
        :return: command answer.
        """
        cmd = str_cmd.format(self._axis_nr)
        return self._ctrl.send_cmd(cmd)

    @property
    def safe_direction(self):
        """
        Gets the current configured safe direction.
        0: forward (FORWARD).
        1: backward (BACKWARD).
        Channel Type: Positioner.

        :return: either 0 or 1.

        Documentation: MCS Manual section 3.2
        """
        ans = self._send_cmd('GSD')
        direction = int(ans[-1])
        result = ['forward', 'backward'][direction]
        return result

    @safe_direction.setter
    def safe_direction(self, direction):
        """
        Sets the current configured safe direction.
        Channel Type: Positioner.

        :param direction: either forward(0) or backward(0).
        :return: None

        Documentation: MCS Manual section 3.2
        """
        direction = direction.lower()
        if direction == 'forward':
            value = 0
        elif direction == 'backward':
            value = 1
        else:
            raise ValueError('Read the help')
        self._send_cmd('SSD', value)

    @property
    def sensor_type(self):
        """
        Gets the type of sensor connected.
        Channel Type: Positioner.

        :return: Sensor code.

        Documentation: MCS Manual section 3.2
        """
        
        ans = self._send_cmd(':CHAN{:d}:PTYPE:NAME?')
        sensor_code = ans.strip("\"").rsplit('.')[0]
        return sensor_code

    @property
    def position(self):
        """
        Gets the current position of a positioner.
        Channel Type: Positioner.

        :return: current positioner position.

        Documentation: MCS Manual section 3.4
        """
        ans = self._send_cmd(':CHAN{:d}:POS?')
        return float(ans)

    @property
    def state(self):
        """
        Get the current movement status of the positioner or end effector.
        Channel Type: Positioner, End Effector.

        :return: channel status code.

        Documentation: MCS Manual section 3.4
        """
        ans = self._send_cmd('GS')
        return int(ans.split(',')[1]) 

    @property
    def status(self):
        """
        Get the current state, state msg and status of the positioner

        :return: channel status code, state msg and status.

        Documentation: MCS Manual section 3.4
        """

        state_code = self.state 
        state_msg = Status.states_txt[state_code]
        status = Status.status_txt[state_code]
        return state_code, state_msg, status

    ############################################################################
    #                       Commands
    ############################################################################
    def move(self, position):
        """
        Abstract method
        :param position: absolute position
        :return:
        """
        self._send_cmd(':MOVE{:d} ' + str(position))

    def calibrate_sensor(self):
        """
        Increase the accuracy of the position calculation.
        Channel Type: Positioner.

        :return: None

        Documentation: MCS Manual section 3.3
        """
        self._send_cmd(':CAL{:d}')

    def find_reference_mark(self, direction=0, hold_time=0, auto_zero=0):
        """
        Move to a known physical position of the positioner. Many strategies can
        be applied by setting different direction values. The hold_time (ms)
        sets for how long the position is actively held. The auto_zero flag setz
        the position to zero after the mark is find.
        Channel Type: Positioner

        :param direction: any valid direction value.
        :param hold_time: held after find reference mark in ms.
        :param auto_zero: flag to reset the position to 0.
        :return: None

        Documentation: MCS Manual section 3.3
        """
        self._send_cmd(':REF{:d}')
        
    def positioner_mode(self, mode=1):
        """
        Move to a known physical position of the positioner. Many strategies can
        be applied by setting different direction values. The hold_time (ms)
        sets for how long the position is actively held. The auto_zero flag setz
        the position to zero after the mark is find.
        Channel Type: Positioner

        :param direction: any valid direction value.
        :param hold_time: held after find reference mark in ms.
        :param auto_zero: flag to reset the position to 0.
        :return: None

        Documentation: MCS Manual section 3.3
        """
        self._send_cmd(':CHAN{:d}:MMOD ' + str(int(mode)))

    def stop(self):
        """
        Stops the ongoing motions of the positioner.
        Channel Type: Positioner.

        :return: None

        Documentation: MCS Manual section 3.3
        """
        self._send_cmd(':STOP{:d}')
