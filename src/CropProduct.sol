// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

import {Amount, Location, NftId, RiskId, Str, Timestamp} from "./Types.sol";

contract CropProduct {

    error StringTooLong(string str);
    error InvalidShortString();

    uint256 public riskCounter;
    uint96 public policyNftCounter = 100101;

    mapping(Str id => RiskId riskId) internal _riskId;

    function createSeason(
        Str seasonId,
        uint16 year,
        Str name,
        Str seasonStart, // ISO 8601 date, eg "2025-02-18"
        Str seasonEnd,
        uint16 seasonDays
    )
        external
    { }

    function createLocation(
        Str locationId,
        int32 latitude,
        int32 longitude
    )
        external
        returns (Location location)
    { }

    function createCrop(Str crop)
        external
    { }

    function createRisk(
        Str id,
        Str seasonId,
        Str locationId,
        Str crop,
        Timestamp seasonEndAt
    )
        external
        returns (RiskId riskId)
    {
        riskCounter++;
        riskId = RiskId.wrap(bytes8(keccak256(abi.encode(riskCounter))));
        _riskId[id] = riskId;
    }

    function createPolicy(
        address policyHolder,
        RiskId riskId,
        Timestamp activateAt,
        Amount sumInsuredAmount,
        Amount premiumAmount
    )
        external
        returns (NftId policyNftId)
    { 
        policyNftCounter++;
        return NftId.wrap(policyNftCounter);
    }

    function getRiskId(Str id)
        external
        view
        returns (RiskId riskId)
    { 
        return _riskId[id]; 
    }

    /// @dev converts the provided string into a short string.
    /// code from OZ ShortStrings.toShortString
    function toStr(string memory str) public pure returns (Str) {
        bytes memory bstr = bytes(str);
        if (bstr.length > 31) {
            revert StringTooLong(str);
        }
        return Str.wrap(bytes32(uint256(bytes32(bstr)) | bstr.length));
    }

    /// @dev converts the provided short string into a string.
    /// code from OZ ShortStrings.toString
    function toString(Str sstr) public pure returns (string memory) {
        uint256 len = length(sstr);
        // using `new string(len)` would work locally but is not memory safe.
        string memory str = new string(32);
        assembly ("memory-safe") {
            mstore(str, len)
            mstore(add(str, 0x20), sstr)
        }
        return str;
    }

    /// @dev returns the length of the provided short string.
    /// code from OZ ShortStrings.byteLength
    function length(Str sstr) public pure returns (uint256) {
        uint256 result = uint256(Str.unwrap(sstr)) & 0xFF;
        if (result > 31) {
            revert InvalidShortString();
        }
        return result;
    }
}