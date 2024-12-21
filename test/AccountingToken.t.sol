// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Test, console} from "forge-std/Test.sol";
import {AccountingToken} from "../src/AccountingToken.sol";

contract AccountingTokenTest is Test {
    address deployer = makeAddr("deployer");
    address personA = makeAddr("personA");
    address teller = makeAddr("teller");

    AccountingToken public token;

    function setUp() public {
        vm.startPrank(deployer);
        token = new AccountingToken();
        vm.stopPrank();
    }

    function test_tokenMetadata() public view {
        assertEq(token.symbol(), "LCA", "unexpected token symbol");
    }

    function test_tokenInitialBalance() public view {
        assertEq(token.balanceOf(deployer), token.totalSupply(), "unexpected initial balance for deployer");
        assertEq(token.balanceOf(personA), 0, "unexpected initial blance for person a");
    }

    function test_transferFrom() public {
        // GIVEN
        vm.startPrank(deployer);
        token.approve(teller, 500);
        vm.stopPrank();

        assertEq(token.balanceOf(personA), 0, "unexpected balance for person a (after)");
        assertEq(token.allowance(deployer, teller), 500, "unexpected allowance for teller (after)");

        // WHEN
        vm.startPrank(teller);
        token.transferFrom(deployer, personA, 300);
        vm.stopPrank();

        // THEN
        assertEq(token.balanceOf(personA), 300, "unexpected balance for person a (after)");
        assertEq(token.balanceOf(deployer), token.totalSupply() - 300, "unexpected balance for deployer (after)");
        assertEq(token.allowance(deployer, teller), 200, "unexpected allowance for teller (after)");
    }
}
