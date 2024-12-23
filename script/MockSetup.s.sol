// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Script, console} from "forge-std/Script.sol";

import {AccountingToken} from "../src/AccountingToken.sol";
import {CropProduct} from "../src/CropProduct.sol";

contract MocksSetupScript is Script {
    AccountingToken public token;
    CropProduct public product;

    function run() public {
        uint256 privateKey = vm.envUint("ETH_PRIVATE_KEY");
        console.log("Using deployer", vm.envAddress("ETH_ADDRESS"));

        vm.startBroadcast(privateKey);
        token = new AccountingToken();
        product = new CropProduct();
        vm.stopBroadcast();

        console.log("Token deployed", address(token));
        console.log("Product deployed", address(product));
    }
}
