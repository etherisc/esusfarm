// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Test, console} from "forge-std/Test.sol";
import {AccountingToken} from "../src/AccountingToken.sol";
import {CropProduct} from "../src/CropProduct.sol";
import {NftId, RiskId, Str, Timestamp} from "../src/Types.sol";

contract CropProductTest is Test {
    address deployer = makeAddr("deployer");
    address personA = makeAddr("personA");
    address teller = makeAddr("teller");

    CropProduct public product;
    AccountingToken public token;

    function setUp() public {
        vm.startPrank(deployer);
        token = new AccountingToken();
        product = new CropProduct(token);
        vm.stopPrank();
    }

    function test_productSetUp() public {
        assertEq(NftId.unwrap(product.getNftId()), 208000205, "unexpected dummy product nft id");
        assertEq(product.getToken(), address(token), "unexpected token");
        assertEq(product.getInstance(), address(product), "unexpected dummy instance address");
        assertEq(product.getRiskSet(), address(product), "unexpected dummy risk set address");
    }

    function test_productRiskCreate() public {
        // GIVEN
        Str id = product.toStr("Ysi1SQUjfJgP");
        Str seasonId = product.toStr("pITRymZd5BPt");
        Str locationId = product.toStr("9kjFbDMG4Smh");
        Str crop = product.toStr("coffee");
        Timestamp seasonEndAt = Timestamp.wrap(uint40(block.timestamp + 90 days));

        // WHEN
        vm.startPrank(deployer);
        RiskId riskId = product.createRisk(id, seasonId, locationId, crop, seasonEndAt);
        vm.stopPrank();

        // THEN
        assertEq(RiskId.unwrap(product.getRiskId(id)), RiskId.unwrap(riskId), "unexpected risk id");
    }

    function test_productStringHelper() public view {
        // GIVEN
        string memory helloString = "hello world!";

        // WHEN
        Str helloStr = product.toStr(helloString);

        // THEN
        assertEq(product.toString(helloStr), helloString, "unexpected string (b)");
        assertEq(product.length(helloStr), 12, "unexpected string length");
    }
}
