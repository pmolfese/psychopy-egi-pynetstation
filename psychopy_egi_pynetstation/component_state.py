"""Runtime state for PsychoPy Builder NetStation Components."""


class NetStationComponentState:
    """
    Give one Builder Component its own lifecycle state around a shared device.

    PsychoPy stores fields such as ``status``, ``tStart`` and ``frameNStart``
    on the object placed in a Routine's component list.  Every NetStation
    command uses the same hardware connection, so putting that connection in
    the list directly makes those fields collide between Components.  This
    lightweight proxy keeps fields assigned by Builder on itself and forwards
    device methods and read-only device attributes to the shared connection.
    """

    def __init__(self, device, status=None):
        self._device = device
        self.status = status

    @property
    def device(self):
        """The shared NetStation hardware device wrapped by this state."""
        return self._device

    def __getattr__(self, name):
        return getattr(self._device, name)
