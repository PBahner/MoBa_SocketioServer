from messages.message import OutboundMessage

from typing import TYPE_CHECKING, Dict
if TYPE_CHECKING:
    from railway.turnout import Turnout


class DistributeCurrentTurnoutPositionsMessage(OutboundMessage):
    def __init__(self, turnouts: list["Turnout"]):
        super().__init__('update_switch_positions')
        self.turnouts = turnouts

    def encode(self) -> Dict[int, int]:
        data = {turnout.id: turnout.current_pos for turnout in self.turnouts}
        return data


class DistributeInitialTurnoutPositionsMessage(DistributeCurrentTurnoutPositionsMessage):
    def __init__(self, turnouts: list["Turnout"]):
        OutboundMessage.__init__(self, 'init_switch_positions')
        self.turnouts = turnouts

