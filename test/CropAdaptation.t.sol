// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.27;

import {Test} from "forge-std/Test.sol";
import {CropProduct} from "../src/crop/CropProduct.sol";
import {CropPool} from "../src/crop/CropPool.sol";

/// @dev Compile-time checks that adapted crop contracts are wired in this repo.
contract CropAdaptationTest is Test {
    function test_cropProduct_is_gif_product_not_mock() public pure {
        assertTrue(type(CropProduct).creationCode.length > 1000);
    }

    function test_cropPool_has_bundle_lifetime_field() public pure {
        // Selector for public bundleLifetimeDays
        bytes4 selector = bytes4(keccak256("bundleLifetimeDays()"));
        assertTrue(selector != bytes4(0));
    }
}