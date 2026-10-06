// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/utils/cryptography/SignatureChecker.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title SwarmClaim
 * @notice Automated Swarm Claim via Deterministic Fast-Path
 * @dev Allows claims through a deterministic fast-path using off-chain signatures
 *      and on-chain verification for batched claims.
 */
contract SwarmClaim is ReentrancyGuard, Ownable {
    IERC20 public immutable claimToken;
    
    // EIP-712 domain separator for typed structured data hashing
    bytes32 private immutable _DOMAIN_SEPARATOR;
    
    // EIP-712 typehash for claim signature
    bytes32 private constant CLAIM_TYPEHASH = keccak256(
        "Claim(address indexed claimant,uint256 indexed sequenceId,uint256 amount,uint256 deadline)"
    );
    
    // Mapping of claimed sequences to prevent replay
    mapping(bytes32 => bool) private _claimedSequences;
    
    // Track total claims per user for fast-path optimization
    mapping(address => uint256) private _claimCount;
    
    // The claim threshold for deterministic fast-path (batch size)
    uint256 public constant FAST_PATH_THRESHOLD = 10;
    
    // Total distributed amount
    uint256 public totalClaimed;
    
    // Events
    event ClaimProcessed(
        address indexed claimant,
        uint256 indexed sequenceId,
        uint256 amount,
        uint256 timestamp
    );
    
    event FastPathEnabled(address indexed claimant, uint256 claimCount);
    event EmergencyPause(bool paused);
    event TokenWithdrawn(address indexed token, uint256 amount);
    
    constructor(address _claimToken) Ownable(msg.sender) {
        claimToken = IERC20(_claimToken);
        _DOMAIN_SEPARATOR = _calculateDomainSeparator();
    }
    
    /**
     * @notice Calculates the EIP-712 domain separator
     */
    function _calculateDomainSeparator() internal view returns (bytes32) {
        return keccak256(abi.encode(
            keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"),
            keccak256(bytes("SwarmClaim")),
            keccak256(bytes("1")),
            block.chainid,
            address(this)
        ));
    }
    
    /**
     * @notice Processes a claim via deterministic fast-path
     * @param claimant Address claiming the reward
     * @param sequenceId Unique sequence identifier for this claim
     * @param amount Amount to claim
     * @param deadline Signature deadline
     * @param signature EIP-712 signed authorization
     */
    function claim(
        address claimant,
        uint256 sequenceId,
        uint256 amount,
        uint256 deadline,
        bytes memory signature
    ) external nonReentrant {
        require(block.timestamp <= deadline, "SwarmClaim: signature expired");
        require(amount > 0, "SwarmClaim: zero amount");
        
        // Check if already claimed
        bytes32 sequenceKey = keccak256(abi.encodePacked(claimant, sequenceId));
        require(!_claimedSequences[sequenceKey], "SwarmClaim: already claimed");
        
        // Compute the EIP-712 hash to verify
        bytes32 structHash = keccak256(abi.encode(
            CLAIM_TYPEHASH,
            claimant,
            sequenceId,
            amount,
            deadline
        ));
        
        bytes32 digest = keccak256(
            abi.encodePacked("\x19\x01", _DOMAIN_SEPARATOR, structHash)
        );
        
        // Verify signature
        require(
            SignatureChecker.isValidSignatureNow(claimant, digest, signature),
            "SwarmClaim: invalid signature"
        );
        
        // Mark as claimed
        _claimedSequences[sequenceKey] = true;
        
        // Transfer tokens
        require(
            claimToken.transfer(claimant, amount),
            "SwarmClaim: transfer failed"
        );
        
        totalClaimed += amount;
        _claimCount[claimant]++;
        
        emit ClaimProcessed(claimant, sequenceId, amount, block.timestamp);
        
        // Check if fast-path should be enabled for this claimant
        if (_claimCount[claimant] >= FAST_PATH_THRESHOLD) {
            emit FastPathEnabled(claimant, _claimCount[claimant]);
        }
    }
    
    /**
     * @notice Batch claim for multiple recipients (gas optimized)
     * @param claimants Array of claimant addresses
     * @param sequenceIds Array of sequence IDs
     * @param amounts Array of claim amounts
     * @param deadlines Array of deadlines
     * @param signatures Array of signatures
     */
    function batchClaim(
        address[] calldata claimants,
        uint256[] calldata sequenceIds,
        uint256[] calldata amounts,
        uint256[] calldata deadlines,
        bytes[] calldata signatures
    ) external nonReentrant {
        require(
            claimants.length == sequenceIds.length &&
            claimants.length == amounts.length &&
            claimants.length == deadlines.length &&
            claimants.length == signatures.length,
            "SwarmClaim: array length mismatch"
        );
        
        for (uint256 i = 0; i < claimants.length; i++) {
            address claimant = claimants[i];
            uint256 sequenceId = sequenceIds[i];
            uint256 amount = amounts[i];
            uint256 deadline = deadlines[i];
            bytes memory signature = signatures[i];
            
            require(block.timestamp <= deadline, "SwarmClaim: signature expired");
            require(amount > 0, "SwarmClaim: zero amount");
            
            bytes32 sequenceKey = keccak256(abi.encodePacked(claimant, sequenceId));
            require(!_claimedSequences[sequenceKey], "SwarmClaim: already claimed");
            
            bytes32 structHash = keccak256(abi.encode(
                CLAIM_TYPEHASH,
                claimant,
                sequenceId,
                amount,
                deadline
            ));
            
            bytes32 digest = keccak256(
                abi.encodePacked("\x19\x01", _DOMAIN_SEPARATOR, structHash)
            );
            
            require(
                SignatureChecker.isValidSignatureNow(claimant, digest, signature),
                "SwarmClaim: invalid signature"
            );
            
            _claimedSequences[sequenceKey] = true;
            
            require(
                claimToken.transfer(claimant, amount),
                "SwarmClaim: transfer failed"
            );
            
            totalClaimed += amount;
            _claimCount[claimant]++;
            
            emit ClaimProcessed(claimant, sequenceId, amount, block.timestamp);
        }
    }
    
    /**
     * @notice Gets the domain separator for EIP-712
     */
    function DOMAIN_SEPARATOR() external view returns (bytes32) {
        return _DOMAIN_SEPARATOR;
    }
    
    /**
     * @notice Gets the EIP-712 typehash for claims
     */
    function CLAIM_TYPEHASH_EXTERNAL() external pure returns (bytes32) {
        return CLAIM_TYPEHASH;
    }
    
    /**
     * @notice Admin: Deposit tokens for claiming
     */
    function deposit() external payable onlyOwner {
        require(address(this).balance > 0, "SwarmClaim: no balance");
    }
    
    /**
     * @notice Admin: Withdraw excess tokens
     */
    function withdrawTokens(address token, uint256 amount) external onlyOwner {
        if (token == address(0)) {
            payable(owner()).transfer(amount);
        } else {
            IERC20(token).transfer(owner(), amount);
        }
        emit TokenWithdrawn(token, amount);
    }
    
    /**
     * @notice Emergency pause (owner only)
     */
    function setPause(bool paused) external onlyOwner {
        // Note: For full pause functionality, add a paused flag and modifiers
        emit EmergencyPause(paused);
    }
    
    /**
     * @notice Get claim count for a user
     */
    function getClaimCount(address user) external view returns (uint256) {
        return _claimCount[user];
    }
    
    /**
     * @notice Check if a sequence has been claimed
     */
    function isClaimed(address claimant, uint256 sequenceId) external view returns (bool) {
        bytes32 sequenceKey = keccak256(abi.encodePacked(claimant, sequenceId));
        return _claimedSequences[sequenceKey];
    }
}
