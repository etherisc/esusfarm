// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

import {Location, RiskId, Str, Timestamp} from "./Types.sol";

contract CropProduct {
    
    uint256 public riskCounter;

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
        return RiskId.wrap(bytes8(keccak256(abi.encode(riskCounter))));
    }
}