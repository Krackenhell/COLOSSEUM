// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title PaymentRegistry
 * @notice Minimal registration fee collector for Colosseum agent onboarding.
 *         Supports configurable fee (0 for test/MVP).
 */
contract PaymentRegistry {
    address public owner;
    uint256 public registrationFee;
    
    mapping(address => bool) public registered;
    mapping(address => uint256) public paidAmount;
    
    event Registered(address indexed wallet, uint256 amount, uint256 timestamp);
    event FeeUpdated(uint256 oldFee, uint256 newFee);
    event Withdrawn(address indexed to, uint256 amount);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor(uint256 _fee) {
        owner = msg.sender;
        registrationFee = _fee;
    }
    
    /**
     * @notice Register and pay the fee. If fee is 0, just registers.
     */
    function register() external payable {
        require(!registered[msg.sender], "Already registered");
        require(msg.value >= registrationFee, "Insufficient fee");
        
        registered[msg.sender] = true;
        paidAmount[msg.sender] = msg.value;
        
        emit Registered(msg.sender, msg.value, block.timestamp);
    }
    
    function setFee(uint256 _fee) external onlyOwner {
        uint256 old = registrationFee;
        registrationFee = _fee;
        emit FeeUpdated(old, _fee);
    }
    
    function withdraw() external onlyOwner {
        uint256 bal = address(this).balance;
        require(bal > 0, "No balance");
        payable(owner).transfer(bal);
        emit Withdrawn(owner, bal);
    }
    
    function isRegistered(address wallet) external view returns (bool) {
        return registered[wallet];
    }
}
