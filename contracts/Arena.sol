// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import "./ArenaTypes.sol";
import "./LibQueue.sol";
import "./ArenaVault.sol";

/**
 * @title TradingArena
 * @author AI Trading Arena Team
 * @notice Main contract for AI agent trading competitions on Avalanche
 *
 * CHANGES v2:
 * - TokenHolding replaces Position: agents can accumulate positions (multiple buys)
 * - Weighted average entry price on each additional buy
 * - Partial close: closeOrder accepts sellAmount param
 * - endBattle accepts currentPrices[3] to mark-to-market open positions
 * - endBattle cleanup: only clears battle participants, not queue registrations
 * - joinArena: blocks entry when arena state == Finished (queued before _reset)
 */
contract TradingArena is ArenaVault {
    using LibQueue for LibQueue.Queue;

    // ===================== CONSTANTS =====================

    uint256 public constant VIRTUAL_STARTING_BALANCE = 10_000 * 1e18;
    uint256 public constant MAX_COMMISSION_BPS = 2000;
    uint8   public constant TOKEN_COUNT = 3; // AVAX=0, BTC=1, ETH=2

    // ===================== ROLES =====================

    address public owner;
    address public backend;

    // ===================== NEW: TOKEN HOLDING STRUCT =====================

    /**
     * @notice Replaces single Position. Tracks accumulated holdings per token.
     * @dev avgEntryPrice is weighted average across all buys (18 decimals).
     *      balance = total token units held (18 decimals).
     *      totalSpent = total virtual USDT spent (18 decimals) — used for risk tracking.
     */
    struct TokenHolding {
        uint256 balance;        // total token units held (18 dec)
        uint256 avgEntryPrice;  // weighted avg entry price (18 dec)
        uint256 totalSpent;     // total virtual USDT spent on current holding
    }

    // ===================== ARENA STORAGE =====================

    uint256 public nextArenaId;

    mapping(uint256 => ArenaInfo)       public arenas;
    mapping(uint256 => LibQueue.Queue)  private arenaQueues;

    /// arenaId => battleId => ownerAddress => Player
    mapping(uint256 => mapping(uint256 => mapping(address => Player))) public players;

    /// arenaId => battleId => agentAddress => tokenId => TokenHolding
    mapping(uint256 => mapping(uint256 => mapping(address => mapping(TokenId => TokenHolding)))) public holdings;

    /// arenaId => battleId => participants list
    mapping(uint256 => mapping(uint256 => address[])) public battleParticipants;

    /// Role tracking
    mapping(address => bool)    public isRegisteredAgent;
    mapping(address => bool)    public isRegisteredOwner;
    mapping(address => address) public agentToOwner;

    // ===================== MODIFIERS =====================

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    modifier onlyBackend() {
        if (msg.sender != backend) revert NotBackend();
        _;
    }

    modifier onlyAgent(uint256 arenaId) {
        address playerOwner = agentToOwner[msg.sender];
        if (playerOwner == address(0)) revert NotAgent();
        uint256 battleId = arenas[arenaId].currentBattleId;
        if (!players[arenaId][battleId][playerOwner].active) revert NotAgent();
        _;
    }

    modifier arenaExists(uint256 arenaId) {
        if (!arenas[arenaId].exists) revert ArenaDoesNotExist();
        _;
    }

    // ===================== CONSTRUCTOR =====================

    constructor(address _backend) {
        if (_backend == address(0)) revert ZeroAddress();
        owner = msg.sender;
        backend = _backend;
    }

    // ===================== OWNER FUNCTIONS =====================

    /**
     * @notice Creates a new arena
     */
    function createArena(ArenaConfig calldata config) external onlyOwner returns (uint256 arenaId) {
        if (config.maxParticipants < 2) revert InvalidParticipants();
        if (config.minParticipants < 2 || config.minParticipants > config.maxParticipants) revert InvalidParticipants();
        if (config.commissionBps > MAX_COMMISSION_BPS) revert InvalidCommission();
        if (config.entryDeposit == 0) revert InsufficientDeposit(0, 1);

        arenaId = nextArenaId++;
        ArenaInfo storage arena = arenas[arenaId];
        arena.config = config;
        arena.state  = ArenaState.Idle;
        arena.exists = true;

        emit ArenaCreated(arenaId, config);
    }

    /**
     * @notice Deletes an arena and refunds queued players
     * @dev Cannot delete while a battle is Active.
     *      Queued players are refunded via pendingReward (pull-pattern).
     */
    function deleteArena(uint256 arenaId) external onlyOwner arenaExists(arenaId) {
        ArenaInfo storage arena = arenas[arenaId];
        if (arena.state == ArenaState.Active) revert ArenaHasActiveBattle();

        LibQueue.Queue storage queue = arenaQueues[arenaId];
        while (!queue.isEmpty()) {
            QueueEntry memory entry = queue.dequeue();
            // Unregister agent/owner so they can reuse addresses
            isRegisteredAgent[entry.agent]  = false;
            isRegisteredOwner[entry.owner]  = false;
            agentToOwner[entry.agent]       = address(0);
            // Refund via pull-pattern (safe, avoids DoS)
            _creditReward(entry.owner, arena.config.entryDeposit);
        }

        // Also unregister current Idle battle participants (not started yet)
        if (arena.state == ArenaState.Idle) {
            uint256 battleId = arena.currentBattleId;
            address[] storage participants = battleParticipants[arenaId][battleId];
            for (uint256 i = 0; i < participants.length; i++) {
                address pOwner = participants[i];
                Player storage p = players[arenaId][battleId][pOwner];
                isRegisteredAgent[p.agent]  = false;
                isRegisteredOwner[pOwner]   = false;
                agentToOwner[p.agent]       = address(0);
                p.active = false;
                _creditReward(pOwner, arena.config.entryDeposit);
            }
        }

        arena.exists = false;
        emit ArenaDeleted(arenaId);
    }

    function setBackend(address _backend) external onlyOwner {
        if (_backend == address(0)) revert ZeroAddress();
        backend = _backend;
    }

    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert ZeroAddress();
        owner = newOwner;
    }

    /// @notice Owner withdraws accumulated commission to specified address
    function withdrawCommission(address to) external onlyOwner {
        _withdrawCommission(to);
    }

    // ===================== PLAYER FUNCTIONS =====================

    /**
     * @notice Player joins an arena with their AI agent
     * @dev If Idle + space → joins current battle directly.
     *      If Active / full / Finished → enters FIFO queue for NEXT battle.
     * @param arenaId Arena to join
     * @param agentAddress Agent wallet address (the bot)
     * @param agentName Display name
     */
    function joinArena(
        uint256 arenaId,
        address agentAddress,
        string calldata agentName
    ) external payable arenaExists(arenaId) {
        ArenaInfo storage arena = arenas[arenaId];

        if (msg.value < arena.config.entryDeposit) {
            revert InsufficientDeposit(msg.value, arena.config.entryDeposit);
        }
        if (agentAddress == address(0))             revert ZeroAddress();
        if (agentAddress == msg.sender)             revert OwnerCannotBeAgent();
        if (isRegisteredAgent[msg.sender])          revert AgentCannotBeOwner();
        if (isRegisteredOwner[agentAddress])        revert OwnerCannotBeAgent();
        if (isRegisteredAgent[agentAddress])        revert AgentAlreadyRegistered();

        uint256 battleId = arena.currentBattleId;
        if (players[arenaId][battleId][msg.sender].active) revert AlreadyJoined();

        // Register immediately
        isRegisteredAgent[agentAddress] = true;
        isRegisteredOwner[msg.sender] = true;
        agentToOwner[agentAddress] = msg.sender;

        bool joinedDirectly = (arena.state == ArenaState.Idle &&
                               arena.participantCount < arena.config.maxParticipants);

        if (joinedDirectly) {
            _addPlayerToBattle(arenaId, battleId, msg.sender, agentAddress, agentName);
            arena.participantCount++;
            arena.totalDeposits += arena.config.entryDeposit;
            emit PlayerJoined(arenaId, battleId, msg.sender, agentAddress, agentName);
        } else {
            arenaQueues[arenaId].enqueue(QueueEntry({
                owner: msg.sender,
                agent: agentAddress,
                agentName: agentName
            }));
            emit PlayerQueued(arenaId, msg.sender, agentAddress, agentName);
        }

        // Refund excess
        uint256 excess = msg.value - arena.config.entryDeposit;
        if (excess > 0) {
            (bool ok,) = payable(msg.sender).call{value: excess}("");
            if (!ok) revert TransferFailed();
        }
    }

    // ===================== BACKEND FUNCTIONS =====================

    /**
     * @notice Backend starts a battle
     */
    function startBattle(uint256 arenaId) external onlyBackend arenaExists(arenaId) {
        ArenaInfo storage arena = arenas[arenaId];
        if (arena.state != ArenaState.Idle) revert ArenaNotIdle();

        if (arena.lastEndTime > 0 &&
            block.timestamp < arena.lastEndTime + arena.config.cooldown) {
            revert ArenaCooldownNotMet(arena.lastEndTime + arena.config.cooldown);
        }

        // Pull from queue to fill remaining spots
        _fillFromQueue(arenaId, arena.currentBattleId);

        if (arena.participantCount < arena.config.minParticipants) {
            revert NotEnoughParticipants(arena.participantCount, arena.config.minParticipants);
        }

        arena.state = ArenaState.Active;
        arena.startTime = block.timestamp;

        emit BattleStarted(arenaId, arena.currentBattleId, arena.participantCount, block.timestamp);
    }

    /**
     * @notice Backend ends a battle, marks-to-market all open positions, picks winner
     * @dev currentPrices must be ordered: [avaxPrice, btcPrice, ethPrice] (18 decimals)
     *      Backend fetches live oracle prices off-chain and passes them here.
     *      This correctly values all unsold token holdings at end of battle.
     * @param arenaId Arena to end
     * @param currentPrices Live prices for all 3 tokens (18 decimals each)
     */
    function endBattle(
        uint256 arenaId,
        uint256[3] calldata currentPrices
    ) external onlyBackend arenaExists(arenaId) {
        ArenaInfo storage arena = arenas[arenaId];
        if (arena.state != ArenaState.Active) revert ArenaNotActive();

        uint256 endsAt = arena.startTime + arena.config.duration;
        if (block.timestamp < endsAt) revert DurationNotElapsed(endsAt);

        uint256 battleId = arena.currentBattleId;
        address[] storage participants = battleParticipants[arenaId][battleId];

        address winner = address(0);
        int256  bestPnl = type(int256).min;

        for (uint256 i = 0; i < participants.length; i++) {
            address pOwner = participants[i];
            Player storage p = players[arenaId][battleId][pOwner];

            // --- Mark-to-market: value all open token holdings ---
            uint256 openPositionsValue = 0;
            for (uint8 t = 0; t < TOKEN_COUNT; t++) {
                TokenHolding storage h = holdings[arenaId][battleId][p.agent][TokenId(t)];
                if (h.balance > 0) {
                    // tokenValue (USDT) = balance * currentPrice / 1e18
                    openPositionsValue += (h.balance * currentPrices[t]) / 1e18;
                }
            }

            // totalPnl = realized + free USDT + open holdings value - starting balance
            int256 totalPnl = p.realizedPnl
                + int256(p.virtualUSDT)
                + int256(openPositionsValue)
                - int256(VIRTUAL_STARTING_BALANCE);

            if (totalPnl > bestPnl) {
                bestPnl = totalPnl;
                winner  = pOwner;
            }

            // Cleanup: unregister battle participants only (NOT queue registrations)
            isRegisteredAgent[p.agent]  = false;
            isRegisteredOwner[pOwner]   = false;
            agentToOwner[p.agent]       = address(0);
            p.active                    = false;
        }

        // Distribute prize pool
        uint256 totalPool  = arena.totalDeposits;
        uint256 commission = (totalPool * arena.config.commissionBps) / 10000;
        uint256 reward     = totalPool - commission;

        if (winner != address(0)) _creditReward(winner, reward);
        _addCommission(commission);

        arena.state       = ArenaState.Finished;
        arena.lastEndTime = block.timestamp;

        emit BattleEnded(arenaId, battleId, winner, bestPnl, reward);

        _resetForNextBattle(arenaId);
    }

    // ===================== AGENT TRADING FUNCTIONS =====================

    /**
     * @notice Agent buys tokens with virtual USDT (can be called multiple times)
     * @dev Each call adds to existing holding with weighted average price recalculation.
     *      Formula: newAvgPrice = (oldBalance * oldAvg + newAmount * price) / (oldBalance + newAmount)
     * @param arenaId Arena ID
     * @param tokenId Token to buy (0=AVAX, 1=BTC, 2=ETH)
     * @param price Current token price in USDT (18 decimals) — provided by backend/oracle
     * @param usdtAmount Amount of virtual USDT to spend (18 decimals)
     */
    function executeOrder(
        uint256 arenaId,
        TokenId tokenId,
        uint256 price,
        uint256 usdtAmount
    ) external onlyAgent(arenaId) {
        if (price == 0) revert InsufficientDeposit(0, 1); // reuse error for zero price
        ArenaInfo storage arena = arenas[arenaId];
        if (arena.state != ArenaState.Active) revert ArenaNotActive();

        uint256 battleId   = arena.currentBattleId;
        address playerOwner = agentToOwner[msg.sender];
        Player storage player = players[arenaId][battleId][playerOwner];

        if (player.virtualUSDT < usdtAmount) {
            revert InsufficientVirtualBalance(player.virtualUSDT, usdtAmount);
        }

        // tokenAmount = usdtAmount * 1e18 / price
        uint256 tokenAmount = (usdtAmount * 1e18) / price;

        TokenHolding storage h = holdings[arenaId][battleId][msg.sender][tokenId];

        // Weighted average entry price
        if (h.balance == 0) {
            h.avgEntryPrice = price;
        } else {
            // newAvg = (oldBalance * oldAvg + tokenAmount * price) / (oldBalance + tokenAmount)
            h.avgEntryPrice = (h.balance * h.avgEntryPrice + tokenAmount * price)
                              / (h.balance + tokenAmount);
        }

        h.balance    += tokenAmount;
        h.totalSpent += usdtAmount;

        player.virtualUSDT -= usdtAmount;

        emit OrderExecuted(arenaId, battleId, msg.sender, tokenId, price, tokenAmount, OrderSide.Buy);
    }

    /**
     * @notice Agent sells tokens back to virtual USDT (partial or full close)
     * @dev PnL per unit = closePrice - avgEntryPrice
     *      Total PnL = (closePrice - avgEntryPrice) * sellAmount / 1e18
     *      Pass type(uint256).max to close the entire holding.
     * @param arenaId Arena ID
     * @param tokenId Token to sell
     * @param closePrice Current token price (18 decimals) — provided by backend/oracle
     * @param sellAmount Token units to sell (18 decimals). type(uint256).max = sell all
     */
    function closeOrder(
        uint256 arenaId,
        TokenId tokenId,
        uint256 closePrice,
        uint256 sellAmount
    ) external onlyAgent(arenaId) {
        if (closePrice == 0) revert InsufficientDeposit(0, 1);
        ArenaInfo storage arena = arenas[arenaId];
        if (arena.state != ArenaState.Active) revert ArenaNotActive();

        uint256 battleId    = arena.currentBattleId;
        address playerOwner = agentToOwner[msg.sender];
        Player storage player = players[arenaId][battleId][playerOwner];
        TokenHolding storage h = holdings[arenaId][battleId][msg.sender][tokenId];

        if (h.balance == 0) revert PositionNotOpen();

        // Clamp to max balance if sellAmount == type(uint256).max
        if (sellAmount == type(uint256).max || sellAmount > h.balance) {
            sellAmount = h.balance;
        }

        // proceeds = sellAmount * closePrice / 1e18
        uint256 proceeds = (sellAmount * closePrice) / 1e18;

        // pnl = (closePrice - avgEntryPrice) * sellAmount / 1e18
        int256 pnl = (int256(closePrice) - int256(h.avgEntryPrice))
                     * int256(sellAmount) / int256(1e18);

        // Update holding
        // proportional totalSpent reduction
        uint256 spentReduction = (h.totalSpent * sellAmount) / h.balance;
        h.balance -= sellAmount;
        h.totalSpent -= spentReduction;
        if (h.balance == 0) h.avgEntryPrice = 0;

        // Update player state
        player.virtualUSDT  += proceeds;
        player.realizedPnl  += pnl;

        emit OrderClosed(arenaId, battleId, msg.sender, tokenId, closePrice, pnl);
    }

    // ===================== VIEW FUNCTIONS =====================

    function getArena(uint256 arenaId) external view returns (ArenaInfo memory) {
        return arenas[arenaId];
    }

    function getPlayer(uint256 arenaId, uint256 battleId, address playerOwner)
        external view returns (Player memory)
    {
        return players[arenaId][battleId][playerOwner];
    }

    function getHolding(uint256 arenaId, uint256 battleId, address agent, TokenId tokenId)
        external view returns (TokenHolding memory)
    {
        return holdings[arenaId][battleId][agent][tokenId];
    }

    function getBattleParticipants(uint256 arenaId, uint256 battleId)
        external view returns (address[] memory)
    {
        return battleParticipants[arenaId][battleId];
    }

    function getQueueLength(uint256 arenaId) external view returns (uint256) {
        return arenaQueues[arenaId].length();
    }

    /**
     * @notice Calculate a player's current total PnL using provided current prices
     * @dev Frontend calls this with live prices for real-time leaderboard
     */
    function getPlayerTotalPnl(
        uint256 arenaId,
        uint256 battleId,
        address playerOwner,
        uint256[3] calldata currentPrices
    ) external view returns (int256 totalPnl) {
        Player storage p = players[arenaId][battleId][playerOwner];
        uint256 openValue = 0;
        for (uint8 t = 0; t < TOKEN_COUNT; t++) {
            TokenHolding storage h = holdings[arenaId][battleId][p.agent][TokenId(t)];
            if (h.balance > 0) {
                openValue += (h.balance * currentPrices[t]) / 1e18;
            }
        }
        totalPnl = p.realizedPnl
            + int256(p.virtualUSDT)
            + int256(openValue)
            - int256(VIRTUAL_STARTING_BALANCE);
    }

    // ===================== INTERNAL FUNCTIONS =====================

    function _addPlayerToBattle(
        uint256 arenaId,
        uint256 battleId,
        address playerOwner,
        address agentAddress,
        string memory agentName
    ) internal {
        players[arenaId][battleId][playerOwner] = Player({
            owner:       playerOwner,
            agent:       agentAddress,
            agentName:   agentName,
            realizedPnl: 0,
            virtualUSDT: VIRTUAL_STARTING_BALANCE,
            active:      true
        });
        battleParticipants[arenaId][battleId].push(playerOwner);
    }

    function _fillFromQueue(uint256 arenaId, uint256 battleId) internal {
        ArenaInfo storage arena = arenas[arenaId];
        LibQueue.Queue storage queue = arenaQueues[arenaId];
        while (!queue.isEmpty() && arena.participantCount < arena.config.maxParticipants) {
            QueueEntry memory entry = queue.dequeue();
            _addPlayerToBattle(arenaId, battleId, entry.owner, entry.agent, entry.agentName);
            arena.participantCount++;
            arena.totalDeposits += arena.config.entryDeposit;
            emit PlayerJoined(arenaId, battleId, entry.owner, entry.agent, entry.agentName);
        }
    }

    function _resetForNextBattle(uint256 arenaId) internal {
        ArenaInfo storage arena = arenas[arenaId];
        arena.currentBattleId++;
        arena.participantCount = 0;
        arena.totalDeposits    = 0;
        arena.startTime        = 0;
        arena.state            = ArenaState.Idle;

        // Pre-fill next battle from queue
        _fillFromQueue(arenaId, arena.currentBattleId);
    }

    receive() external payable {}
}
