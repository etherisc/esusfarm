// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.2;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

contract Mapper is 
    Ownable
{
    uint16 [] private _ids;
    mapping(uint16 => bytes32) private _processId;

    constructor() Ownable() { }

    function ids() external view returns (uint256) { return _ids.length; }
    function getId(uint256 idx) external view returns (uint16 id) { return _ids[idx]; }
    function getProcessId(uint16 id) external view returns (bytes32 processId) { return _processId[id]; }

    function setProcessId(uint16 id, bytes32 processId)
        external
        onlyOwner()
    {
        require(_processId[id] == bytes32(0), "ERROR:MPR-001:ID_ALREADY_SET");
        _processId[id] = processId;
        _ids.push(id);
    }
}
