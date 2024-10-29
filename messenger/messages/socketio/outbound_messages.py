from messages.message import OutboundMessage

from typing import TYPE_CHECKING, Dict
if TYPE_CHECKING:
    from railway.turnout import Turnout
    from railway.track import TrackInterruption


class DistributeCurrentTurnoutPositionsMessage(OutboundMessage):
    def __init__(self, turnouts: list["Turnout"]):
        super().__init__('update_switch_positions')
        self.turnouts = turnouts

    def encode(self) -> Dict[int, int]:
        data = {turnout.id: int(turnout.current_pos) for turnout in self.turnouts}
        return data


class DistributeInitialTurnoutPositionsMessage(DistributeCurrentTurnoutPositionsMessage):
    def __init__(self, turnouts: list["Turnout"]):
        OutboundMessage.__init__(self, 'init_switch_positions')
        self.turnouts = turnouts


class DistributeCurrentTrackInterruptionsMessage(OutboundMessage):
    def __init__(self, track_interruptions: list["TrackInterruption"]):
        super().__init__('distribute_track_interruptions')
        self.track_interruptions = track_interruptions

    def encode(self) -> Dict[int, int]:
        data = {(track.global_number << 2) + track.section: int(track.state) for track in self.track_interruptions if track.state}
        return data
