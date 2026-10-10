// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title RepoMindRegistry
 * @notice Stores integrity records for RepoMind-AI repository analyses.
 *
 * The blockchain stores:
 * - analysis ID
 * - repository hash
 * - complete sanitized summary report
 * - report hash
 * - submitting user
 * - timestamp
 *
 * Sensitive information such as passwords, JWTs, GitHub tokens,
 * private source code, and detailed reports must NOT be stored here.
 */
contract RepoMindRegistry {
    struct AnalysisRecord {
        uint256 analysisId;
        bytes32 repositoryHash;
        bytes32 reportHash;
        string summaryReport;
        address submittedBy;
        uint256 timestamp;
    }

    mapping(uint256 => AnalysisRecord) private records;

    event AnalysisRegistered(
        uint256 indexed analysisId,
        bytes32 indexed repositoryHash,
        bytes32 indexed reportHash,
        address submittedBy,
        uint256 timestamp
    );

    /**
     * @notice Register a repository analysis summary.
     */
    function registerAnalysis(
        uint256 analysisId,
        bytes32 repositoryHash,
        bytes32 reportHash,
        string calldata summaryReport
    ) external {
        require(
            records[analysisId].timestamp == 0,
            "Analysis already registered"
        );

        records[analysisId] = AnalysisRecord({
            analysisId: analysisId,
            repositoryHash: repositoryHash,
            reportHash: reportHash,
            summaryReport: summaryReport,
            submittedBy: msg.sender,
            timestamp: block.timestamp
        });

        emit AnalysisRegistered(
            analysisId,
            repositoryHash,
            reportHash,
            msg.sender,
            block.timestamp
        );
    }

    /**
     * @notice Retrieve a stored analysis record.
     */
    function getAnalysis(
        uint256 analysisId
    )
        external
        view
        returns (
            uint256,
            bytes32,
            bytes32,
            string memory,
            address,
            uint256
        )
    {
        require(
            records[analysisId].timestamp != 0,
            "Analysis not found"
        );

        AnalysisRecord memory record = records[analysisId];

        return (
            record.analysisId,
            record.repositoryHash,
            record.reportHash,
            record.summaryReport,
            record.submittedBy,
            record.timestamp
        );
    }

    /**
     * @notice Verify whether a supplied report matches
     * the report hash stored on-chain.
     */
    function verifyReport(
        uint256 analysisId,
        bytes32 reportHash
    ) external view returns (bool) {
        require(
            records[analysisId].timestamp != 0,
            "Analysis not found"
        );

        return records[analysisId].reportHash == reportHash;
    }

    /**
     * @notice Check whether an analysis has already been registered.
     */
    function exists(
        uint256 analysisId
    ) external view returns (bool) {
        return records[analysisId].timestamp != 0;
    }
}
