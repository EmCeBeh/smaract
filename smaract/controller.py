# ------------------------------------------------------------------------------
# This file is part of smaract (https://github.com/ALBA-Synchrotron/smaract)
#
# Copyright 2008-2017 CELLS / ALBA Synchrotron, Bellaterra, Spain
#
# Distributed under the terms of the GNU General Public License,
# either version 3 of the License, or (at your option) any later version.
# See LICENSE.txt for more info.
# ------------------------------------------------------------------------------


from constants import *
from axis import SmaractBaseAxis
from communication import SmaractCommunication


class SmaractBaseController(list):
    """
    Smaract Controller Base class. Contains the common Smaract ASCii API for any
    Smaract motor controller. The methods here implemented correspond to those
    at the controller level. It also implements a generic send_cmd function to
    automatically handles the error codes. This send_cmd functions is based on
    the communication base class, which provides an abstraction from the
    hardware layer communication.
    """
    ERROR_CODES = {0: 'No Error',
                   1: 'Syntax Error',
                   2: 'Invalid Command Error',
                   3: 'Overflow Error',
                   4: 'Parse Error',
                   5: 'Too Few Parameters Error',
                   6: 'Too Many Parameters Error',
                   7: 'Invalid Parameter Error',
                   8: 'Wrong Mode Error',
                   129: 'No Sensor Present Error',
                   140: 'Sensor Disabled Error',
                   141: 'Command Overridden Error',
                   142: 'End Stop Reached Error',
                   143: 'Wrong Sensor Type Error',
                   144: 'Could Not Find Reference Mark Error',
                   145: 'Wrong End Effector Type Error',
                   146: 'Movement Locked Error',
                   147: 'Range Limit Reached Error',
                   148: 'Physical Position Unknown Error',
                   150: 'Command Not Processable Error',
                   151: 'Waiting For Trigger Error',
                   152: 'Command Not Triggerable Error',
                   153: 'Command Queue Full Error',
                   154: 'Invalid Component Error',
                   155: 'Invalid Sub Component Error',
                   156: 'Invalid Property Error',
                   157: 'Permission Denied Error',
                   159: 'Power Amplifier Disabled Error'}

    SENSOR_CODE = {1: 'SL',
                   2: 'SR',
                   3: 'ML',
                   4: 'MR',
                   5: 'SP',
                   6: 'SC',
                   7: 'M25',
                   8: 'SR20',
                   9: 'M',
                   10: 'GC',
                   11: 'GD',
                   12: 'GE',
                   13: 'RA',
                   14: 'GF',
                   15: 'RB',
                   16: 'G605S',
                   17: 'G775S',
                   18: 'SC500',
                   19: 'G955S',
                   20: 'SR77',
                   21: 'SD',
                   22: 'R20ME',
                   23: 'SR2',
                   24: 'SCD',
                   25: 'SRC',
                   26: 'SR36M',
                   27: 'SR36ME',
                   28: 'SR50M',
                   29: 'SR50ME',
                   30: 'G1045S',
                   31: 'G1395S',
                   32: 'MD',
                   33: 'G935M',
                   34: 'SHL20',
                   35: 'SCT'}

    LINEAR_SENSORS = [1, 5, 6, 9, 18, 21, 24, 32, 35]

    ROTARY_SENSORS = [2, 8, 14, 20, 22, 23, 25, 26, 27, 28, 29]

    def __init__(self, comm_type, *args):
        """
        Class constructor. Requires an axis or list of axes from class
        SmaractBase axis (or derived classes).

        :param axes: axis or list of axes.
        """
        list.__init__(self)
        self._comm = SmaractCommunication(comm_type, *args)

    def send_cmd(self, cmd):
        """
        Communication function used to send any command to the smaract
        controller.
        :param cmd: string command following the Smaract ASCii Programming
        Interface.
        :return:
        """
        ans = self._comm.send_cmd(cmd)
        while True:
            err = int(self._comm.send_cmd(':SYST:ERR:COUN?'))
            if err == 0:
                break
            resp = self._comm.send_cmd(':SYST:ERR:NEXT?')
            print(resp)
            error_code = int(resp.rsplit(',')[0])
            error_msg = resp.rsplit(',')[1]
            if error_code != 0:
                msg = ('Error %d: %s' % (error_code, error_msg))
                                                   
                raise RuntimeError(msg)
        return ans

    @property
    def comm_type(self):
        """
        Get the communication type for this controller.

        :return: communication type
        """
        return self._comm.get_comm_type()

    # 3.1 - Initialization commands
    # -------------------------------------------------------------------------

    @property
    def nchannels(self):
        """
        Get the number of channels available (does not represent the number of
        currently connected positioners and effectors). The channels indexed are
        zero based.

        :return: the number of channels configured.
        """
        cmd = ':DEV:NOCH?'
        ans = self.send_cmd(cmd)
        return int(ans)

    @property
    def id(self):
        """
        Identify the controller with a unique ID.

        :return: system ID.
        """
        cmd = ':DEV:SNUM?'
        ans = self.send_cmd(cmd)
        return ans

class SmaractMCSController(SmaractBaseController):
    """
    Specific Smaract motor controller class for a Modular Controller System
    (MCS). This class extends the base class with the ASCII commands specific
    for the MCS motion controller.
    """

    def __init__(self, comm_type, *args):
        SmaractBaseController.__init__(self, comm_type, *args)

        # Configure communication mode to synchronous
        # The communication library work with acknowledge
        self._create_axes()
        
    def _create_axes(self):
        # We need to remake the complete axis list
        try:
            while True:
                self.pop()
        except IndexError:
            pass

        for axis_nr in range(self.nchannels):
            ans = self.send_cmd(':CHAN%d:PTYPE:NAME?' % axis_nr)
            sensor_code = ans.replace('\"', '').replace('\r', '').rsplit('.')[0]
            if sensor_code in ['SL']:
                axis = SmaractBaseAxis(self, axis_nr)
                self.append(axis)
            elif sensor_code in ['SR']:
                axis = SmaractBaseAxis(self, axis_nr)
                self.append(axis)
            elif sensor_code in ['CUSTOM0', 'CUSTOM1', 'CUSTOM2', 'CUSTOM3']:
                axis = SmaractBaseAxis(self, axis_nr)
                self.append(axis)
            else:
                msg = "Failed to create axis %s\n" % axis_nr
                msg += 'There is not axis class for sensor code %s' % sensor_code
                raise RuntimeError(msg)

    # 3.1 - Initialization commands

    def reset(self):
        """
        Performs a system reset, equivalent to a power up/down cycle.

        :return: None
        """
        ans = self.send_cmd('*RST')
        return float(ans.split(',')[1])

    # 3.2 - Configuration commands
    # -------------------------------------------------------------------------
    @property
    def sensor_enabled(self):
        """
        Gets the current sensor operation mode.

        0: Disabled (DISABLED)
        1: Enabled (ENABLED)
        2: Power save (POWER_SAVE)

        :return: integer representing the sensor operation mode.
        """
        cmd = 'GSE'
        ans = self.send_cmd(cmd)
        return str(ans[-1])

    @sensor_enabled.setter
    def sensor_enabled(self, enabled):
        """
        Sets the current sensor operation mode.

        :param enabled: operation mode value (0,1 or 2)
        :return: None
        """
        cmd = 'SSE%d' % enabled
        self.send_cmd(cmd)

    def trigger_command(self, trigger_idx=0):
        """
        Triggers the commands that were loaded into the command queue. Each
        is loaded with a given trigger index, grouping the commands loaded.
        There are 256 trigger index available, from 0 to 255, which correspond
        to a code range between 1792 and 2047.

        :param trigger_idx: trigger index of the command(s).
        :return: None
        """
        is_trigger_in_range(int(trigger_idx))
        cmd = 'TC%d' % (trigger_idx + TRIGGER_INDEX_0)
        self.send_cmd(cmd)

    # 3.5 - Miscellaneous commands
    # -------------------------------------------------------------------------
    def configure_baudrate(self, baudrate):
        """
        Sets the baudrate of the RS-232 interface.
        IMPORTANT: NOT AVAILABLE for network interface.

        :param baudrate: valid baudrate value
        :return: applied baudrate value.
        """
        # TODO: Restrict only to serial communication layer.
        is_baudrate_in_range(baudrate)
        cmd = 'BR%d' % baudrate
        ans = self.send_cmd(cmd)
        return int(ans[2:])

    def keep_alive(self, delay=0):
        """
        Timeout mechanism to stop all positioners immediately if the system does
        not receive a command in a certain interval. If delay=0 disables this
        feature.

        :param delay: timeout in ms.
        :return: None
        """
        cmd = 'K%d' % delay
        self.send_cmd(cmd)
