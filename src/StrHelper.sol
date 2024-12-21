// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

type Str is bytes32;

contract StrHelper {

    error StringTooLong(string str);
    error InvalidShortString();

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