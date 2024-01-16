// SPDX-License-Identifier: MIT
pragma solidity 0.8.2;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {IERC20Metadata} from "@openzeppelin/contracts/token/ERC20/extensions/IERC20Metadata.sol";
import {EnumerableSet} from "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";

import {Product} from "@etherisc/gif-interface/contracts/components/Product.sol";
import {IPolicy} from "@etherisc/gif-interface/contracts/modules/IPolicy.sol";

import {ArcModel} from "./ArcModel.sol";

contract ArcProduct is 
    Product, 
    AccessControl
{
    using EnumerableSet for EnumerableSet.Bytes32Set;

    bytes32 public constant NAME = "ArcIndexProduct";
    bytes32 public constant VERSION = "0.1";
    bytes32 public constant POLICY_FLOW = "PolicyDefaultFlow";

    mapping(bytes32 /* riskId */ => EnumerableSet.Bytes32Set /* processIds */) private _policies;
    bytes32 [] private _processIds; // useful for debugging, might need to get rid of this

    ArcModel private _model;
    IERC20Metadata private _token;

    event LogArcApplicationCreated(bytes32 processId, bytes32 beneficiaryId, address policyHolder, uint256 premiumAmount, uint256 sumInsuredAmount);
    event LogArcApplicationDeclined(bytes32 processId);

    event LogArcPolicyCreated(bytes32 policyId, bytes32 beneficiaryId, bytes32 riskId, uint256 premiumAmount);
    event LogArcPolicyProcessed(bytes32 policyId, uint256 claimId, uint256 payoutAmount);
    event LogArcPolicyClosed(bytes32 policyId);
    
    event LogArcClaimCreated(bytes32 policyId, uint256 claimId, uint256 payoutAmount);
    event LogArcPayoutCreated(bytes32 policyId, uint256 payoutAmount);

    constructor(
        bytes32 productName,
        address token,
        uint256 riskpoolId,
        address registry,
        address model
    )
        Product(productName, token, POLICY_FLOW, riskpoolId, registry)
    {
        _token = IERC20Metadata(token);
        _model = ArcModel(model);
    }


    function transferModel(
        address newOwner
    )
        external
        onlyOwner()
    {
        _model.transferOwnership(newOwner);
    }

    function setLocation(
        bytes16 locationId,
        bool isValid
    )
        external
        onlyOwner()
    {
        _model.setLocation(locationId, isValid);
    }

    function createRisk(
        bytes16 configId,
        bytes16 locationId,
        string memory crop,
        uint256 indexReferenceValue,
        uint256 indexSeasonValue,
        bool riskIsFinal
    )
        external
        onlyOwner()
        returns (bytes16 riskId)
    {
        // check if we have to add location
        if(!_model.isValidLocation(locationId)) {
            _model.setLocation(locationId, true);
        }

        riskId = _model.toRiskId(configId, locationId, crop);
        if (_model.getRisk(riskId).createdAt == 0) {
            _model.createRisk(
                configId, 
                locationId, 
                crop,
                indexReferenceValue,
                indexSeasonValue,
                riskIsFinal);
        }
    }


    function createPolicy(
        bytes16 beneficiaryId,
        address wallet,
        uint8 sex,
        bytes16 riskId,
        uint256 premiumAmount,
        uint256 sumInsuredAmount,
        uint32 subscriptionDate,
        bool underwriteApplication
    )
        external 
        onlyOwner()
        returns(
            bytes32 processId
        )
    {
        // deal with beneficiary
        if (_model.getBeneficiary(beneficiaryId).wallet == address(0)) {
            _model.createBeneficiary(beneficiaryId, wallet, sex);
        }
        ArcModel.Beneficiary memory beneficiary = _model.getBeneficiary(beneficiaryId);

        // get risk
        ArcModel.Risk memory risk = _model.getRisk(riskId);
        require(risk.valid, "ERROR:ARC-020:RISK_INVALID");

        address policyHolder = beneficiary.wallet;
        bytes memory applicationData = encodeApplicationData(
            riskId,
            beneficiaryId,
            beneficiary.sex,
            risk.locationId,
            risk.crop,
            subscriptionDate);

        processId = _newApplication(
            policyHolder, 
            premiumAmount, 
            sumInsuredAmount,
            "",
            applicationData);

        _processIds.push(processId);

        emit LogArcApplicationCreated(
            processId, 
            beneficiaryId, 
            policyHolder, 
            premiumAmount, 
            sumInsuredAmount);

        if (underwriteApplication) {
            underwrite(processId);
        } else {
            decline(processId);
        }
    }


    function underwrite(bytes32 processId) 
        public 
        onlyOwner()
        returns(bool success)
    {
        // ensure the application for processId exists and has the correct state
        IPolicy.Application memory application = _getApplication(processId);
        require(application.state == IPolicy.ApplicationState.Applied, "ERROR:ARC-060:STATE_NOT_APPLIED");

        success = _underwrite(processId);

        if (success) {
            (bytes16 riskId, bytes16 beneficiaryId,,,,) = decodeApplicationData(application.data);
            EnumerableSet.add(_policies[riskId], processId);

            emit LogArcPolicyCreated(
                processId, 
                beneficiaryId, 
                riskId, 
                application.premiumAmount);
        }
    }


    function decline(bytes32 processId) 
        public 
        onlyOwner()
    {
        // ensure the application for processId exists and has the correct state
        IPolicy.Application memory application = _getApplication(processId);
        require(application.state == IPolicy.ApplicationState.Applied, "ERROR:ARC-070:STATE_NOT_APPLIED");

        _decline(processId);

        emit LogArcApplicationDeclined(processId);
    }


    function collectPremium(bytes32 processId) 
        external
        onlyOwner()
        returns(bool success, uint256 fee, uint256 netPremium)
    {
        // ensure the policy for processId exists and has the correct state
        IPolicy.Policy memory policy = _getPolicy(processId);
        require(policy.state == IPolicy.PolicyState.Active, "ERROR:ARC-080:STATE_NOT_ACTIVE");

        (success, fee, netPremium) = _collectPremium(processId);
    }

    function processPolicy(bytes32 policyId)
        external
        onlyOwner()
        returns (uint256 claimId)
    {
        IPolicy.Application memory application = _getApplication(policyId);
        require(application.createdAt > 0, "ERROR:ARC-100:PROCESS_ID_INVALID");

        (bytes16 riskId,,,,,) = decodeApplicationData(application.data);
        ArcModel.Risk memory risk = _model.getRisk(riskId);
        require(risk.valid, "ERROR:ARC-101:RISK_ID_INVALID");

        IPolicy.Policy memory policy = _getPolicy(policyId);
        require(policy.createdAt > 0, "ERROR:ARC-102:POLICY_UNAVAILABLE");

        // check if claim needs to be created (will create a claim even if there is not payout)
        if(policy.claimsCount == 0) {
            bytes memory claimData = "";
            uint256 claimAmount = calculatePayoutAmount(
                risk.configId, 
                risk.indexReferenceValue, 
                risk.indexSeasonValue, 
                application.sumInsuredAmount);

            claimId = _newClaim(policyId, claimAmount, claimData);

            // once the end of season claim is created no new claims will be acceptable
            // we can expire the policy
            _expire(policyId);
        } else {
            // we will only have one claim (which will has claimId = 0)
            claimId = 0;
        }

        IPolicy.Claim memory claim = _getClaim(policyId, claimId);
        require(claim.createdAt > 0, "ERROR:ARC-103:CLAIM_UNAVAILABLE");

        // shortcut, nothing to do
        if(claim.state == IPolicy.ClaimState.Closed) {
            return claimId;
        }

        // confirm claim if risk status is final (decline if payout is 0)
        if(claim.state == IPolicy.ClaimState.Applied && risk.isFinal) {
            // (re)calculate payout amount based on final season index
            uint256 payoutAmount = calculatePayoutAmount(
                risk.configId, 
                risk.indexReferenceValue, 
                risk.indexSeasonValue, 
                application.sumInsuredAmount);

            if(payoutAmount > 0) {
                _confirmClaim(policyId, claimId, payoutAmount);

                bytes memory payoutData = "";
                uint256 payoutId = _newPayout(policyId, claimId, payoutAmount, payoutData);
                _processPayout(policyId, payoutId);
            } else {
                _declineClaim(policyId, claimId);
                _closeClaim(policyId, claimId);
            }

            // we have now eiter declined a claim (when no payout was to be made)
            // or the payout has been made -> we can now close the policy
            _close(policyId);

            emit LogArcPolicyProcessed(policyId, claimId, payoutAmount);
        }
    }


    function closePolicy(bytes32 processId) 
        external
        onlyOwner()
    {
        _expire(processId);
        _close(processId);

        emit LogArcPolicyClosed(processId);
    }


    function isProcessed(bytes32 policyId)
        external
        view
        returns (bool)
    {
        return _getClaim(policyId, 0).state == IPolicy.ClaimState.Closed;
    }


    function encodeApplicationData(
        bytes16 riskId,
        bytes16 beneficiaryId,
        uint8 sex,
        bytes16 locationId,
        string memory crop,
        uint32 subscriptionDate
    )
        public
        pure
        returns(bytes memory data)
    {
        return abi.encode(
            riskId,
            beneficiaryId,
            sex,
            locationId,
            crop,
            subscriptionDate);
    }


    function decodeApplicationData(
        bytes memory data
    )
        public
        pure
        returns(
            bytes16 riskId,
            bytes16 beneficiaryId,
            uint8 sex,
            bytes16 locationId,
            string memory crop,
            uint32 subscriptionDate
        )
    {
        (
            riskId,
            beneficiaryId,
            sex,
            locationId,
            crop,
            subscriptionDate
        ) = abi.decode(data, (bytes16, bytes16, uint8, bytes16, string, uint32));
    }

    function getModel() external view returns (ArcModel model) { return _model; }


    function calculatePayoutAmount(
        bytes16 configId,
        uint256 indexReferenceValue,
        uint256 indexSeasonValue,
        uint256 sumInsuredAmount
    )
        public
        view
        returns(uint256 payoutAmount)
    {
        ArcModel.Config memory config = _model.getConfig(configId);
        require(config.valid, "ERROR:ARC-200:CONFIG_INVALID");

        uint256 indexRatio = (10 ** _model.UFIXED_DECIMALS() * indexSeasonValue) / indexReferenceValue;
        uint256 payoutRatio = 0;

        // check index ratio against trigger levels
        if(indexRatio <= config.triggerSevereLevel) { payoutRatio = config.triggerSeverePayout; }
        else if(indexRatio <= config.triggerMediumLevel) { payoutRatio = config.triggerMediumPayout; }
        else if(indexRatio <= config.triggerWeakLevel) { payoutRatio = config.triggerWeakPayout; }

        // for index ratios > config.triggerWeakLevel
        if(payoutRatio == 0) {
            return 0;
        }

        return (payoutRatio * sumInsuredAmount) / 10 ** _model.UFIXED_DECIMALS();
    }

    function getTokenDecimals() external view returns(uint256) {
        return _token.decimals();
    }

    function processIds() external view returns(uint256 applicationCount) {
        return _processIds.length;
    }

    function getProcessId(uint256 index) external view returns(bytes32 processId) {
        return _processIds[index];
    }

    function policies(bytes32 riskId) external view returns(uint256 count) {
        return EnumerableSet.length(_policies[riskId]);
    }

    function getPolicyId(bytes32 riskId, uint256 policyIdx) external view returns(bytes32 processId) {
        return EnumerableSet.at(_policies[riskId], policyIdx);
    }
}