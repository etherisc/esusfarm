// SPDX-License-Identifier: MIT
pragma solidity 0.8.2;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

contract ArcModel is 
    Ownable
{
    uint8 public constant SEX_FEMALE = 10;
    uint8 public constant SEX_MALE = 20;
    uint256 public constant UFIXED_DECIMALS = 6;

    struct Beneficiary {
        address wallet;
        uint8 sex;
    }

    struct Risk {
        bool valid;
        bytes16 configId;
        bytes16 locationId;
        string crop;
        uint256 indexReferenceValue;
        uint256 indexSeasonValue;
        bool isFinal;
        uint32 createdAt;
        uint32 updatedAt;
    }

    struct Config {
        bool valid;
        string name; // example: MainSeason2023
        uint16 year; // example 2023
        uint8 startOfSeason; // decade, example: 13
        uint8 endOfSeason; // decade, example: 32
        string indexType; // example: WRSI
        string dataSource; // example: CHIRPS
        uint256 triggerSevereLevel; // UFixed, example: 700000 (70% or below refernce value)
        uint256 triggerSeverePayout; // UFixed, example: 1000000 (100% of sum insured)
        uint256 triggerMediumLevel; // UFixed, example: 800000 (80% or below reference value)
        uint256 triggerMediumPayout; // UFixed, example: 250000 (25% of sum insured)
        uint256 triggerWeakLevel; // UFixed, example: 900000 (90% or below reference value)
        uint256 triggerWeakPayout; // UFixed, example: 100000 (10% of sum insured)
        uint32 createdAt;
        uint32 updatedAt;
    }

    bytes16 [] private _beneficiaryIds;
    mapping(bytes16 /* beneficiaryId */ => Beneficiary) private _beneficiaries;

    bytes16 [] private _riskIds;
    mapping(bytes16 /* riskId */ => Risk) private _risks;

    bytes16 [] private _configIds;
    mapping(bytes16 /* configId */ =>  Config /* configId */ ) private _configs;

    mapping(bytes16 /* locationId */ => bool /* isValid */) private _locations;
    mapping(string /* crop */ => bool /* isValid */) private _crops;

    event LogArcBeneficiaryCreated(bytes16 beneficiaryId, address wallet, uint8 sex);
    event LogArcConfigCreated(bytes16 configId, string name, uint16 year);
    event LogArcRiskCreated(bytes16 riskId, bytes16 configId, bytes32 locationId, string crop);

    constructor()
        Ownable()
    {
        _setupValidCrops();
        _setupConfig2023();
    }

    function setConfig(bytes16 configId, bool isValid)
        external
        onlyOwner()
    {
        require(_configs[configId].createdAt > 0, "ERROR:ARM-010:CONFIG_UNKNOWN");
        _configs[configId].valid = isValid;
        _configs[configId].updatedAt = getTimestamp();
    }

    function setRisk(bytes16 riskId, bool isFinal, bool isValid)
        external
        onlyOwner()
    {
        require(_risks[riskId].createdAt > 0, "ERROR:ARM-015:RISK_UNKNOWN");
        _risks[riskId].isFinal = isFinal;
        _risks[riskId].valid = isValid;
        _risks[riskId].updatedAt = getTimestamp();
    }

    function setLocation(bytes16 locationId, bool isValid) external onlyOwner() { _locations[locationId] = isValid; }
    function setCrop(string memory crop, bool isValid) external onlyOwner() { _crops[crop] = isValid; }


    function createBeneficiary(
        bytes16 beneficiaryId,
        address wallet,
        uint8 sex
    )
        external onlyOwner()
    {
        require(_beneficiaries[beneficiaryId].wallet == address(0), "ERROR:ARM-025:BENEFICIARY_ALREADY_EXISTS");
        _beneficiaries[beneficiaryId] = Beneficiary(
            wallet,
            sex
        );

        _beneficiaryIds.push(beneficiaryId);
        emit LogArcBeneficiaryCreated(beneficiaryId, wallet, sex);
    }


    function createRisk(
        bytes16 configId,
        bytes16 locationId,
        string memory crop,
        uint256 indexReferenceValue,
        uint256 indexSeasonValue,
        bool isFinal
    )
        external onlyOwner()
        returns(bytes16 riskId)
    {
        riskId = toRiskId(configId, locationId, crop);
        uint32 timestamp = getTimestamp();

        require(_risks[riskId].createdAt == 0, "ERROR:ARM-025:RISK_ALREADY_EXISTS");
        _risks[riskId] = Risk(
            true, // valid
            configId,
            locationId,
            crop,
            indexReferenceValue,
            indexSeasonValue,
            isFinal,
            timestamp, // createdAt
            timestamp); // updatedAt

        _riskIds.push(riskId);
        emit LogArcRiskCreated(riskId, configId, locationId, crop);
    }


    function createConfig(
        string memory name,
        uint16 year,
        uint8 startOfSeason,
        uint8 endOfSeason,
        string memory indexType,
        string memory dataSource,
        uint256 triggerSevereLevel,
        uint256 triggerSeverePayout,
        uint256 triggerMediumLevel,
        uint256 triggerMediumPayout,
        uint256 triggerWeakLevel,
        uint256 triggerWeakPayout
    )
        external onlyOwner()
        returns(bytes16 configId)
    {
        return _createConfig(
            name,
            year,
            startOfSeason,
            endOfSeason,
            indexType,
            dataSource,
            triggerSevereLevel,
            triggerSeverePayout,
            triggerMediumLevel,
            triggerMediumPayout,
            triggerWeakLevel,
            triggerWeakPayout);
    }

    function isValidRisk(bytes16 riskId) public view returns(bool isValid) { return _risks[riskId].valid; }
    function isValidConfig(bytes16 configId) public view returns(bool isValid) { return _configs[configId].valid; }
    function isValidLocation(bytes16 locationId) public view returns(bool isValid) { return _locations[locationId]; }
    function isValidCrop(string memory crop) public view returns(bool isValid) { return _crops[crop]; }

    function beneficiaries() external view returns(uint256) { return _beneficiaryIds.length; }
    function getBeneficiaryId(uint256 idx) external view returns(bytes16 benficiaryId) { return _beneficiaryIds[idx]; }
    function getBeneficiary(bytes16 benficiaryId) external view returns(Beneficiary memory beneficiary) { return _beneficiaries[benficiaryId]; }

    function risks() external view returns(uint256) { return _riskIds.length; }
    function getRiskId(uint256 idx) external view returns(bytes16 riskId) { return _riskIds[idx]; }
    function getRisk(bytes16 riskId) external view returns(Risk memory risk) { return _risks[riskId]; }

    function configs() external view returns(uint256) { return _configIds.length; }
    function getConfigId(uint256 idx) external view returns(bytes16 configId) { return _configIds[idx]; }
    function getConfig(bytes16 configId) external view returns(Config memory config) { return _configs[configId]; }


    function toBeneficiaryId(
        string memory id,
        string memory phone,
        string memory salt
    )
        external
        pure
        returns(bytes16 beneficiaryId)
    {
        return bytes16(keccak256(abi.encodePacked(id, phone, salt)));
    }

    function toRiskId(
        bytes16 configId,
        bytes16 locationId,
        string memory crop
    )
        public
        view
        returns(bytes16 riskId)
    {
        require(isValidConfig(configId), "ERROR:ARM-110:CONFIG_INVALID");
        require(isValidLocation(locationId), "ERROR:ARM-111:LOCATION_INVALID");
        require(isValidCrop(crop), "ERROR:ARM-112:CROP_INVALID");
        return bytes16(keccak256(abi.encode(configId, locationId, crop)));
    }


    function toConfigId(
        string memory name,
        uint16 year
    )
        public
        view
        returns(bytes16 locationId)
    {
        require(year == 2023, "ERROR:ARM-110:YEAR_INVALID");
        return bytes16(keccak256(abi.encode(name, year)));
    }

    function toLocationId(
        string memory region,
        string memory province,
        string memory department,
        string memory village,
        string memory salt
    )
        public
        view
        returns(bytes16 locationId)
    {
        return bytes16(keccak256(abi.encode(region, province, department, village, salt)));
    }


    function getTimestamp() public view returns (uint32 timestamp) {
        return uint32(block.timestamp);
    }


    function decimals() public pure returns (uint256) {
        return UFIXED_DECIMALS;
    }

    function _setupValidCrops() 
        internal
    {
        _crops["Fusion"] = true;
        _crops["Maize"] = true;
        _crops["Millet"] = true;
        _crops["Sorghum"] = true;
    }

    function _setupConfig2023() 
        internal
    {
        _createConfig(
            "MainSeasons2023",
               2023,
                 13,
                 32,
            "WRSI",
            "CHIRPS",
             700000,
            1000000,
             800000,
             250000,
             900000,
             100000);
    }

    function _createConfig(
        string memory name,
        uint16 year,
        uint8 startOfSeason,
        uint8 endOfSeason,
        string memory indexType,
        string memory dataSource,
        uint256 triggerSevereLevel,
        uint256 triggerSeverePayout,
        uint256 triggerMediumLevel,
        uint256 triggerMediumPayout,
        uint256 triggerWeakLevel,
        uint256 triggerWeakPayout
    )
        internal
        returns(bytes16 configId)
    {
        configId = toConfigId(name, year);
        uint32 timestamp = getTimestamp();

        require(_configs[configId].createdAt == 0, "ERROR:ARM-020:CONFIG_ALREADY_EXISTS");
        _configs[configId] = Config(
            true, // valid
            name,
            year,
            startOfSeason,
            endOfSeason,
            indexType,
            dataSource,
            triggerSevereLevel,
            triggerSeverePayout,
            triggerMediumLevel,
            triggerMediumPayout,
            triggerWeakLevel,
            triggerWeakPayout,
            timestamp, // createdAt
            timestamp); // updatedAt

        _configIds.push(configId);
        emit LogArcConfigCreated(configId, name, year);
    }
}