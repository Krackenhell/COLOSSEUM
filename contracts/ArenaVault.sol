// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "./ArenaTypes.sol";

/**
 * @title ArenaVault
 * @notice Manages AVAX deposits, pending rewards, and commission withdrawals
 * @dev Separates funds logic from trading logic for security
 *      Uses pull-pattern for reward claims (CEI: Checks-Effects-Interactions)
 */
abstract contract ArenaVault is IArenaTypes {

    // ===================== STATE =====================

    /// @notice Accumulated pending rewards per user (in wei)
    mapping(address => uint256) public pendingReward;

    /// @notice Accumulated owner commission (in wei)
    uint256 public accumulatedCommission;

    // ===================== INTERNAL =====================

    /**
     * @notice Credits reward to a user (internal, called by arena logic)
     * @param user Recipient address
     * @param amount Reward amount in wei
     */
    function _creditReward(address user, uint256 amount) internal {
        pendingReward[user] += amount;
    }

    /**
     * @notice Adds to accumulated commission
     * @param amount Commission amount in wei
     */
    function _addCommission(uint256 amount) internal {
        accumulatedCommission += amount;
    }

    // ===================== EXTERNAL =====================

    /**
     * @notice Allows winners to claim their pending rewards (pull-pattern)
     * @dev CEI pattern: checks -> effects -> interactions
     */
    function claimReward() external {
        uint256 amount = pendingReward[msg.sender];
        if (amount == 0) revert NoRewardToClaim();
        if (address(this).balance < amount) {
            revert InsufficientContractBalance(address(this).balance, amount);
        }

        // Effects before interaction
        pendingReward[msg.sender] = 0;

        // Interaction
        (bool success,) = payable(msg.sender).call{value: amount}("");
        if (!success) revert TransferFailed();

        emit RewardClaimed(msg.sender, amount);
    }

    /**
     * @notice Owner withdraws accumulated commission to specified address
     * @param to Recipient of commission
     * @dev Must be overridden with onlyOwner modifier in child contract
     */
    function _withdrawCommission(address to) internal {
        if (to == address(0)) revert ZeroAddress();
        uint256 amount = accumulatedCommission;
        if (amount == 0) revert NoRewardToClaim();
        if (address(this).balance < amount) {
            revert InsufficientContractBalance(address(this).balance, amount);
        }

        accumulatedCommission = 0;

        (bool success,) = payable(to).call{value: amount}("");
        if (!success) revert TransferFailed();

        emit CommissionWithdrawn(to, amount);
    }
}