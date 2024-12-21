// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

contract AccountingToken {

    string public constant NAME = "Local Currency (Accounting Token)";
    string public constant SYMBOL = "LCA";
    uint8 public constant DECIMALS = 6;
    uint256 public constant INITIAL_SUPPLY = 10**12 * 10**DECIMALS;

    mapping(address => uint256) internal _balanceOf;
    mapping(address => mapping(address => uint256)) internal _allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    
    constructor() {
        _balanceOf[msg.sender] = INITIAL_SUPPLY;
        emit Transfer(address(0), msg.sender, INITIAL_SUPPLY);
    }

    function totalSupply() external view returns (uint256) { return INITIAL_SUPPLY; }

    function balanceOf(address account) external view returns (uint256) { 
        return _balanceOf[account];
    }

    function transfer(address to, uint256 value) external returns (bool) {
        require(_balanceOf[msg.sender] >= value, "Insufficient balance");
        _balanceOf[msg.sender] -= value;
        _balanceOf[to] += value;
        emit Transfer(msg.sender,to,value);
        return true;
    }

    function allowance(address owner, address spender) external view returns (uint256) {
        return _allowance[owner][spender];
    } 

    function approve(address spender, uint256 value) external returns (bool) {
        _allowance[msg.sender][spender] = value;
        emit Approval(msg.sender,spender,value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) external returns (bool) {
        require(_balanceOf[from] >= value, "Insufficient balance");
        require(_allowance[from][msg.sender] >= value, "Allowance exceeded");
        _allowance[from][msg.sender] -= value;
        _balanceOf[from] -= value;
        _balanceOf[to] += value;
        emit Transfer(from,to,value);
        return true;
    }

    function name() external view returns (string memory) { return NAME; }

    function symbol() external view returns (string memory) { return SYMBOL; }

    function decimals() public pure returns(uint8) { return DECIMALS; }
}
