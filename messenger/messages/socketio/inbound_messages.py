from ..message import InboundMessage

from typing import List


class TurnoutChangeRequestMessage(InboundMessage):
    turnouts: List[int] = []

    def decode(self):
        self.turnouts = self.data["data"]


class TrackInterruptionOnRequestMessage(InboundMessage):
    turnouts: List[int] = []

    def decode(self):
        self.turnouts = self.data["data"]


class TrackInterruptionOffRequestMessage(InboundMessage):
    turnouts: List[int] = []

    def decode(self):
        self.turnouts = self.data["data"]
