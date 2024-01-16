// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.2;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract EXOF is 
    ERC20 
{

    string public constant NAME = "eF.CFA - Accounting Token";
    string public constant SYMBOL = "EXOF";
    uint8 public constant DECIMALS = 2;

    uint256 public constant INITIAL_SUPPLY = 10**24;

    constructor()
        ERC20(NAME, SYMBOL)
    {
        _mint(
            _msgSender(),
            INITIAL_SUPPLY
        );
    }

    function decimals() public pure override returns(uint8) {
        return DECIMALS;
    }
}
