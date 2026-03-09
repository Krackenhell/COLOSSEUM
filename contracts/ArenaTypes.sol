// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

/**
 * @title IArenaTypes
 * @notice Shared types, events, and custom errors for AI Trading Arena
 */
interface IArenaTypes {

    // ===================== ENUMS =====================

    enum ArenaState {
        Idle,       // arena created, waiting for participants
        Active,     // trading in progress
        Finished    // arena resolved, rewards distributed
    }

    enum TokenId {
        AVAX,   // 0
        BTC,    // 1
        ETH     // 2
    }

    enum OrderSide {
        Buy,
        Sell
    }

    // ===================== STRUCTS =====================

    /// @notice Configuration for an arena (set once on creation)
    struct ArenaConfig {
        uint256 entryDeposit;       // AVAX deposit to enter (wei)
        uint256 maxParticipants;    // max players per battle
        uint256 minParticipants;    // min players to start
        uint256 duration;           // battle duration in seconds
        uint256 cooldown;           // min seconds between battles in same arena
        uint16  commissionBps;      // owner commission in basis points (e.g. 500 = 5%)
    }

    /// @notice Runtime state for an arena
    struct ArenaInfo {
        ArenaConfig config;
        ArenaState  state;
        uint256     currentBattleId;
        uint256     startTime;          // timestamp when current battle started
        uint256     lastEndTime;        // timestamp when last battle ended
        uint256     participantCount;   // current battle participants
        uint256     totalDeposits;      // total AVAX deposited in current battle
        bool        exists;
    }

    /// @notice Player info within a battle
    struct Player {
        address owner;          // human wallet (deposited funds)
        address agent;          // agent wallet (trades)
        string  agentName;      // display name
        int256  realizedPnl;    // closed positions profit/loss (virtual USDT, 18 dec)
        uint256 virtualUSDT;    // remaining virtual USDT balance
        bool    active;         // is in current battle
    }

    /// @notice Open position
    struct Position {
        TokenId tokenId;
        uint256 entryPrice;     // price at open (18 decimals)
        uint256 amount;         // token amount (18 decimals)
        uint256 usdtSpent;      // how much virtual USDT was spent to open
        bool    isOpen;
    }

    /// @notice FIFO queue entry
    struct QueueEntry {
        address owner;
        address agent;
        string  agentName;
    }

    // ===================== EVENTS =====================

    event ArenaCreated(uint256 indexed arenaId, ArenaConfig config);
    event ArenaDeleted(uint256 indexed arenaId);

    event PlayerJoined(uint256 indexed arenaId, uint256 indexed battleId, address indexed owner, address agent, string agentName);
    event PlayerQueued(uint256 indexed arenaId, address indexed owner, address agent, string agentName);

    event BattleStarted(uint256 indexed arenaId, uint256 indexed battleId, uint256 participantCount, uint256 startTime);
    event BattleEnded(uint256 indexed arenaId, uint256 indexed battleId, address winner, int256 winnerPnl, uint256 reward);

    event OrderExecuted(uint256 indexed arenaId, uint256 indexed battleId, address indexed agent, TokenId tokenId, uint256 price, uint256 amount, OrderSide side);
    event OrderClosed(uint256 indexed arenaId, uint256 indexed battleId, address indexed agent, TokenId tokenId, uint256 closePrice, int256 pnl);

    event RewardClaimed(address indexed user, uint256 amount);
    event CommissionWithdrawn(address indexed to, uint256 amount);

    // ===================== CUSTOM ERRORS =====================

    error NotOwner();
    error NotBackend();
    error NotAgent();
    error ArenaDoesNotExist();
    error ArenaAlreadyActive();
    error ArenaNotActive();
    error ArenaNotFinished();
    error ArenaNotIdle();
    error ArenaCooldownNotMet(uint256 readyAt);
    error NotEnoughParticipants(uint256 current, uint256 required);
    error ArenaFull();
    error AlreadyJoined();
    error AgentAlreadyRegistered();
    error OwnerCannotBeAgent();
    error AgentCannotBeOwner();
    error InsufficientDeposit(uint256 sent, uint256 required);
    error InsufficientVirtualBalance(uint256 available, uint256 required);
    error PositionNotOpen();
    error PositionAlreadyOpen();
    error NoRewardToClaim();
    error TransferFailed();
    error DurationNotElapsed(uint256 endsAt);
    error InvalidCommission();
    error InvalidParticipants();
    error ZeroAddress();
    error QueueEmpty();
    error ArenaHasActiveBattle();
    error InsufficientContractBalance(uint256 available, uint256 required);
}