// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Script, console} from "forge-std/Script.sol";
import {Product} from "../../src/mock/Product.sol";

contract MocksDeployScript is Script {
    Product public product;

    function run() public {
        uint256 privateKey = vm.envUint("ETH_PRIVATE_KEY");
        console.log("Using deployer", vm.envAddress("ETH_ADDRESS"));

        vm.startBroadcast(privateKey);
        product = new Product();
        vm.stopBroadcast();

        console.log("Counter deployed", address(product));
    }
}
