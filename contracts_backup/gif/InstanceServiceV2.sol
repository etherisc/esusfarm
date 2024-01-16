// SPDX-License-Identifier: MIT
pragma solidity 0.8.2;

// dummy contract to access instance service using web3.py
contract InstanceServiceV2 {
    // States
    enum PolicyFlowState {Started, Active, Finished}
    enum ApplicationState {Applied, Revoked, Underwritten, Declined}
    enum PolicyState {Active, Expired, Closed}
    enum ClaimState {Applied, Confirmed, Declined, Closed}
    enum PayoutState {Expected, PaidOut}

    // Objects
    struct Metadata {
        address owner;
        uint256 productId;
        PolicyFlowState state;
        bytes data;
        uint256 createdAt;
        uint256 updatedAt;
    }

    struct Application {
        ApplicationState state;
        uint256 premiumAmount;
        uint256 sumInsuredAmount;
        bytes data; 
        uint256 createdAt;
        uint256 updatedAt;
    }

    struct Policy {
        PolicyState state;
        uint256 premiumExpectedAmount;
        uint256 premiumPaidAmount;
        uint256 claimsCount;
        uint256 openClaimsCount;
        uint256 payoutMaxAmount;
        uint256 payoutAmount;
        uint256 createdAt;
        uint256 updatedAt;
    }

    struct Claim {
        ClaimState state;
        uint256 claimAmount;
        uint256 paidAmount;
        bytes data;
        uint256 createdAt;
        uint256 updatedAt;
    }

    struct Payout {
        uint256 claimId;
        PayoutState state;
        uint256 amount;
        bytes data;
        uint256 createdAt;
        uint256 updatedAt;
    }

    function getMetadata(bytes32 processId) external view returns(Metadata memory metadata) {}
    function getApplication(bytes32 processId) external view returns(Application memory application) {}
    function getPolicy(bytes32 processId) external view returns(Policy memory policy) {}

    function claims(bytes32 processId) external view returns(uint256 numberOfClaims) {}
    function getClaim(bytes32 processId, uint256 claimId) external view returns (Claim memory claim) {}

    function payouts(bytes32 processId) external view returns(uint256 numberOfPayouts) {}
    function getPayout(bytes32 processId, uint256 payoutId) external view returns (Payout memory payout) {}
}