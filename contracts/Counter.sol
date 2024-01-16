// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.2;

contract Counter {

    uint256 public value;

    function setValue(uint256 newValue) external {
        value = newValue;
    }
}