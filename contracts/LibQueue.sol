// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "./ArenaTypes.sol";

/**
 * @title LibQueue
 * @notice Gas-efficient FIFO queue for arena participants using mapping-based approach
 * @dev Based on the mapping queue pattern for O(1) enqueue/dequeue
 */
library LibQueue {

    struct Queue {
        mapping(uint256 => IArenaTypes.QueueEntry) entries;
        uint256 first;
        uint256 last;
    }

    function enqueue(Queue storage self, IArenaTypes.QueueEntry memory entry) internal {
        self.last += 1;
        self.entries[self.last] = entry;
    }

    function dequeue(Queue storage self) internal returns (IArenaTypes.QueueEntry memory entry) {
        if (isEmpty(self)) revert IArenaTypes.QueueEmpty();
        entry = self.entries[self.first + 1];
        delete self.entries[self.first + 1];
        self.first += 1;
    }

    function peek(Queue storage self) internal view returns (IArenaTypes.QueueEntry memory) {
        if (isEmpty(self)) revert IArenaTypes.QueueEmpty();
        return self.entries[self.first + 1];
    }

    function length(Queue storage self) internal view returns (uint256) {
        return self.last - self.first;
    }

    function isEmpty(Queue storage self) internal view returns (bool) {
        return self.last <= self.first;
    }
}
